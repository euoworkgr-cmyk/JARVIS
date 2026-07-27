from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
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
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / assistant.APP_NAME
    return Path.home() / f".{assistant.APP_NAME.casefold()}"


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
    kind: Literal["power", "game_mode", "kill", "clear_history"]
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

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        items = self.items[-self.limit :] if self.limit else self.items
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(
            json.dumps(items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)
        self.items = list(items)


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
        self.items.append(entry)
        self.save()
        return entry

    def update(self, entry_id: str, outcome: CommandOutcome) -> None:
        for entry in self.items:
            if entry.get("id") == entry_id:
                entry.update(
                    {
                        "timestamp": _timestamp(),
                        "status": outcome.status,
                        "title": outcome.title,
                        "detail": outcome.detail,
                    }
                )
                self.save()
                return

    def remove(self, entry_id: str) -> bool:
        previous_length = len(self.items)
        self.items = [item for item in self.items if item.get("id") != entry_id]
        if len(self.items) == previous_length:
            return False
        self.save()
        return True

    def clear(self) -> None:
        self.items.clear()
        self.save()


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
            self.items = migrated
            self.save()

        if self.items or migrated:
            try:
                marker.parent.mkdir(parents=True, exist_ok=True)
                marker.touch(exist_ok=True)
            except OSError:
                pass

    def add(self, text: str) -> list[str]:
        value = text.strip()
        if value:
            self.items.append(value)
            self.save()
        return list(self.items)

    def update(self, index: int, text: str) -> list[str]:
        value = text.strip()
        if not value or not 0 <= index < len(self.items):
            raise ValueError("Не удалось изменить заметку.")
        self.items[index] = value
        self.save()
        return list(self.items)

    def remove(self, index: int) -> list[str]:
        if not 0 <= index < len(self.items):
            raise ValueError("Заметка не найдена.")
        self.items.pop(index)
        self.save()
        return list(self.items)

    def clear(self) -> list[str]:
        self.items.clear()
        self.save()
        return []


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
    ) -> None:
        self.program_map = dict(program_map) if program_map is not None else assistant.get_program_map()
        self.history = history or HistoryStore()
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

        if lowered in assistant.EXIT_COMMANDS:
            return CommandOutcome("exit", "Завершаю JARVIS")
        if lowered in {"/help", "help", "помощь"}:
            return CommandOutcome(
                "info",
                "Команды JARVIS",
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
                return CommandOutcome("not_found", f"Не нашёл запущенный процесс «{kill_target}»")
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
                return CommandOutcome("success", "Закрывать нечего", scan.warning or "Заметной GPU-нагрузки нет.")
            return self._pending_outcome(
                "game_mode",
                command,
                "Включить игровой режим?",
                f"Будет завершено приложений: {len(scan.candidates)}.",
                scan,
            )
        if lowered in assistant.SPECIAL_LAUNCH_COMMANDS:
            return self._launch_outcome(assistant.open_special_command(lowered))
        if lowered in assistant.PRESET_COMMANDS:
            return self._launch_outcome(assistant.open_preset(lowered, self.program_map))

        program_name = assistant.extract_program_name(command)
        if not program_name:
            return CommandOutcome("not_found", "После команды нужно название", "Например: открой VS Code")
        return self._launch_outcome(assistant.open_program(program_name, self.program_map))

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
    def _launch_outcome(result: assistant.LaunchResult) -> CommandOutcome:
        return CommandOutcome(result.kind, result.title, result.detail)
