from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import ctypes
import json
import os
from pathlib import Path
import sys
from typing import Any, Literal
import uuid

import assistant
from game_mode import GameModeScan, ProcessCandidate, activate_game_mode, scan_game_mode, scan_named_processes


OutcomeStatus = Literal[
    "success",
    "error",
    "not_found",
    "info",
    "pending",
    "exit",
]


def app_data_directory() -> Path:
    configured_directory = os.environ.get("JARVIS_DATA_DIR")
    if configured_directory:
        return Path(configured_directory)
    return assistant.user_data_directory()


@dataclass(frozen=True)
class CommandRequest:
    text: str
    source: Literal["text", "voice", "ai"] = "text"


@dataclass(frozen=True)
class CommandOutcome:
    status: OutcomeStatus
    title: str
    detail: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PendingAction:
    id: str
    kind: Literal["power", "game_mode", "kill", "clear_history", "protocol"]
    command: str
    title: str
    detail: str
    payload: Any = None


def _timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class JsonListStore:
    def __init__(self, path: Path, *, limit: int | None = None) -> None:
        self.path = path
        self.limit = limit
        self.items = self._load()

    def _load(self) -> list[Any]:
        if not self.path.exists():
            return []
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            self._preserve_corrupt_file()
            return []
        return payload if isinstance(payload, list) else []

    def _preserve_corrupt_file(self) -> None:
        if not self.path.exists():
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = self.path.with_name(f"{self.path.stem}.corrupt-{stamp}{self.path.suffix}")
        try:
            self.path.replace(backup)
        except OSError:
            pass

    def _save_items(self, items: list[Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        stored_items = list(items[-self.limit :] if self.limit else items)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(
            json.dumps(stored_items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)
        self.items = stored_items

    def save(self) -> None:
        self._save_items(list(self.items))


class HistoryStore(JsonListStore):
    def __init__(self, path: Path | None = None, *, limit: int = 100) -> None:
        super().__init__(path or app_data_directory() / "history.json", limit=limit)
        self.items = [item for item in self.items if isinstance(item, dict)][-limit:]

    def add(
        self,
        request: CommandRequest,
        outcome: CommandOutcome,
        *,
        entry_id: str | None = None,
    ) -> dict[str, Any]:
        entry = {
            "id": entry_id or uuid.uuid4().hex,
            "timestamp": _timestamp(),
            "source": request.source,
            "command": request.text,
            "status": outcome.status,
            "title": outcome.title,
            "detail": outcome.detail,
        }
        program = str(outcome.data.get("program", "")).strip()
        program_title = str(outcome.data.get("program_title", "")).strip()
        if program:
            entry["program"] = program
        if program_title:
            entry["program_title"] = program_title
        self._save_items([*self.items, entry])
        return entry

    def update(self, entry_id: str, outcome: CommandOutcome) -> None:
        updated_items = list(self.items)
        for index, entry in enumerate(updated_items):
            if entry.get("id") == entry_id:
                updated_items[index] = {
                    **entry,
                    "timestamp": _timestamp(),
                    "status": outcome.status,
                    "title": outcome.title,
                    "detail": outcome.detail,
                }
                self._save_items(updated_items)
                return

    def remove(self, entry_id: str) -> bool:
        previous_length = len(self.items)
        updated_items = [item for item in self.items if item.get("id") != entry_id]
        if len(updated_items) == previous_length:
            return False
        self._save_items(updated_items)
        return True

    def clear(self) -> None:
        self._save_items([])


class NotesStore(JsonListStore):
    def __init__(
        self,
        path: Path | None = None,
        *,
        legacy_path: Path | None = None,
    ) -> None:
        target = path or app_data_directory() / "notes.json"
        super().__init__(target)
        self.items = [str(item) for item in self.items if isinstance(item, str) and item.strip()]
        self._migrate_legacy_notes(legacy_path)

    def _legacy_paths(self, explicit_path: Path | None) -> list[Path]:
        if explicit_path is not None:
            return [explicit_path]

        source_root = Path(__file__).resolve().parent
        executable_root = Path(sys.executable).resolve().parent
        working_root = Path.cwd()
        candidates = [
            assistant.notes_file_path(),
            executable_root / "notes.json",
            working_root / "notes.json",
            working_root / "dist" / "notes.json",
            source_root / "notes.json",
            source_root / "dist" / "notes.json",
        ]
        unique: list[Path] = []
        for candidate in candidates:
            try:
                resolved = candidate.resolve()
            except OSError:
                resolved = candidate
            if resolved != self.path.resolve() and resolved not in unique:
                unique.append(resolved)
        return unique

    def _migrate_legacy_notes(self, explicit_path: Path | None) -> None:
        marker = self.path.with_name(".notes-migrated-v1")
        if marker.exists():
            return

        migrated: list[str] = []
        if not self.items:
            for legacy in self._legacy_paths(explicit_path):
                if not legacy.exists():
                    continue
                try:
                    payload = json.loads(legacy.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if not isinstance(payload, list):
                    continue
                for item in payload:
                    value = str(item).strip() if isinstance(item, str) else ""
                    if value and value not in migrated:
                        migrated.append(value)

        if migrated:
            self._save_items(migrated)

        if self.items or migrated:
            try:
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.touch(exist_ok=True)
            except OSError:
                pass

    def add(self, text: str) -> list[str]:
        value = text.strip()
        if value:
            self._save_items([*self.items, value])
        return list(self.items)

    def update(self, index: int, text: str) -> list[str]:
        value = text.strip()
        if not value or not 0 <= index < len(self.items):
            raise ValueError("Не удалось изменить заметку.")
        updated_items = list(self.items)
        updated_items[index] = value
        self._save_items(updated_items)
        return list(self.items)

    def remove(self, index: int) -> list[str]:
        if not 0 <= index < len(self.items):
            raise ValueError("Заметка не найдена.")
        updated_items = list(self.items)
        updated_items.pop(index)
        self._save_items(updated_items)
        return list(self.items)

    def clear(self) -> list[str]:
        self._save_items([])
        return []


PROTOCOL_ACTION_TYPES = {
    "launch",
    "close",
    "volume_up",
    "volume_down",
    "volume_mute",
    "show_desktop",
    "lock_pc",
    "sleep",
    "shutdown",
    "restart",
}


class ProtocolStore(JsonListStore):
    def __init__(self, path: Path | None = None) -> None:
        super().__init__(path or app_data_directory() / "protocols.json")
        self.items = [item for item in self.items if self._valid_item(item)]

    @staticmethod
    def normalize_phrase(phrase: str) -> str:
        normalized = " ".join(str(phrase).strip().casefold().split())
        if normalized == "протокол":
            return ""
        if normalized.startswith("протокол "):
            normalized = normalized.removeprefix("протокол ").strip()
        return normalized

    @staticmethod
    def _valid_item(item: Any) -> bool:
        return (
            isinstance(item, dict)
            and isinstance(item.get("phrase"), str)
            and bool(item["phrase"].strip())
            and isinstance(item.get("actions"), list)
            and bool(item["actions"])
        )

    def save_protocol(self, phrase: str, actions: list[dict[str, Any]]) -> None:
        normalized = self.normalize_phrase(phrase)
        if not normalized:
            raise ValueError("Введите кодовую фразу после слова «протокол».")
        clean_actions: list[dict[str, str]] = []
        for action in actions:
            action_type = str(action.get("type", "")).strip().casefold()
            target = " ".join(str(action.get("target", "")).strip().split())
            if action_type not in PROTOCOL_ACTION_TYPES:
                raise ValueError("В протоколе есть неизвестное действие.")
            if action_type in {"launch", "close"} and not target:
                raise ValueError("Для запуска или закрытия укажите программу.")
            clean_actions.append({"type": action_type, "target": target})
        if not clean_actions:
            raise ValueError("Добавьте хотя бы одно действие.")
        updated = [item for item in self.items if item["phrase"] != normalized]
        self._save_items([*updated, {"phrase": normalized, "actions": clean_actions}])

    def remove_protocol(self, phrase: str) -> bool:
        normalized = self.normalize_phrase(phrase)
        updated = [item for item in self.items if item["phrase"] != normalized]
        if len(updated) == len(self.items):
            return False
        self._save_items(updated)
        return True

    def find(self, phrase: str) -> dict[str, Any] | None:
        normalized = self.normalize_phrase(phrase)
        return next((item for item in self.items if item["phrase"] == normalized), None)


def _send_windows_key(virtual_key: int, *, with_windows_key: bool = False) -> None:
    if os.name != "nt":
        raise OSError("Системное действие доступно только в Windows.")
    user32 = ctypes.windll.user32
    key_up = 0x0002
    if with_windows_key:
        user32.keybd_event(0x5B, 0, 0, 0)
    user32.keybd_event(virtual_key, 0, 0, 0)
    user32.keybd_event(virtual_key, 0, key_up, 0)
    if with_windows_key:
        user32.keybd_event(0x5B, 0, key_up, 0)


def _candidate_dict(candidate: ProcessCandidate) -> dict[str, Any]:
    return {
        "pid": candidate.pid,
        "name": candidate.name,
        "create_time": candidate.create_time,
        "gpu_usage": candidate.gpu_usage,
        "reason": candidate.reason,
    }


class CommandService:
    def __init__(
        self,
        *,
        program_map: dict[str, str] | None = None,
        history: HistoryStore | None = None,
        protocols: ProtocolStore | None = None,
    ) -> None:
        self.program_map = dict(program_map) if program_map is not None else assistant.get_program_map()
        self.history = history or HistoryStore()
        self.protocols = protocols or ProtocolStore()
        self._pending: dict[str, PendingAction] = {}

    @property
    def programs(self) -> list[str]:
        return sorted(self.program_map, key=str.casefold)

    @property
    def history_items(self) -> list[dict[str, Any]]:
        return list(self.history.items)

    def refresh_programs(self) -> CommandOutcome:
        program_map, error = assistant.generate_program_map()
        if error:
            return CommandOutcome("error", "Не удалось обновить программы", error)
        self.program_map = program_map
        return CommandOutcome(
            "success",
            "Список программ обновлён",
            f"Найдено программ: {len(program_map)}",
            {"programs": self.programs},
        )

    def execute(self, request: CommandRequest | str) -> CommandOutcome:
        if isinstance(request, str):
            request = CommandRequest(request)
        text = " ".join(request.text.strip().split())
        if not text:
            return CommandOutcome("not_found", "Введите команду")
        request = CommandRequest(text, request.source)
        try:
            outcome = self._prepare(request)
        except Exception as error:  # UI boundary: return a visible failure instead of crashing.
            outcome = CommandOutcome("error", "Команда не выполнена", str(error))
        pending_id = str(outcome.data.get("pending_id", ""))
        self.history.add(request, outcome, entry_id=pending_id or None)
        return outcome

    def _prepare(self, request: CommandRequest) -> CommandOutcome:
        command = request.text
        lowered = command.casefold()

        if lowered == "протокол":
            return CommandOutcome("not_found", "После слова «протокол» нужна кодовая фраза")
        if lowered.startswith("протокол "):
            protocol = self.protocols.find(command)
            if protocol is None:
                return CommandOutcome("not_found", f"Протокол «{command.split(maxsplit=1)[1]}» не найден")
            dangerous = any(action["type"] in {"sleep", "shutdown", "restart"} for action in protocol["actions"])
            if dangerous:
                return self._pending_outcome(
                    "protocol",
                    command,
                    f"Запустить протокол «{protocol['phrase']}»?",
                    "Протокол содержит управление питанием компьютера.",
                    protocol,
                )
            return self._execute_protocol_item(protocol)

        if lowered in assistant.EXIT_COMMANDS:
            return CommandOutcome("exit", "Завершаю Supersonic")
        if lowered in {"/help", "help", "помощь"}:
            return CommandOutcome(
                "info",
                "Команды Supersonic",
                "Открываю встроенную справку.",
                {"action": "help"},
            )
        if lowered in {"/apps", "apps", "программы", "список программ"}:
            return CommandOutcome(
                "info",
                f"Программы · {len(self.program_map)}",
                "Выберите приложение или введите его название.",
                {"action": "apps", "programs": self.programs},
            )
        if lowered in assistant.PRESET_LIST_COMMANDS:
            presets = [
                {"number": number, "title": title}
                for number, (title, _program) in assistant.PRESET_COMMANDS.items()
            ]
            return CommandOutcome("info", "Пресеты", "Доступно пять быстрых запусков.", {"presets": presets})
        if lowered in assistant.NOTES_COMMANDS:
            return CommandOutcome("info", "Заметки", "Открываю локальные заметки.", {"action": "notes"})
        if lowered in {"/clear", "clear", "очистить"}:
            return self._pending_outcome(
                "clear_history",
                command,
                "Очистить историю?",
                "Все сохранённые команды будут удалены.",
            )

        try:
            power_command = assistant.extract_power_command(command)
        except ValueError as error:
            return CommandOutcome("error", "Некорректная команда питания", str(error))
        if power_command is not None:
            descriptions = {
                "shutdown": "Windows завершит работу компьютера.",
                "restart": "Windows немедленно перезагрузит компьютер.",
                "sleep": "Компьютер перейдёт в спящий режим.",
                "abort": "Запланированное выключение будет отменено.",
            }
            if power_command.action == "shutdown" and power_command.delay_seconds:
                detail = f"Выключение будет запланировано через {power_command.delay_seconds // 60} мин."
            else:
                detail = descriptions[power_command.action]
            return self._pending_outcome("power", command, "Подтвердите действие", detail, power_command)

        kill_target = assistant.extract_kill_target(command)
        if kill_target is not None:
            if not kill_target:
                return CommandOutcome("not_found", "После kill нужно название программы", "Например: kill chrome")
            scan = scan_named_processes(assistant.normalize_kill_target(kill_target))
            if not scan.candidates:
                return CommandOutcome(
                    "not_found",
                    f"Не нашёл запущенный процесс «{kill_target}»",
                    data={"candidates": []},
                )
            return self._pending_outcome(
                "kill",
                command,
                f"Завершить «{kill_target}»?",
                f"Будет завершено деревьев процессов: {len(scan.candidates)}.",
                scan,
            )

        if lowered in assistant.GAME_MODE_PREVIEW_COMMANDS:
            return self.game_mode_preview()
        if lowered in assistant.GAME_MODE_COMMANDS:
            scan = scan_game_mode()
            if not scan.candidates:
                return CommandOutcome(
                    "success",
                    "Закрывать нечего",
                    scan.warning or "Заметной GPU-нагрузки нет.",
                    {"candidates": [], "warning": scan.warning},
                )
            return self._pending_outcome(
                "game_mode",
                command,
                "Включить игровой режим?",
                f"Будет завершено приложений: {len(scan.candidates)}.",
                scan,
            )
        if lowered in assistant.SPECIAL_LAUNCH_COMMANDS:
            title = assistant.SPECIAL_LAUNCH_COMMANDS[lowered][0]
            return self._launch_outcome(
                assistant.open_special_command(lowered),
                program=lowered,
                program_title=title,
            )
        if lowered in assistant.PRESET_COMMANDS:
            title, program_name = assistant.PRESET_COMMANDS[lowered]
            return self._launch_outcome(
                assistant.open_preset(lowered, self.program_map),
                program=str(program_name or "yandex browser"),
                program_title=title,
            )

        program_name = assistant.extract_program_name(command)
        if not program_name:
            return CommandOutcome("not_found", "После команды нужно название", "Например: открой VS Code")
        matched_name, _score = assistant.find_program(program_name, self.program_map)
        return self._launch_outcome(
            assistant.open_program(program_name, self.program_map),
            program=matched_name or "",
            program_title=matched_name or program_name,
        )

    def _execute_protocol(self, command: str) -> CommandOutcome:
        protocol = self.protocols.find(command)
        if protocol is None:
            return CommandOutcome("not_found", f"Протокол «{command.removeprefix('протокол ').strip()}» не найден")
        return self._execute_protocol_item(protocol)

    def _execute_protocol_item(self, protocol: dict[str, Any]) -> CommandOutcome:
        completed: list[str] = []
        for action in protocol["actions"]:
            action_type = action["type"]
            target = action.get("target", "")
            if action_type == "launch":
                result = assistant.open_program(target, self.program_map)
                if result.kind != "success":
                    return CommandOutcome("error", "Протокол остановлен", result.title)
                completed.append(f"открыто: {target}")
            elif action_type == "close":
                scan = scan_named_processes(assistant.normalize_kill_target(target))
                if scan.candidates:
                    result = activate_game_mode(scan, force=True)
                    if result.failed:
                        return CommandOutcome("error", "Протокол остановлен", f"Не удалось закрыть {target}")
                completed.append(f"закрыто: {target}")
            elif action_type == "volume_up":
                _send_windows_key(0xAF)
                completed.append("громкость увеличена")
            elif action_type == "volume_down":
                _send_windows_key(0xAE)
                completed.append("громкость уменьшена")
            elif action_type == "volume_mute":
                _send_windows_key(0xAD)
                completed.append("звук переключён")
            elif action_type == "show_desktop":
                _send_windows_key(0x44, with_windows_key=True)
                completed.append("показан рабочий стол")
            elif action_type == "lock_pc":
                if os.name != "nt" or not ctypes.windll.user32.LockWorkStation():
                    raise OSError("Не удалось заблокировать компьютер.")
                completed.append("компьютер заблокирован")
            elif action_type in {"sleep", "shutdown", "restart"}:
                power_action = {
                    "sleep": assistant.PowerCommand("sleep"),
                    "shutdown": assistant.PowerCommand("shutdown"),
                    "restart": assistant.PowerCommand("restart"),
                }[action_type]
                result = assistant.execute_power_command(power_action)
                if result.kind != "success":
                    return CommandOutcome("error", "Протокол остановлен", result.title)
                completed.append({
                    "sleep": "включён спящий режим",
                    "shutdown": "запущено выключение",
                    "restart": "запущена перезагрузка",
                }[action_type])
        return CommandOutcome(
            "success",
            f"Протокол «{protocol['phrase']}» выполнен",
            " · ".join(completed),
            {"action": "protocol", "protocol": protocol["phrase"]},
        )

    def _pending_outcome(
        self,
        kind: PendingAction.__annotations__["kind"],
        command: str,
        title: str,
        detail: str,
        payload: Any = None,
    ) -> CommandOutcome:
        pending_id = uuid.uuid4().hex
        self._pending[pending_id] = PendingAction(pending_id, kind, command, title, detail, payload)
        data: dict[str, Any] = {"pending_id": pending_id, "kind": kind}
        if isinstance(payload, GameModeScan):
            data["candidates"] = [_candidate_dict(item) for item in payload.candidates]
            data["warning"] = payload.warning
        return CommandOutcome("pending", title, detail, data)

    def confirm(self, pending_id: str) -> CommandOutcome:
        action = self._pending.pop(pending_id, None)
        if action is None:
            return CommandOutcome("error", "Действие уже выполнено или отменено")
        try:
            if action.kind == "clear_history":
                self.history.clear()
                return CommandOutcome("success", "История очищена")
            if action.kind == "power":
                outcome = self._launch_outcome(assistant.execute_power_command(action.payload))
            elif action.kind == "protocol":
                outcome = self._execute_protocol_item(action.payload)
            else:
                result = activate_game_mode(action.payload, force=action.kind == "kill")
                if result.failed:
                    failed = "; ".join(f"{candidate.name}: {error}" for candidate, error in result.failed)
                    outcome = CommandOutcome(
                        "error",
                        f"Завершено: {len(result.closed)}, ошибок: {len(result.failed)}",
                        failed,
                    )
                else:
                    title = "Игровой режим включён" if action.kind == "game_mode" else "Приложение завершено"
                    outcome = CommandOutcome("success", title, f"Завершено деревьев процессов: {len(result.closed)}")
        except Exception as error:  # Destructive adapter boundary.
            outcome = CommandOutcome("error", "Не удалось выполнить действие", str(error))
        self.history.update(pending_id, outcome)
        return outcome

    def cancel(self, pending_id: str) -> CommandOutcome:
        action = self._pending.pop(pending_id, None)
        if action is None:
            return CommandOutcome("error", "Действие уже выполнено или отменено")
        outcome = CommandOutcome("info", "Действие отменено")
        self.history.update(pending_id, outcome)
        return outcome

    def game_mode_preview(self) -> CommandOutcome:
        scan = scan_game_mode()
        candidates = [_candidate_dict(item) for item in scan.candidates]
        if not candidates:
            return CommandOutcome("success", "Закрывать нечего", scan.warning or "Заметной GPU-нагрузки нет.", {"candidates": []})
        return CommandOutcome(
            "info",
            f"Найдено приложений: {len(candidates)}",
            scan.warning,
            {"candidates": candidates},
        )

    @staticmethod
    def _launch_outcome(
        result: assistant.LaunchResult,
        *,
        program: str = "",
        program_title: str = "",
    ) -> CommandOutcome:
        data: dict[str, Any] = {}
        if result.kind == "success" and program:
            data = {
                "action": "launch_program",
                "program": program,
                "program_title": program_title or program,
            }
        return CommandOutcome(result.kind, result.title, result.detail, data)
