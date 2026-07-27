from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import assistant
from command_service import CommandRequest, CommandService, HistoryStore, NotesStore
from game_mode import GameModeResult, GameModeScan, ProcessCandidate


class HistoryStoreTests(unittest.TestCase):
    def test_history_is_limited_and_survives_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            history = HistoryStore(path, limit=3)
            for number in range(5):
                history.add(
                    CommandRequest(f"command {number}"),
                    CommandService._launch_outcome(assistant.LaunchResult("success", "ok")),
                )

            restored = HistoryStore(path, limit=3)

            self.assertEqual([item["command"] for item in restored.items], ["command 2", "command 3", "command 4"])

    def test_corrupt_history_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "history.json"
            path.write_text("not json", encoding="utf-8")

            history = HistoryStore(path)

            self.assertEqual(history.items, [])
            self.assertFalse(path.exists())
            self.assertEqual(len(list(path.parent.glob("history.corrupt-*.json"))), 1)


class NotesStoreTests(unittest.TestCase):
    def test_legacy_notes_are_migrated(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "old-notes.json"
            target = root / "JARVIS" / "notes.json"
            legacy.write_text(json.dumps(["Первая заметка"], ensure_ascii=False), encoding="utf-8")

            notes = NotesStore(target, legacy_path=legacy)

            self.assertEqual(notes.items, ["Первая заметка"])
            self.assertTrue(target.exists())

    def test_notes_can_be_added_updated_and_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            notes = NotesStore(Path(directory) / "notes.json", legacy_path=Path(directory) / "missing.json")

            notes.add("Купить молоко")
            notes.update(0, "Купить чай")
            notes.remove(0)

            self.assertEqual(notes.items, [])


class CommandServiceTests(unittest.TestCase):
    def make_service(self, path: Path) -> CommandService:
        return CommandService(program_map={"chrome": "Chrome"}, history=HistoryStore(path))

    @patch("command_service.assistant.open_program")
    def test_regular_command_returns_structured_outcome(self, open_mock) -> None:
        open_mock.return_value = assistant.LaunchResult("success", "Открываю chrome", "Совпадение 100%")
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory) / "history.json")

            outcome = service.execute(CommandRequest("открой chrome"))

            self.assertEqual(outcome.status, "success")
            self.assertEqual(outcome.title, "Открываю chrome")
            self.assertEqual(service.history_items[-1]["command"], "открой chrome")

    @patch("command_service.assistant.execute_power_command")
    def test_power_command_requires_one_time_confirmation(self, execute_mock) -> None:
        execute_mock.return_value = assistant.LaunchResult("success", "Перезагружаю компьютер")
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory) / "history.json")
            pending = service.execute("перезагрузка")

            self.assertEqual(pending.status, "pending")
            execute_mock.assert_not_called()

            completed = service.confirm(pending.data["pending_id"])
            repeated = service.confirm(pending.data["pending_id"])

            self.assertEqual(completed.status, "success")
            self.assertEqual(repeated.status, "error")
            execute_mock.assert_called_once()

    @patch("command_service.activate_game_mode")
    @patch("command_service.scan_named_processes")
    def test_kill_shows_exact_candidate_before_execution(self, scan_mock, activate_mock) -> None:
        candidate = ProcessCandidate(42, "chrome.exe", 10.0, 0.0, "kill · совпадение 100%")
        scan_mock.return_value = GameModeScan([candidate], False)
        activate_mock.return_value = GameModeResult([candidate], [])
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory) / "history.json")

            pending = service.execute("kill chrome")

            self.assertEqual(pending.status, "pending")
            self.assertEqual(pending.data["candidates"][0]["pid"], 42)
            activate_mock.assert_not_called()

            result = service.confirm(pending.data["pending_id"])

            self.assertEqual(result.status, "success")
            activate_mock.assert_called_once()

    def test_clear_history_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory) / "history.json")
            service.execute("chrome")

            pending = service.execute("/clear")

            self.assertGreater(len(service.history_items), 0)
            service.confirm(pending.data["pending_id"])
            self.assertEqual(service.history_items, [])


if __name__ == "__main__":
    unittest.main()
