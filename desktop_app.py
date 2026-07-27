from __future__ import annotations

import os
from pathlib import Path
import sys

from PySide6.QtCore import QIODevice, QObject, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QIcon, QWindow
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow, QSGRendererInterface
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from desktop_backend import DesktopBackend


INSTANCE_NAME = "JARVIS.Desktop.Instance"


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
    app = QApplication(sys.argv)
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
    tray.hide()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(run_desktop_app())
