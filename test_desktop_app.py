from __future__ import annotations

import os
from pathlib import Path
import unittest
import uuid

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from desktop_backend import DesktopBackend
from desktop_app import SingleInstance


class DesktopAppSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_main_qml_loads_without_errors(self) -> None:
        root = Path(__file__).resolve().parent
        engine = QQmlApplicationEngine()
        backend = DesktopBackend(root)
        engine.rootContext().setContextProperty("backend", backend)

        engine.load(QUrl.fromLocalFile(str(root / "qml" / "Main.qml")))

        self.assertEqual(len(engine.rootObjects()), 1)
        window = engine.rootObjects()[0]
        self.assertEqual(window.title(), "JARVIS Desktop")
        backend._quitting = True
        window.close()

    def test_second_instance_notifies_existing_server(self) -> None:
        name = f"JARVIS.Desktop.Test.{uuid.uuid4().hex}"
        first = SingleInstance(name)
        second = SingleInstance(name)
        try:
            self.assertTrue(first.start())
            self.assertFalse(second.start())
        finally:
            if first.server is not None:
                first.server.close()
                first.server.removeServer(name)


if __name__ == "__main__":
    unittest.main()
