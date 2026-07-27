from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
from pathlib import Path
import sys

from PySide6.QtCore import QFileInfo, QIODevice, QObject, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QFont, QFontDatabase, QGuiApplication, QIcon, QImage, QPixmap, QWindow
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider, QQuickWindow, QSGRendererInterface
from PySide6.QtWidgets import QApplication, QFileIconProvider, QMenu, QSystemTrayIcon

from desktop_backend import DesktopBackend


INSTANCE_NAME = "JARVIS.Desktop.Instance"


def ensure_windows_autostart(value_name: str) -> bool:
    """Register the frozen desktop build for background startup at user logon."""
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return False
    try:
        import winreg

        command = f'"{Path(sys.executable).resolve()}"'
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
        ) as key:
            winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, command)
        return True
    except OSError:
        return False


class ProgramIconProvider(QQuickImageProvider):
    """Expose native Windows program icons to QML without writing cache files."""

    def __init__(self, backend: DesktopBackend) -> None:
        super().__init__(QQuickImageProvider.ImageType.Pixmap)
        self.backend = backend
        self.file_icons = QFileIconProvider()

    def requestPixmap(
        self,
        identifier: str,
        size: QSize,
        requested_size: QSize,
    ) -> QPixmap:
        target = self.backend.program_icon_target(identifier)
        if target is None:
            return QPixmap()

        dimensions = requested_size if requested_size.isValid() else QSize(32, 32)
        pixmap = self._windows_pixmap(target, dimensions)
        if pixmap.isNull():
            pixmap = self.file_icons.icon(QFileInfo(target)).pixmap(dimensions)
        if not pixmap.isNull():
            size.setWidth(pixmap.width())
            size.setHeight(pixmap.height())
        return pixmap

    @staticmethod
    def _windows_pixmap(target: str, dimensions: QSize) -> QPixmap:
        if os.name != "nt":
            return QPixmap()

        class SHFILEINFO(ctypes.Structure):
            _fields_ = [
                ("hIcon", wintypes.HICON),
                ("iIcon", ctypes.c_int),
                ("dwAttributes", wintypes.DWORD),
                ("szDisplayName", wintypes.WCHAR * 260),
                ("szTypeName", wintypes.WCHAR * 80),
            ]

        info = SHFILEINFO()
        flags = 0x000000100 | 0x000000000  # SHGFI_ICON | SHGFI_LARGEICON
        result = ctypes.windll.shell32.SHGetFileInfoW(
            target,
            0,
            ctypes.byref(info),
            ctypes.sizeof(info),
            flags,
        )
        if not result or not info.hIcon:
            return QPixmap()
        try:
            image = QImage.fromHICON(info.hIcon)
            return QPixmap.fromImage(image).scaled(
                dimensions,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        finally:
            ctypes.windll.user32.DestroyIcon(info.hIcon)


def resource_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


class SingleInstance(QObject):
    activationRequested = Signal()

    def __init__(self, name: str = INSTANCE_NAME) -> None:
        super().__init__()
        self.name = name
        self.server: QLocalServer | None = None

    def start(self) -> bool:
        socket = QLocalSocket(self)
        socket.connectToServer(self.name, QIODevice.WriteOnly)
        if socket.waitForConnected(250):
            socket.write(b"show")
            socket.flush()
            socket.waitForBytesWritten(250)
            socket.disconnectFromServer()
            return False

        QLocalServer.removeServer(self.name)
        self.server = QLocalServer(self)
        if not self.server.listen(self.name):
            return False
        self.server.newConnection.connect(self._read_activation)
        return True

    def _read_activation(self) -> None:
        if self.server is None:
            return
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.waitForReadyRead(100)
            socket.readAll()
            socket.disconnectFromServer()
        self.activationRequested.emit()


def create_tray(
    backend: DesktopBackend,
    resources: Path,
    *,
    display_name: str = "JARVIS · Desktop command center",
    open_action_text: str = "Открыть JARVIS",
    include_pet: bool = True,
) -> QSystemTrayIcon:
    icon_path = resources / "assets" / "pet" / "idle.png"
    tray = QSystemTrayIcon(QIcon(str(icon_path)))
    tray.setToolTip(display_name)

    menu = QMenu()
    open_action = QAction(open_action_text, menu)
    pet_action = QAction("Скрыть питомца", menu)
    exit_action = QAction("Выйти", menu)
    open_action.triggered.connect(backend.showMainWindow)
    pet_action.triggered.connect(backend.togglePet)
    exit_action.triggered.connect(backend.quitApplication)
    menu.addAction(open_action)
    if include_pet:
        menu.addAction(pet_action)
    menu.addSeparator()
    menu.addAction(exit_action)
    tray.setContextMenu(menu)

    def update_pet_action() -> None:
        pet_action.setText("Скрыть питомца" if backend.petVisible else "Показать питомца")

    backend.petVisibleChanged.connect(update_pet_action)

    def activate(reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in {
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        }:
            backend.showMainWindow()

    tray.activated.connect(activate)
    tray.show()
    return tray


def run_desktop_app(
    *,
    main_qml: str = "Main.qml",
    main_window_title: str = "JARVIS Desktop",
    instance_name: str = INSTANCE_NAME,
    display_name: str = "JARVIS · Desktop command center",
    open_action_text: str = "Открыть JARVIS",
    load_pet: bool = True,
    autostart_name: str | None = None,
) -> int:
    resources = resource_directory()
    installation_directory = (
        Path(sys.executable).resolve().parent
        if getattr(sys, "frozen", False)
        else resources
    )
    os.environ.setdefault("JARVIS_DATA_DIR", str(installation_directory / "data"))
    os.environ.setdefault(
        "QML_DISK_CACHE_PATH", str(installation_directory / ".cache" / "qml")
    )
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    os.environ.setdefault("QSG_RENDER_LOOP", "basic")
    if os.name == "nt":
        QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Direct3D11)

    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    available_families = set(QFontDatabase.families())
    ui_font_family = (
        "Segoe UI Variable"
        if "Segoe UI Variable" in available_families
        else "Segoe UI"
    )
    app.setFont(QFont(ui_font_family))
    app.setApplicationName("JARVIS")
    app.setApplicationDisplayName("JARVIS Desktop")
    app.setOrganizationName("JARVIS")
    app.setQuitOnLastWindowClosed(False)

    single_instance = SingleInstance(instance_name)
    if not single_instance.start():
        return 0
    if autostart_name:
        ensure_windows_autostart(autostart_name)

    backend = DesktopBackend(resources)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.addImageProvider("programicons", ProgramIconProvider(backend))
    engine.load(QUrl.fromLocalFile(str(resources / "qml" / main_qml)))
    if load_pet:
        engine.load(QUrl.fromLocalFile(str(resources / "qml" / "Pet.qml")))

    root_windows = {
        window.title(): window
        for window in engine.rootObjects()
        if isinstance(window, QQuickWindow)
    }
    main_window = root_windows.get(main_window_title)
    pet_window = root_windows.get("JARVIS Pet") if load_pet else None
    if main_window is None or (load_pet and pet_window is None):
        return 2

    backend.set_main_window(main_window)
    backend.startVoiceControl()

    def keep_pet_visible(visibility: QWindow.Visibility) -> None:
        if pet_window is not None and visibility == QWindow.Visibility.Minimized and backend.petVisible:
            QTimer.singleShot(0, pet_window.show)
            QTimer.singleShot(0, pet_window.raise_)

    main_window.visibilityChanged.connect(keep_pet_visible)
    single_instance.activationRequested.connect(backend.showMainWindow)
    tray = create_tray(
        backend,
        resources,
        display_name=display_name,
        open_action_text=open_action_text,
        include_pet=load_pet,
    )

    exit_code = app.exec()
    backend.shutdown_workers()
    tray.hide()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(run_desktop_app())
