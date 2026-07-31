from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import assistant
from command_service import CommandRequest, CommandService, HistoryStore, NotesStore, ProtocolStore
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

    def test_legacy_notes_fill_empty_desktop_store(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "dist" / "notes.json"
            target = root / "JARVIS" / "notes.json"
            legacy.parent.mkdir()
            target.parent.mkdir()
            legacy.write_text(json.dumps(["Заметка из терминала"], ensure_ascii=False), encoding="utf-8")
            target.write_text("[]", encoding="utf-8")

            notes = NotesStore(target, legacy_path=legacy)

            self.assertEqual(notes.items, ["Заметка из терминала"])
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), ["Заметка из терминала"])

    def test_notes_can_be_added_updated_and_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            notes = NotesStore(Path(directory) / "notes.json", legacy_path=Path(directory) / "missing.json")

            notes.add("Купить молоко")
            notes.update(0, "Купить чай")
            notes.remove(0)

            self.assertEqual(notes.items, [])

    def test_failed_writes_leave_notes_unchanged(self) -> None:
        operations = (
            lambda store: store.add("Новая"),
            lambda store: store.update(0, "Изменённая"),
            lambda store: store.remove(0),
            lambda store: store.clear(),
        )
        with tempfile.TemporaryDirectory() as directory:
            for number, operation in enumerate(operations):
                with self.subTest(operation=number):
                    store = NotesStore(
                        Path(directory) / f"notes-{number}.json",
                        legacy_path=Path(directory) / "missing.json",
                    )
                    store.items = ["Первая", "Вторая"]
                    with (
                        patch("command_service.Path.write_text", side_effect=OSError("disk full")),
                        self.assertRaises(OSError),
                    ):
                        operation(store)
                    self.assertEqual(store.items, ["Первая", "Вторая"])


class CommandServiceTests(unittest.TestCase):
    def make_service(self, path: Path) -> CommandService:
        return CommandService(program_map={"chrome": "Chrome"}, history=HistoryStore(path))

    def test_custom_protocol_is_saved_and_runs_actions_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocols = ProtocolStore(root / "protocols.json")
            protocols.save_protocol(
                "Протокол рабочий режим",
                [
                    {"type": "launch", "target": "chrome"},
                    {"type": "volume_up", "target": ""},
                ],
            )
            service = CommandService(
                program_map={"chrome": "Chrome"},
                history=HistoryStore(root / "history.json"),
                protocols=protocols,
            )
            with (
                patch("command_service.assistant.open_program", return_value=assistant.LaunchResult("success", "ok")) as open_mock,
                patch("command_service._send_windows_key") as key_mock,
            ):
                outcome = service.execute("протокол рабочий режим")

        self.assertEqual(outcome.status, "success")
        open_mock.assert_called_once_with("chrome", {"chrome": "Chrome"})
        key_mock.assert_called_once_with(0xAF)

    def test_unknown_protocol_returns_clear_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service = CommandService(
                program_map={},
                history=HistoryStore(root / "history.json"),
                protocols=ProtocolStore(root / "protocols.json"),
            )

            outcome = service.execute("протокол несуществующий")

        self.assertEqual(outcome.status, "not_found")
        self.assertIn("не найден", outcome.title)

    def test_power_protocol_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            protocols = ProtocolStore(root / "protocols.json")
            protocols.save_protocol("сон", [{"type": "sleep", "target": ""}])
            service = CommandService(
                program_map={},
                history=HistoryStore(root / "history.json"),
                protocols=protocols,
            )

            outcome = service.execute("протокол сон")

        self.assertEqual(outcome.status, "pending")
        self.assertEqual(outcome.data["kind"], "protocol")

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
        execute_mock.return_value = assistant.LaunchResult("success", "Выключаю компьютер")
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory) / "history.json")
            pending = service.execute("Выключи ПК")

            self.assertEqual(pending.status, "pending")
            self.assertEqual(pending.data["kind"], "power")
            execute_mock.assert_not_called()

            completed = service.confirm(pending.data["pending_id"])
            repeated = service.confirm(pending.data["pending_id"])

            self.assertEqual(completed.status, "success")
            self.assertEqual(repeated.status, "error")
            execute_mock.assert_called_once_with(
                assistant.PowerCommand("shutdown", 0)
            )

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
            activate_mock.assert_called_once_with(scan_mock.return_value, force=True)

    @patch("command_service.scan_named_processes")
    def test_russian_close_command_uses_kill_confirmation(self, scan_mock) -> None:
        candidate = ProcessCandidate(42, "browser.exe", 10.0, 0.0, "kill · совпадение 100%")
        scan_mock.return_value = GameModeScan([candidate], False)
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory) / "history.json")

            pending = service.execute("Закрой Яндекс")

        self.assertEqual(pending.status, "pending")
        scan_mock.assert_called_once_with("browser")

    @patch("command_service.activate_game_mode")
    @patch("command_service.scan_game_mode")
    def test_game_mode_keeps_graceful_shutdown(self, scan_mock, activate_mock) -> None:
        candidate = ProcessCandidate(42, "chrome.exe", 10.0, 8.0, "браузер · GPU 8.0%")
        scan_mock.return_value = GameModeScan([candidate], True)
        activate_mock.return_value = GameModeResult([candidate], [])
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory) / "history.json")

            pending = service.execute("/game")
            result = service.confirm(pending.data["pending_id"])

            self.assertEqual(result.status, "success")
            activate_mock.assert_called_once_with(scan_mock.return_value, force=False)

    @patch("command_service.scan_game_mode")
    def test_empty_game_scan_clears_previous_candidates(self, scan_mock) -> None:
        scan_mock.return_value = GameModeScan([], True, "")
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory) / "history.json")

            outcome = service.execute("/game")

        self.assertEqual(outcome.status, "success")
        self.assertEqual(outcome.data["candidates"], [])

    @patch("command_service.scan_named_processes")
    def test_empty_kill_scan_clears_previous_candidates(self, scan_mock) -> None:
        scan_mock.return_value = GameModeScan([], False, "")
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory) / "history.json")

            outcome = service.execute("kill chrome")

        self.assertEqual(outcome.status, "not_found")
        self.assertEqual(outcome.data["candidates"], [])

    @patch("command_service.assistant.open_program")
    def test_clear_history_requires_confirmation(self, open_mock) -> None:
        open_mock.return_value = assistant.LaunchResult("success", "Открываю chrome")
        with tempfile.TemporaryDirectory() as directory:
            service = self.make_service(Path(directory) / "history.json")
            service.execute("chrome")

            pending = service.execute("/clear")

            self.assertGreater(len(service.history_items), 0)
            service.confirm(pending.data["pending_id"])
            self.assertEqual(service.history_items, [])


if __name__ == "__main__":
    unittest.main()
