from __future__ import annotations

import os
from pathlib import Path
import sys

from PySide6.QtCore import QFileInfo, QIODevice, QObject, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QFont, QFontDatabase, QGuiApplication, QIcon, QPixmap, QWindow
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider, QQuickWindow, QSGRendererInterface
from PySide6.QtWidgets import QApplication, QFileIconProvider, QMenu, QSystemTrayIcon

from desktop_backend import DesktopBackend


INSTANCE_NAME = "JARVIS.Desktop.Instance"


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
        target = self.backend.preset_icon_target(identifier)
        if target is None:
            return QPixmap()

        icon = self.file_icons.icon(QFileInfo(target))
        dimensions = requested_size if requested_size.isValid() else QSize(32, 32)
        pixmap = icon.pixmap(dimensions)
        if not pixmap.isNull():
            size.setWidth(pixmap.width())
            size.setHeight(pixmap.height())
        return pixmap


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
) -> int:
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

    resources = resource_directory()
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
