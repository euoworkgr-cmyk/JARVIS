from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import assistant


class AssistantSpecialCommandTests(unittest.TestCase):
    def test_shutdown_delay_is_converted_from_minutes_to_seconds(self) -> None:
        self.assertEqual(
            assistant.extract_power_command("Выключить пк(30)"),
            assistant.PowerCommand("shutdown", 1800),
        )
        self.assertEqual(
            assistant.extract_power_command("выключить пк"),
            assistant.PowerCommand("shutdown", 0),
        )

    def test_restart_sleep_and_abort_power_commands(self) -> None:
        self.assertEqual(
            assistant.extract_power_command("перезагрузка"),
            assistant.PowerCommand("restart"),
        )
        self.assertEqual(
            assistant.extract_power_command("спящий режим"),
            assistant.PowerCommand("sleep"),
        )
        self.assertEqual(
            assistant.extract_power_command("отменить выключение"),
            assistant.PowerCommand("abort"),
        )

    def test_invalid_shutdown_delay_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            assistant.extract_power_command("выключить пк(полчаса)")

    @patch("assistant.subprocess.Popen")
    def test_shutdown_uses_windows_seconds_argument(self, popen_mock) -> None:
        result = assistant.execute_power_command(
            assistant.PowerCommand("shutdown", 1800)
        )

        self.assertEqual(result.kind, "success")
        popen_mock.assert_called_once_with(
            ["shutdown.exe", "-s", "-t", "1800"],
            creationflags=assistant.subprocess.CREATE_NO_WINDOW,
        )

    def test_notes_command_is_registered(self) -> None:
        self.assertIn("заметки", assistant.NOTES_COMMANDS)

    def test_notes_are_saved_and_loaded_as_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.json"
            notes = ["Купить молоко", "Запустить Протокол игры"]

            assistant.save_notes(notes, path)

            self.assertEqual(assistant.load_notes(path), notes)

    def test_kill_command_is_extracted_before_program_search(self) -> None:
        self.assertEqual(assistant.extract_kill_target("kill chrome"), "chrome")
        self.assertEqual(assistant.extract_kill_target("KILL   Telegram"), "Telegram")
        self.assertEqual(assistant.extract_kill_target("Закрой Яндекс"), "Яндекс")
        self.assertEqual(assistant.extract_kill_target("заверши   Telegram"), "Telegram")
        self.assertEqual(assistant.extract_kill_target("close VS Code"), "VS Code")
        self.assertEqual(assistant.extract_kill_target("kill"), "")
        self.assertIsNone(assistant.extract_kill_target("chrome"))

    def test_kill_aliases_map_to_real_process_names(self) -> None:
        self.assertEqual(assistant.normalize_kill_target("яндекс"), "browser")
        self.assertEqual(assistant.normalize_kill_target("яндекс музыку"), "яндекс музыка")
        self.assertEqual(assistant.normalize_kill_target("vs code"), "code")

    def test_preset_list_command_is_registered(self) -> None:
        self.assertIn("пресеты", assistant.PRESET_LIST_COMMANDS)

    def test_exact_cyrillic_program_name_bypasses_ascii_fuzzy_search(self) -> None:
        program_map = {
            "камера": "Microsoft.WindowsCamera_8wekyb3d8bbwe!App",
        }

        self.assertEqual(
            assistant.find_program("камера", program_map),
            ("камера", 100),
        )

    @patch("assistant.current_jarvis_executable")
    def test_stale_jarvis_index_uses_current_executable(self, executable_mock) -> None:
        executable_mock.return_value = Path(r"A:\JARVIS\dist\assistant.exe")

        program_map = assistant.with_current_jarvis_target(
            {"jarvis": r"D:\Jarvis\Jarvis.exe", "chrome": "Chrome"}
        )

        self.assertEqual(program_map["jarvis"], r"A:\JARVIS\dist\assistant.exe")
        self.assertEqual(program_map["supersonic"], r"A:\JARVIS\dist\assistant.exe")
        self.assertEqual(program_map["chrome"], "Chrome")

    def test_vpn_command_uses_configured_executable(self) -> None:
        with (
            patch("assistant.Path.is_file", return_value=True),
            patch("assistant.launch_console_target") as launch_mock,
        ):
            result = assistant.open_special_command("VPN")

        self.assertEqual(result.kind, "success")
        launch_mock.assert_called_once_with(assistant.VPN_EXECUTABLE)

    def test_claude_code_command_uses_configured_launcher(self) -> None:
        with (
            patch("assistant.Path.is_file", return_value=True),
            patch("assistant.launch_target") as launch_mock,
        ):
            result = assistant.open_special_command("Claude code")

        self.assertEqual(result.kind, "success")
        launch_mock.assert_called_once_with(str(assistant.CLAUDE_CODE_LAUNCHER))

    def test_claude_code_launcher_falls_back_to_existing_batch_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            desktop = Path(directory)
            batch_file = desktop / "Claude code.bat"
            batch_file.touch()

            launcher = assistant.resolve_claude_code_launcher(desktop)

        self.assertEqual(launcher, batch_file)

    @patch("assistant.os.startfile")
    @patch("assistant.os.path.exists", return_value=True)
    def test_shortcut_is_opened_via_windows_shell(
        self,
        _exists_mock,
        startfile_mock,
    ) -> None:
        shortcut = r"C:\Users\Евгений\Desktop\Claude code.lnk"

        assistant.launch_target(shortcut)

        startfile_mock.assert_called_once_with(shortcut)

    @patch("assistant.os.startfile")
    @patch("assistant.os.path.exists", return_value=True)
    def test_batch_launcher_is_opened_via_windows_shell(
        self,
        _exists_mock,
        startfile_mock,
    ) -> None:
        batch_file = r"C:\Users\Евгений\Desktop\Claude code.bat"

        assistant.launch_target(batch_file)

        startfile_mock.assert_called_once_with(batch_file)

    @patch("assistant.subprocess.Popen")
    def test_vpn_console_does_not_inherit_jarvis_input(self, popen_mock) -> None:
        assistant.launch_console_target(assistant.VPN_EXECUTABLE)

        popen_mock.assert_called_once_with(
            [str(assistant.VPN_EXECUTABLE)],
            cwd=str(assistant.VPN_EXECUTABLE.parent),
            creationflags=assistant.subprocess.CREATE_NEW_CONSOLE,
            close_fds=True,
        )

    @patch("assistant.subprocess.Popen")
    @patch("assistant.Path.is_file", return_value=True)
    def test_preset_one_opens_new_yandex_window(
        self,
        _is_file_mock,
        popen_mock,
    ) -> None:
        result = assistant.open_preset("1", {})

        self.assertEqual(result.kind, "success")
        popen_mock.assert_called_once_with(
            [str(assistant.YANDEX_BROWSER_EXECUTABLE), "--new-window"],
            cwd=str(assistant.YANDEX_BROWSER_EXECUTABLE.parent),
        )

    @patch("assistant.open_program")
    def test_program_presets_use_expected_index_names(self, open_mock) -> None:
        open_mock.return_value = assistant.LaunchResult("success", "ok")
        expected = {
            "2": "chatgpt",
            "3": "visual studio code",
            "4": "telegram",
            "5": "камера",
        }

        for number, program_name in expected.items():
            with self.subTest(number=number):
                assistant.open_preset(number, {})
                open_mock.assert_called_with(program_name, {})

    @patch("assistant.launch_target")
    def test_camera_preset_launches_registered_camera_app(self, launch_mock) -> None:
        camera_app_id = "Microsoft.WindowsCamera_8wekyb3d8bbwe!App"

        result = assistant.open_preset("5", {"камера": camera_app_id})

        self.assertEqual(result.kind, "success")
        launch_mock.assert_called_once_with(camera_app_id)

    @patch("get_programs.get_installed_programs")
    @patch("assistant.program_index_path")
    def test_program_index_can_be_refreshed_in_desktop_build(
        self,
        index_path_mock,
        installed_mock,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "JARVIS" / "programs.json"
            index_path_mock.return_value = path
            installed_mock.return_value = {"новая программа": "Example.App"}

            programs, error = assistant.generate_program_map()

            self.assertIsNone(error)
            self.assertEqual(programs, {"новая программа": "Example.App"})
            self.assertEqual(
                assistant.json.loads(path.read_text(encoding="utf-8")),
                programs,
            )


if __name__ == "__main__":
    unittest.main()
