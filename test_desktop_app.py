from __future__ import annotations

import os
from pathlib import Path
import unittest
from unittest.mock import patch
import uuid

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtGui import QWindow
from PySide6.QtQuick import QQuickWindow
from PySide6.QtWidgets import QApplication

from desktop_backend import DesktopBackend
from desktop_app import SingleInstance


class DesktopAppSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_desktop_windows_load_without_transient_relationship(self) -> None:
        root = Path(__file__).resolve().parent
        engine = QQmlApplicationEngine()
        backend = DesktopBackend(root)
        engine.rootContext().setContextProperty("backend", backend)

        engine.load(QUrl.fromLocalFile(str(root / "qml" / "Main.qml")))
        engine.load(QUrl.fromLocalFile(str(root / "qml" / "Pet.qml")))

        windows = {
            window.title(): window
            for window in engine.rootObjects()
            if isinstance(window, QQuickWindow)
        }
        self.assertEqual(set(windows), {"JARVIS Desktop", "JARVIS Pet"})
        main_window = windows["JARVIS Desktop"]
        pet_window = windows["JARVIS Pet"]
        self.assertEqual(main_window.color().alpha(), 255)
        self.assertIsNone(pet_window.transientParent())

        main_window.show()
        pet_window.show()
        self.app.processEvents()
        main_window.showMinimized()
        self.app.processEvents()

        self.assertTrue(pet_window.isVisible())
        self.assertNotEqual(pet_window.visibility(), QWindow.Visibility.Minimized)
        backend._quitting = True
        main_window.close()
        pet_window.close()

    def test_jarvis_core_has_no_per_frame_canvas_repaint(self) -> None:
        root = Path(__file__).resolve().parent
        source = (root / "qml" / "components" / "JarvisCore.qml").read_text(encoding="utf-8")

        self.assertNotIn("Canvas {", source)
        self.assertNotIn("requestPaint", source)
        self.assertIn("layer.enabled: true", source)
        self.assertIn("RotationAnimator", source)

    @patch("desktop_backend.QTimer.singleShot")
    @patch("desktop_backend.get_work_areas", return_value=[])
    @patch("desktop_backend.reduced_motion_enabled", return_value=True)
    def test_reduced_motion_still_restores_only_the_latest_state(
        self,
        _reduced_motion_mock,
        _work_areas_mock,
        single_shot_mock,
    ) -> None:
        backend = DesktopBackend(Path(__file__).resolve().parent)

        backend._set_state("success", restore=True)

        single_shot_mock.assert_called_once()
        restore_callback = single_shot_mock.call_args.args[1]
        backend._set_state("working")
        restore_callback()
        self.assertEqual(backend.jarvisState, "working")

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
