from __future__ import annotations

import unittest
from unittest.mock import patch

import assistant


class AssistantSpecialCommandTests(unittest.TestCase):
    def test_vpn_command_uses_configured_executable(self) -> None:
        with (
            patch("assistant.Path.is_file", return_value=True),
            patch("assistant.launch_target") as launch_mock,
        ):
            result = assistant.open_special_command("VPN")

        self.assertEqual(result.kind, "success")
        launch_mock.assert_called_once_with(str(assistant.VPN_EXECUTABLE))

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


if __name__ == "__main__":
    unittest.main()
