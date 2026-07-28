from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any


STORE_FILES = ("history.json", "notes.json", "programs.json", "pet_state.json")


def configure_data_directory(installation_directory: Path) -> Path:
    """Select a stable store and migrate data from known pre-rename locations."""
    configured = os.environ.get("JARVIS_DATA_DIR", "").strip()
    if configured:
        target = Path(configured)
    elif os.name == "nt" and getattr(sys, "frozen", False):
        local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
        target = (
            Path(local_app_data) / "Supersonic"
            if local_app_data
            else installation_directory / "data"
        )
    else:
        target = installation_directory / "data"

    target.mkdir(parents=True, exist_ok=True)
    os.environ["JARVIS_DATA_DIR"] = str(target)
    _migrate_legacy_stores(target, installation_directory)
    return target


def _legacy_data_directories(installation_directory: Path) -> list[Path]:
    candidates = [
        installation_directory / "data",
        installation_directory.parent / "JARVIS-Personal" / "data",
    ]
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if local_app_data:
        candidates.append(Path(local_app_data) / "JARVIS-Personal" / "data")
    return candidates


def _migrate_legacy_stores(target: Path, installation_directory: Path) -> None:
    target_resolved = target.resolve()
    for filename in STORE_FILES:
        destination = target / filename
        if destination.exists():
            continue
        for legacy_directory in _legacy_data_directories(installation_directory):
            try:
                if legacy_directory.resolve() == target_resolved:
                    continue
            except OSError:
                continue
            source = legacy_directory / filename
            if not source.is_file():
                continue
            temporary: Path | None = None
            try:
                with tempfile.NamedTemporaryFile(
                    dir=target, prefix=f".{filename}.", suffix=".tmp", delete=False
                ) as stream:
                    temporary = Path(stream.name)
                shutil.copy2(source, temporary)
                os.replace(temporary, destination)
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            break


class AppSettings:
    DEFAULTS = {
        "autostartEnabled": False,
        "voiceStartupEnabled": False,
    }

    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            data_directory = Path(
                os.environ.get("JARVIS_DATA_DIR", Path(__file__).resolve().parent / "data")
            )
            path = data_directory / "app_settings.json"
        self.path = path
        self._values = self._load()

    def _load(self) -> dict[str, Any]:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return dict(self.DEFAULTS)
        if not isinstance(value, dict):
            return dict(self.DEFAULTS)
        return {**self.DEFAULTS, **value}

    def get_bool(self, name: str) -> bool:
        return bool(self._values.get(name, self.DEFAULTS.get(name, False)))

    def set_bool(self, name: str, value: bool) -> None:
        self._values[name] = bool(value)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        try:
            temporary.write_text(
                json.dumps(self._values, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            os.replace(temporary, self.path)
        finally:
            temporary.unlink(missing_ok=True)


def set_windows_autostart(
    value_name: str,
    enabled: bool,
    legacy_value_names: tuple[str, ...] = (),
) -> tuple[bool, str]:
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return False, "Автозапуск доступен только в установленной Windows-сборке"
    try:
        import winreg

        command = f'"{Path(sys.executable).resolve()}"'
        with winreg.CreateKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
        ) as key:
            if enabled:
                winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, value_name)
                except FileNotFoundError:
                    pass
            for legacy_name in legacy_value_names:
                if legacy_name == value_name:
                    continue
                try:
                    winreg.DeleteValue(key, legacy_name)
                except FileNotFoundError:
                    pass
        return True, ""
    except OSError as error:
        return False, str(error)
