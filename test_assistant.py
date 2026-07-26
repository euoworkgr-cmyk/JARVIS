from __future__ import annotations

import unittest
from unittest.mock import patch

import assistant


class AssistantSpecialCommandTests(unittest.TestCase):
    def test_vpn_command_uses_configured_executable(self) -> None:
        with (
            patch("assistant.Path.is_file", return_value=True),
            patch("assistant.launch_console_target") as launch_mock,
        ):
            result = assistant.open_special_command("VPN")

        self.assertEqual(result.kind, "success")
        launch_mock.assert_called_once_with(assistant.VPN_EXECUTABLE)

    def test_claude_code_command_uses_configured_shortcut(self) -> None:
        with (
            patch("assistant.Path.is_file", return_value=True),
            patch("assistant.launch_target") as launch_mock,
        ):
            result = assistant.open_special_command("Claude code")

        self.assertEqual(result.kind, "success")
        launch_mock.assert_called_once_with(str(assistant.CLAUDE_CODE_SHORTCUT))

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


if __name__ == "__main__":
    unittest.main()
