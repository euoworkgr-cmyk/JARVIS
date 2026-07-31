from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from desktop_backend import DesktopBackend
from user_settings import AppSettings, STORE_FILES, configure_data_directory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class UserSettingsTests(unittest.TestCase):
    def test_personal_store_is_migrated_to_stable_local_app_data(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            installation = root / "Supersonic"
            legacy = root / "JARVIS-Personal" / "data"
            local_app_data = root / "LocalAppData"
            installation.mkdir()
            legacy.mkdir(parents=True)
            for index, filename in enumerate(STORE_FILES):
                (legacy / filename).write_text(
                    json.dumps({"value": index}), encoding="utf-8"
                )

            with (
                patch.dict(
                    os.environ,
                    {"LOCALAPPDATA": str(local_app_data)},
                    clear=True,
                ),
                patch("user_settings.os.name", "nt"),
                patch("user_settings.sys.frozen", True, create=True),
            ):
                target = configure_data_directory(installation)

            self.assertEqual(target, local_app_data / "Supersonic")
            for index, filename in enumerate(STORE_FILES):
                self.assertEqual(
                    json.loads((target / filename).read_text(encoding="utf-8")),
                    {"value": index},
                )

    def test_migration_never_overwrites_new_store(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            installation = root / "Supersonic"
            legacy = root / "JARVIS-Personal" / "data"
            target = root / "stable"
            installation.mkdir()
            legacy.mkdir(parents=True)
            target.mkdir()
            (legacy / "history.json").write_text('"legacy"', encoding="utf-8")
            (target / "history.json").write_text('"current"', encoding="utf-8")

            with patch.dict(os.environ, {"JARVIS_DATA_DIR": str(target)}, clear=True):
                configure_data_directory(installation)

            self.assertEqual(
                json.loads((target / "history.json").read_text(encoding="utf-8")),
                "current",
            )

    @patch("desktop_backend.set_windows_autostart", return_value=(True, ""))
    def test_autostart_and_voice_require_explicit_opt_in(self, autostart_mock) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = AppSettings(Path(directory) / "settings.json")
            backend = DesktopBackend(
                Path(__file__).resolve().parent,
                autostart_name="Supersonic",
                legacy_autostart_names=("JARVIS Personal",),
                settings=settings,
            )
            backend.startVoiceControl = MagicMock()

            self.assertFalse(backend.autostartEnabled)
            self.assertFalse(backend.voiceStartupEnabled)
            self.assertEqual(backend.colorScheme, "dark")
            autostart_mock.assert_called_once_with(
                "Supersonic", False, ("JARVIS Personal",)
            )

            backend.setAutostartEnabled(True)
            backend.setVoiceStartupEnabled(True)

            autostart_mock.assert_called_with(
                "Supersonic", True, ("JARVIS Personal",)
            )
            backend.startVoiceControl.assert_called_once_with()
            self.assertTrue(backend.autostartEnabled)
            self.assertTrue(backend.voiceStartupEnabled)

            backend.setAutostartEnabled(False)
            backend.setVoiceStartupEnabled(False)

            autostart_mock.assert_called_with(
                "Supersonic", False, ("JARVIS Personal",)
            )
            self.assertFalse(backend.autostartEnabled)
            self.assertFalse(backend.voiceStartupEnabled)

            backend.setColorScheme("light")
            self.assertEqual(backend.colorScheme, "light")
            self.assertEqual(settings.get_str("colorScheme"), "light")

    @patch("desktop_backend.set_windows_autostart", return_value=(False, "denied"))
    def test_registry_error_is_visible_and_does_not_enable_autostart(
        self, _autostart_mock
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            backend = DesktopBackend(
                Path(__file__).resolve().parent,
                autostart_name="Supersonic",
                settings=AppSettings(Path(directory) / "settings.json"),
            )

            backend.setAutostartEnabled(True)

            self.assertFalse(backend.autostartEnabled)
            self.assertEqual(backend.preferenceError, "denied")


if __name__ == "__main__":
    unittest.main()
