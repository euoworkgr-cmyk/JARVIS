from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtWidgets import QApplication

from command_service import CommandOutcome, CommandRequest, CommandService, HistoryStore
from desktop_backend import DesktopBackend, _format_bytes


class PersonalAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_personal_shell_loads_without_replacing_classic_main(self) -> None:
        root = Path(__file__).resolve().parent
        classic_source = (root / "qml" / "Main.qml").read_text(encoding="utf-8")
        personal_source = (root / "qml" / "personal" / "PersonalMain.qml").read_text(
            encoding="utf-8"
        )
        self.assertIn('title: "JARVIS Desktop"', classic_source)
        self.assertIn('title: "JARVIS Personal"', personal_source)
        self.assertIn("load_pet=True", (root / "personal_assistant.py").read_text(encoding="utf-8"))

        engine = QQmlApplicationEngine()
        backend = DesktopBackend(root)
        engine.rootContext().setContextProperty("backend", backend)
        engine.load(
            QUrl.fromLocalFile(str(root / "qml" / "personal" / "PersonalMain.qml"))
        )

        windows = [item for item in engine.rootObjects() if isinstance(item, QQuickWindow)]
        self.assertEqual([window.title() for window in windows], ["JARVIS Personal"])
        backend._quitting = True
        windows[0].close()

    def test_frequent_programs_exclude_quick_launch_presets(self) -> None:
        root = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as directory:
            history = HistoryStore(Path(directory) / "history.json")
            history.add(
                CommandRequest("открой obs studio"),
                CommandOutcome(
                    "success",
                    "Открываю obs studio",
                    data={"program": "obs studio", "program_title": "OBS Studio"},
                ),
            )
            history.add(
                CommandRequest("3"),
                CommandOutcome(
                    "success",
                    "Открываю visual studio code",
                    data={
                        "program": "visual studio code",
                        "program_title": "VS Code",
                    },
                ),
            )
            backend = DesktopBackend(root)
            backend.service = CommandService(
                program_map={"obs studio": "OBS", "visual studio code": "Code"},
                history=history,
            )

            items = backend.frequentPrograms

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["name"], "OBS Studio")
        self.assertEqual(items[0]["launchLabel"], "1 запуск")
        self.assertEqual(items[0]["iconId"], "obs%20studio")

    def test_program_icon_target_uses_indexed_executable(self) -> None:
        root = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "Demo.exe"
            executable.touch()
            backend = DesktopBackend(root)
            backend.service = CommandService(program_map={"demo": str(executable)})

            target = backend.program_icon_target("program/demo")

        self.assertEqual(target, str(executable))

    def test_quick_launch_uses_compact_titles_that_fit_cards(self) -> None:
        root = Path(__file__).resolve().parent
        backend = DesktopBackend(root)

        self.assertEqual(
            [item["title"] for item in backend.presetItems],
            ["Яндекс Браузер", "ChatGPT", "VS Code", "Telegram", "Камера"],
        )

    def test_history_uses_clean_program_display_title(self) -> None:
        root = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as directory:
            history = HistoryStore(Path(directory) / "history.json")
            history.add(
                CommandRequest("открой яндекс музыку"),
                CommandOutcome(
                    "success",
                    "Открываю яндекс музыка",
                    data={"program": "яндекс музыка", "program_title": "яндекс музыка"},
                ),
            )
            backend = DesktopBackend(root)
            backend.service = CommandService(program_map={}, history=history)

            item = backend.historyItems[0]

        self.assertEqual(item["displayTitle"], "Яндекс Музыка")

    def test_storage_values_use_compact_russian_units(self) -> None:
        self.assertEqual(_format_bytes(238 * 1024**3), "238 ГБ")
        self.assertEqual(_format_bytes(int(1.5 * 1024**4)), "1,5 ТБ")


if __name__ == "__main__":
    unittest.main()
