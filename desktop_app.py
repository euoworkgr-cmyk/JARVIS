from __future__ import annotations

import os
from pathlib import Path
import sys

from PySide6.QtCore import QIODevice, QObject, QUrl, Signal
from PySide6.QtGui import QAction, QIcon
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


def create_tray(backend: DesktopBackend, resources: Path) -> QSystemTrayIcon:
    icon_path = resources / "assets" / "pet" / "idle.png"
    tray = QSystemTrayIcon(QIcon(str(icon_path)))
    tray.setToolTip("JARVIS · Desktop command center")

    menu = QMenu()
    open_action = QAction("Открыть JARVIS", menu)
    pet_action = QAction("Скрыть питомца", menu)
    exit_action = QAction("Выйти", menu)
    open_action.triggered.connect(backend.showMainWindow)
    pet_action.triggered.connect(backend.togglePet)
    exit_action.triggered.connect(backend.quitApplication)
    menu.addAction(open_action)
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


def run_desktop_app() -> int:
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
    os.environ.setdefault("QSG_RENDER_LOOP", "basic")
    if os.name == "nt":
        QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Direct3D11)
    app = QApplication(sys.argv)
    app.setApplicationName("JARVIS")
    app.setApplicationDisplayName("JARVIS Desktop")
    app.setOrganizationName("JARVIS")
    app.setQuitOnLastWindowClosed(False)

    single_instance = SingleInstance()
    if not single_instance.start():
        return 0

    resources = resource_directory()
    backend = DesktopBackend(resources)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.load(QUrl.fromLocalFile(str(resources / "qml" / "Main.qml")))
    if not engine.rootObjects():
        return 2

    main_window = engine.rootObjects()[0]
    backend.set_main_window(main_window)
    single_instance.activationRequested.connect(backend.showMainWindow)
    tray = create_tray(backend, resources)

    exit_code = app.exec()
    tray.hide()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(run_desktop_app())
