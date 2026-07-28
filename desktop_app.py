from __future__ import annotations

import ctypes
from ctypes import wintypes
from functools import lru_cache
import json
import os
from pathlib import Path
import subprocess
import sys

from PySide6.QtCore import QFileInfo, QIODevice, QObject, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QFont, QFontDatabase, QGuiApplication, QIcon, QImage, QPixmap, QWindow
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider, QQuickWindow, QSGRendererInterface
from PySide6.QtWidgets import QApplication, QFileIconProvider, QMenu, QSystemTrayIcon

from desktop_backend import DesktopBackend
from user_settings import configure_data_directory


INSTANCE_NAME = "Supersonic.Desktop.Instance"


def _parse_icon_location(value: str) -> tuple[str, int]:
    location = value.strip().strip('"')
    if not location:
        return "", 0
    path, separator, raw_index = location.rpartition(",")
    if separator:
        try:
            return path.strip().strip('"'), int(raw_index.strip())
        except ValueError:
            pass
    return location, 0


def resolve_windows_icon_source(target: str) -> tuple[str, int]:
    """Resolve a .lnk to its original icon source without the shortcut overlay."""
    path = Path(target)
    if os.name != "nt" or path.suffix.casefold() != ".lnk":
        return target, 0

    try:
        modified_ns = path.stat().st_mtime_ns
    except OSError:
        modified_ns = 0
    return _resolve_windows_icon_source_cached(target, modified_ns)


@lru_cache(maxsize=128)
def _resolve_windows_icon_source_cached(
    target: str, _modified_ns: int
) -> tuple[str, int]:
    path = Path(target)

    environment = os.environ.copy()
    environment["SUPERSONIC_SHORTCUT_PATH"] = str(path)
    script = (
        "[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false);"
        "$s=(New-Object -ComObject WScript.Shell).CreateShortcut("
        "$env:SUPERSONIC_SHORTCUT_PATH);"
        "@{TargetPath=$s.TargetPath;IconLocation=$s.IconLocation}"
        "|ConvertTo-Json -Compress"
    )
    try:
        completed = subprocess.run(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
            ],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8-sig",
            errors="replace",
            timeout=4,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            env=environment,
        )
        shortcut = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError, TypeError):
        return target, 0

    icon_path, icon_index = _parse_icon_location(
        str(shortcut.get("IconLocation", ""))
    )
    candidates = [
        (icon_path, icon_index),
        (str(shortcut.get("TargetPath", "")), 0),
    ]
    for candidate, index in candidates:
        expanded = Path(os.path.expandvars(candidate.strip().strip('"')))
        if candidate and expanded.is_file():
            return str(expanded), index
    return target, 0


class ProgramIconProvider(QQuickImageProvider):
    """Expose native Windows program icons to QML without writing cache files."""

    def __init__(self, backend: DesktopBackend) -> None:
        super().__init__(
            QQuickImageProvider.ImageType.Pixmap,
            QQuickImageProvider.Flag.ForceAsynchronousImageLoading,
        )
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
        icon_source, icon_index = resolve_windows_icon_source(target)
        pixmap = self._windows_pixmap(icon_source, dimensions, icon_index)
        if pixmap.isNull():
            pixmap = self.file_icons.icon(QFileInfo(icon_source)).pixmap(dimensions)
        if not pixmap.isNull():
            size.setWidth(pixmap.width())
            size.setHeight(pixmap.height())
        return pixmap

    @staticmethod
    def _windows_pixmap(
        target: str,
        dimensions: QSize,
        icon_index: int = 0,
    ) -> QPixmap:
        if os.name != "nt":
            return QPixmap()

        large_icon = wintypes.HICON()
        small_icon = wintypes.HICON()
        extracted = ctypes.windll.shell32.ExtractIconExW(
            target,
            icon_index,
            ctypes.byref(large_icon),
            ctypes.byref(small_icon),
            1,
        )
        if extracted:
            preferred = (
                large_icon
                if max(dimensions.width(), dimensions.height()) >= 32
                else small_icon
            )
            if not preferred:
                preferred = large_icon or small_icon
            try:
                if preferred:
                    image = QImage.fromHICON(preferred.value)
                    return QPixmap.fromImage(image).scaled(
                        dimensions,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
            finally:
                handles = {
                    handle.value
                    for handle in (large_icon, small_icon)
                    if handle and handle.value
                }
                for handle in handles:
                    ctypes.windll.user32.DestroyIcon(handle)

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

    def __init__(
        self, name: str = INSTANCE_NAME, legacy_names: tuple[str, ...] = ()
    ) -> None:
        super().__init__()
        self.name = name
        self.server: QLocalServer | None = None
        self.servers: list[QLocalServer] = []
        self.names = tuple(dict.fromkeys((name, *legacy_names)))

    def start(self) -> bool:
        for name in self.names:
            socket = QLocalSocket(self)
            socket.connectToServer(name, QIODevice.WriteOnly)
            if socket.waitForConnected(250):
                socket.write(b"show")
                socket.flush()
                socket.waitForBytesWritten(250)
                socket.disconnectFromServer()
                return False

        for name in self.names:
            QLocalServer.removeServer(name)
            server = QLocalServer(self)
            if not server.listen(name):
                self.close()
                return False
            server.newConnection.connect(lambda server=server: self._read_activation(server))
            self.servers.append(server)
        self.server = self.servers[0]
        return True

    def close(self) -> None:
        for name, server in zip(self.names, self.servers):
            server.close()
            QLocalServer.removeServer(name)
        self.servers.clear()
        self.server = None

    def _read_activation(self, server: QLocalServer) -> None:
        while server.hasPendingConnections():
            socket = server.nextPendingConnection()
            socket.waitForReadyRead(100)
            socket.readAll()
            socket.disconnectFromServer()
        self.activationRequested.emit()


def create_tray(
    backend: DesktopBackend,
    resources: Path,
    *,
    display_name: str = "Supersonic · Desktop command center",
    open_action_text: str = "Открыть Supersonic",
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
    main_window_title: str = "Supersonic Desktop",
    instance_name: str = INSTANCE_NAME,
    display_name: str = "Supersonic · Desktop command center",
    open_action_text: str = "Открыть Supersonic",
    load_pet: bool = True,
    autostart_name: str | None = None,
    legacy_autostart_names: tuple[str, ...] = (),
    legacy_instance_names: tuple[str, ...] = (),
) -> int:
    resources = resource_directory()
    installation_directory = (
        Path(sys.executable).resolve().parent
        if getattr(sys, "frozen", False)
        else resources
    )
    configure_data_directory(installation_directory)
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
    app.setApplicationName("Supersonic")
    app.setApplicationDisplayName("Supersonic Desktop")
    app.setOrganizationName("Supersonic")
    app.setQuitOnLastWindowClosed(False)

    single_instance = SingleInstance(instance_name, legacy_instance_names)
    if not single_instance.start():
        return 0
    backend = DesktopBackend(
        resources,
        autostart_name=autostart_name,
        legacy_autostart_names=legacy_autostart_names,
    )
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
    pet_window = root_windows.get("Supersonic Pet") if load_pet else None
    if main_window is None or (load_pet and pet_window is None):
        return 2

    backend.set_main_window(main_window)
    backend.startConfiguredVoiceControl()

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
