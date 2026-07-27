from __future__ import annotations

import ctypes
from collections import Counter
from datetime import datetime
import getpass
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Callable

import psutil
from PySide6.QtCore import Property, QObject, QRunnable, QThreadPool, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication, QWindow

import assistant
from command_service import CommandOutcome, CommandService, NotesStore
from desktop_pet import WINDOW_SIZE, Point, clamp_position, default_position, get_work_areas, load_position, pet_state_path, save_position


PRESET_DISPLAY_TITLES = {
    "1": "Яндекс Браузер",
    "2": "ChatGPT",
    "3": "VS Code",
    "4": "Telegram",
    "5": "Камера",
}

PRESET_ICON_NAMES = {
    "1": ("Яндекс", "Yandex"),
    "2": ("ChatGPT", "Codex"),
    "3": ("Visual Studio Code", "VS Code"),
    "4": ("Telegram",),
    "5": ("Камера", "Camera"),
}


def reduced_motion_enabled() -> bool:
    if assistant.os.name != "nt":
        return False
    enabled = ctypes.c_bool(True)
    try:
        success = ctypes.windll.user32.SystemParametersInfoW(
            0x1042,  # SPI_GETCLIENTAREAANIMATION
            0,
            ctypes.byref(enabled),
            0,
        )
    except (AttributeError, OSError):
        return False
    return bool(success) and not enabled.value


def _format_bytes(value: int) -> str:
    amount = float(max(0, value))
    units = ("Б", "КБ", "МБ", "ГБ", "ТБ")
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            digits = 0 if unit in {"Б", "КБ", "МБ"} else 1
            return f"{amount:.{digits}f} {unit}".replace(".0 ", " ").replace(".", ",")
        amount /= 1024
    return f"{amount:.1f} ТБ".replace(".", ",")


def _gpu_snapshot() -> dict[str, Any]:
    executable = shutil.which("nvidia-smi")
    if not executable and os.name == "nt":
        candidate = (
            Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
            / "NVIDIA Corporation"
            / "NVSMI"
            / "nvidia-smi.exe"
        )
        if candidate.is_file():
            executable = str(candidate)
    if not executable:
        return {"percent": 0, "detail": "Нет данных", "available": False}
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    try:
        completed = subprocess.run(
            [
                executable,
                "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=True,
            creationflags=creation_flags,
        )
        values = [part.strip() for part in completed.stdout.splitlines()[0].split(",")]
        usage, used_memory, total_memory, temperature = (float(value) for value in values[:4])
    except (IndexError, OSError, subprocess.SubprocessError, ValueError):
        return {"percent": 0, "detail": "Нет данных", "available": False}
    return {
        "percent": round(usage),
        "detail": (
            f"{temperature:.0f} °C · {used_memory / 1024:.1f} / "
            f"{total_memory / 1024:.1f} ГБ"
        ).replace(".", ","),
        "available": True,
    }


def collect_system_snapshot() -> dict[str, Any]:
    cpu_percent = round(psutil.cpu_percent(interval=0.15))
    frequency = psutil.cpu_freq()
    cpu_detail = (
        f"{frequency.current / 1000:.1f} ГГц".replace(".", ",")
        if frequency
        else "Активен"
    )
    memory = psutil.virtual_memory()
    disks: list[dict[str, Any]] = []
    seen_devices: set[str] = set()
    for partition in psutil.disk_partitions(all=False):
        device = partition.device or partition.mountpoint
        normalized = device.casefold()
        if normalized in seen_devices or "cdrom" in partition.opts.casefold():
            continue
        seen_devices.add(normalized)
        try:
            usage = psutil.disk_usage(partition.mountpoint)
        except (OSError, PermissionError):
            continue
        disks.append(
            {
                "name": device.rstrip("\\/") or partition.mountpoint,
                "percent": round(usage.percent),
                "used": _format_bytes(usage.used),
                "total": _format_bytes(usage.total),
                "detail": f"{_format_bytes(usage.used)} / {_format_bytes(usage.total)}",
            }
        )
    return {
        "resources": {
            "cpu": {
                "label": "CPU",
                "percent": cpu_percent,
                "detail": cpu_detail,
                "available": True,
            },
            "gpu": {"label": "GPU", **_gpu_snapshot()},
            "memory": {
                "label": "RAM",
                "percent": round(memory.percent),
                "detail": f"{_format_bytes(memory.used)} / {_format_bytes(memory.total)}",
                "available": True,
            },
        },
        "disks": disks,
        "updated": datetime.now().strftime("%H:%M:%S"),
    }


class WorkerSignals(QObject):
    finished = Signal(object)
    failed = Signal(str)


class TaskWorker(QRunnable):
    def __init__(self, task: Callable[[], Any]) -> None:
        super().__init__()
        self.task = task
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self.task()
        except Exception as error:
            self.signals.failed.emit(str(error))
            return
        self.signals.finished.emit(result)


class DesktopBackend(QObject):
    historyChanged = Signal()
    programsChanged = Signal()
    notesChanged = Signal()
    busyChanged = Signal()
    stateChanged = Signal()
    currentPageChanged = Signal()
    pendingActionChanged = Signal()
    gameScanChanged = Signal()
    lastMessageChanged = Signal()
    petPositionChanged = Signal()
    petVisibleChanged = Signal()
    quittingChanged = Signal()
    systemStatsChanged = Signal()
    voiceStatusChanged = Signal()
    commandOutcome = Signal(object)

    showMainRequested = Signal()
    helpRequested = Signal()
    quitRequested = Signal()

    def __init__(self, resource_directory: Path) -> None:
        super().__init__()
        self.resource_directory = resource_directory
        self.service = CommandService()
        self.notes_store = NotesStore()
        self.thread_pool = QThreadPool.globalInstance()
        self._workers: set[TaskWorker] = set()
        self._main_window = None
        self._busy = False
        self._state = "idle"
        self._current_page = "home"
        self._pending_action: dict[str, Any] = {}
        self._game_candidates: list[dict[str, Any]] = []
        self._game_warning = ""
        self._last_message: dict[str, Any] = {}
        self._message_token = 0
        self._state_token = 0
        self._pet_visible = True
        self._quitting = False
        self._reduced_motion = reduced_motion_enabled()
        self._preset_icon_targets: dict[str, str | None] = {}
        self._system_stats: dict[str, Any] = {
            "cpu": {
                "label": "CPU",
                "percent": 0,
                "detail": "Ожидание",
                "available": True,
            },
            "gpu": {
                "label": "GPU",
                "percent": 0,
                "detail": "Ожидание",
                "available": False,
            },
            "memory": {
                "label": "RAM",
                "percent": 0,
                "detail": "Ожидание",
                "available": True,
            },
        }
        self._disk_items: list[dict[str, Any]] = []
        self._stats_updated_label = "Ожидание обновления"
        self._stats_refreshing = False
        self._voice_controller = None
        self._voice_status = "disabled"
        self._voice_status_label = "Голосовое управление не запущено"
        self._stats_timer = QTimer(self)
        self._stats_timer.setInterval(3000)
        self._stats_timer.timeout.connect(self.refreshSystemStats)

        work_areas = get_work_areas()
        if work_areas:
            stored = load_position(pet_state_path())
            self._pet_position = clamp_position(
                stored or default_position(work_areas[0]),
                WINDOW_SIZE,
                work_areas,
            )
        else:
            self._pet_position = Point(24, 24)

    def set_main_window(self, window) -> None:
        self._main_window = window

    @Property("QVariantList", notify=historyChanged)
    def historyItems(self) -> list[dict[str, Any]]:
        return self.service.history_items

    @Property("QVariantList", notify=programsChanged)
    def programItems(self) -> list[dict[str, str]]:
        return [{"name": name} for name in self.service.programs]

    @Property("QVariantList", notify=notesChanged)
    def noteItems(self) -> list[dict[str, Any]]:
        return [
            {"index": index, "text": text}
            for index, text in enumerate(self.notes_store.items)
        ]

    @Property(str, constant=True)
    def displayName(self) -> str:
        value = (os.environ.get("USERNAME") or getpass.getuser() or "Пользователь").strip()
        return value[:1].upper() + value[1:] if value else "Пользователь"

    @Property("QVariantList", notify=programsChanged)
    def presetItems(self) -> list[dict[str, Any]]:
        return [
            {
                "number": number,
                "title": PRESET_DISPLAY_TITLES.get(number, title),
                "program": str(program_name or "yandex browser"),
                "monogram": self._program_monogram(
                    PRESET_DISPLAY_TITLES.get(number, title)
                ),
            }
            for number, (title, program_name) in assistant.PRESET_COMMANDS.items()
        ]

    def preset_icon_target(self, number: str) -> str | None:
        if number in self._preset_icon_targets:
            return self._preset_icon_targets[number]

        preset = assistant.PRESET_COMMANDS.get(number)
        if preset is None:
            self._preset_icon_targets[number] = None
            return None

        _title, program_name = preset
        candidates: list[Path] = []
        if number == "1":
            candidates.append(assistant.YANDEX_BROWSER_EXECUTABLE)

        target = self.service.program_map.get(str(program_name or "yandex browser"), "")
        expanded_target = Path(os.path.expandvars(target)) if target else None
        if expanded_target is not None and expanded_target.is_file():
            candidates.append(expanded_target)

        local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
        roaming_app_data = Path(os.environ.get("APPDATA", ""))
        program_files = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
        candidates.extend(
            {
                "2": [
                    local_app_data / "Programs" / "ChatGPT" / "ChatGPT.exe",
                    local_app_data / "Microsoft" / "WindowsApps" / "ChatGPT.exe",
                ],
                "3": [
                    local_app_data / "Programs" / "Microsoft VS Code" / "Code.exe",
                    program_files / "Microsoft VS Code" / "Code.exe",
                ],
                "4": [
                    roaming_app_data / "Telegram Desktop" / "Telegram.exe",
                    local_app_data / "Telegram Desktop" / "Telegram.exe",
                ],
            }.get(number, [])
        )

        result = next((str(candidate) for candidate in candidates if candidate.is_file()), None)
        if result is not None:
            self._preset_icon_targets[number] = result
            return result

        start_menu_roots = [
            roaming_app_data / "Microsoft" / "Windows" / "Start Menu" / "Programs",
            Path(os.environ.get("ProgramData", r"C:\ProgramData"))
            / "Microsoft"
            / "Windows"
            / "Start Menu"
            / "Programs",
        ]
        names = tuple(name.casefold() for name in PRESET_ICON_NAMES.get(number, ()))
        for start_menu in start_menu_roots:
            if not start_menu.is_dir():
                continue
            try:
                shortcuts = start_menu.rglob("*.lnk")
                candidates.extend(
                    shortcut
                    for shortcut in shortcuts
                    if any(name in shortcut.stem.casefold() for name in names)
                )
            except OSError:
                continue

        result = next((str(candidate) for candidate in candidates if candidate.is_file()), None)
        self._preset_icon_targets[number] = result
        return result

    @Property("QVariantList", constant=True)
    def protocolItems(self) -> list[dict[str, Any]]:
        return [
            {
                "id": "game_mode",
                "title": "Игровой режим",
                "detail": "Освободить ресурсы перед запуском игры",
                "symbol": "◆",
                "extra": True,
            },
            {
                "id": "vpn",
                "title": "VPN",
                "detail": "Запустить личное VPN-подключение",
                "symbol": "◈",
                "extra": False,
            },
            {
                "id": "claude_code",
                "title": "Claude Code",
                "detail": "Открыть рабочую консоль Claude Code",
                "symbol": "⌁",
                "extra": False,
            },
        ]

    @Property("QVariantList", notify=historyChanged)
    def frequentPrograms(self) -> list[dict[str, Any]]:
        preset_commands = set(assistant.PRESET_COMMANDS)
        preset_programs = {
            str(program_name or "yandex browser").casefold()
            for _title, program_name in assistant.PRESET_COMMANDS.values()
        }
        counts: Counter[str] = Counter()
        display_names: dict[str, str] = {}
        for entry in self.service.history_items:
            if entry.get("status") != "success":
                continue
            command = str(entry.get("command", "")).strip()
            if command.casefold() in preset_commands:
                continue
            program = str(entry.get("program", "")).strip()
            title = str(entry.get("program_title", "")).strip()
            if not program:
                outcome_title = str(entry.get("title", "")).strip()
                if not outcome_title.startswith("Открываю"):
                    continue
                title = outcome_title.removeprefix("Открываю:").removeprefix("Открываю").strip()
                program = title.casefold()
            key = program.casefold()
            if not key or key in preset_programs or key == "jarvis":
                continue
            counts[key] += 1
            display_names[key] = title or self._display_program_name(program)
        maximum = max(counts.values(), default=1)
        return [
            {
                "name": display_names[key],
                "command": key,
                "launches": count,
                "launchLabel": self._launch_count_label(count),
                "ratio": count / maximum,
                "monogram": self._program_monogram(display_names[key]),
                "bars": self._usage_bars(key, count),
            }
            for key, count in counts.most_common(4)
        ]

    @Property("QVariantMap", notify=systemStatsChanged)
    def systemStats(self) -> dict[str, Any]:
        return dict(self._system_stats)

    @Property("QVariantList", notify=systemStatsChanged)
    def diskItems(self) -> list[dict[str, Any]]:
        return list(self._disk_items)

    @Property(str, notify=systemStatsChanged)
    def statsUpdatedLabel(self) -> str:
        return self._stats_updated_label

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=stateChanged)
    def jarvisState(self) -> str:
        return self._state

    @Property(str, notify=stateChanged)
    def stateLabel(self) -> str:
        return {
            "idle": "Готов к работе",
            "working": "Выполняю команду",
            "success": "Команда выполнена",
            "error": "Нужна проверка",
            "pending": "Жду подтверждения",
            "listening": "Слушаю команду",
            "recognizing": "Распознаю речь",
        }.get(self._state, "Готов к работе")

    @Property(str, notify=voiceStatusChanged)
    def voiceStatus(self) -> str:
        return self._voice_status

    @Property(str, notify=voiceStatusChanged)
    def voiceStatusLabel(self) -> str:
        return self._voice_status_label

    @Property(str, notify=currentPageChanged)
    def currentPage(self) -> str:
        return self._current_page

    @Property("QVariantMap", notify=pendingActionChanged)
    def pendingAction(self) -> dict[str, Any]:
        return dict(self._pending_action)

    @Property("QVariantList", notify=gameScanChanged)
    def gameCandidates(self) -> list[dict[str, Any]]:
        return list(self._game_candidates)

    @Property(str, notify=gameScanChanged)
    def gameWarning(self) -> str:
        return self._game_warning

    @Property("QVariantMap", notify=lastMessageChanged)
    def lastMessage(self) -> dict[str, Any]:
        return dict(self._last_message)

    @Property(bool, constant=True)
    def reducedMotion(self) -> bool:
        return self._reduced_motion

    @Property(int, notify=petPositionChanged)
    def petX(self) -> int:
        return self._pet_position.x

    @Property(int, notify=petPositionChanged)
    def petY(self) -> int:
        return self._pet_position.y

    @Property(bool, notify=petVisibleChanged)
    def petVisible(self) -> bool:
        return self._pet_visible

    @Property(bool, notify=quittingChanged)
    def quitting(self) -> bool:
        return self._quitting

    def _set_busy(self, value: bool) -> None:
        if self._busy == value:
            return
        self._busy = value
        self.busyChanged.emit()

    @staticmethod
    def _display_program_name(value: str) -> str:
        known = {
            "visual studio code": "Visual Studio Code",
            "google chrome": "Google Chrome",
            "claude code": "Claude Code",
            "vpn": "VPN",
        }
        return known.get(value.casefold(), value[:1].upper() + value[1:])

    @staticmethod
    def _program_monogram(value: str) -> str:
        words = [word for word in value.replace("-", " ").split() if word]
        if not words:
            return "•"
        if len(words) == 1:
            return words[0][:2].upper()
        return "".join(word[0].upper() for word in words[:2])

    @staticmethod
    def _launch_count_label(count: int) -> str:
        last_two = count % 100
        last = count % 10
        if 11 <= last_two <= 14:
            ending = "запусков"
        elif last == 1:
            ending = "запуск"
        elif 2 <= last <= 4:
            ending = "запуска"
        else:
            ending = "запусков"
        return f"{count} {ending}"

    @staticmethod
    def _usage_bars(key: str, count: int) -> list[float]:
        seed = sum(ord(character) for character in key) + count * 17
        return [
            0.28 + ((seed * (index + 3) + index * 29) % 64) / 100
            for index in range(10)
        ]

    def _set_state(self, value: str, *, restore: bool = False) -> None:
        self._state_token += 1
        token = self._state_token
        if self._state != value:
            self._state = value
            self.stateChanged.emit()
        if restore:
            QTimer.singleShot(1800, lambda: self._restore_idle(token))

    def _restore_idle(self, token: int) -> None:
        if token != self._state_token:
            return
        if not self._busy and not self._pending_action:
            self._set_state("idle")

    def _run_task(
        self,
        task: Callable[[], Any],
        completed: Callable[[Any], None],
    ) -> None:
        if self._busy:
            return
        self._set_busy(True)
        self._set_state("working")
        worker = TaskWorker(task)
        self._workers.add(worker)

        def finish(result: Any) -> None:
            self._workers.discard(worker)
            self._set_busy(False)
            completed(result)

        def fail(message: str) -> None:
            self._workers.discard(worker)
            self._set_busy(False)
            self._handle_outcome(CommandOutcome("error", "Операция не выполнена", message))

        worker.signals.finished.connect(finish)
        worker.signals.failed.connect(fail)
        self.thread_pool.start(worker)

    @Slot(str)
    def executeCommand(self, text: str) -> None:
        if not text.strip() or self._busy:
            return
        self._run_task(lambda: self.service.execute(text), self._handle_outcome)

    @Slot(str)
    def executeVoiceCommand(self, text: str) -> None:
        if self._busy:
            self.commandOutcome.emit(
                {
                    "status": "error",
                    "title": "Я уже выполняю другую команду",
                    "detail": "Повторите голосовую команду после завершения текущей.",
                }
            )
            return
        self.executeCommand(text)

    def _handle_outcome(self, outcome: CommandOutcome) -> None:
        self.historyChanged.emit()
        if "candidates" in outcome.data:
            self._game_candidates = list(outcome.data.get("candidates") or [])
            self._game_warning = str(outcome.data.get("warning") or "")
            self.gameScanChanged.emit()
        if outcome.status == "pending":
            self._pending_action = {
                **outcome.data,
                "title": outcome.title,
                "detail": outcome.detail,
            }
            self.pendingActionChanged.emit()
            self._set_state("pending")
            self.commandOutcome.emit(
                {"status": outcome.status, "title": outcome.title, "detail": outcome.detail}
            )
            return
        self._pending_action = {}
        self.pendingActionChanged.emit()
        if outcome.status == "exit":
            self.quitApplication()
            return
        self._set_message(outcome)
        action = str(outcome.data.get("action", ""))
        if action in {"apps", "notes"}:
            self.setPage(action)
        elif action == "help":
            self.helpRequested.emit()
        if outcome.status == "error" or outcome.status == "not_found":
            self._set_state("error", restore=True)
        elif outcome.status == "success":
            self._set_state("success", restore=True)
        else:
            self._set_state("idle")
        self.commandOutcome.emit(
            {"status": outcome.status, "title": outcome.title, "detail": outcome.detail}
        )

    @Slot()
    def startVoiceControl(self) -> None:
        if self._voice_controller is not None:
            return
        from voice_control import LocalVoiceController, VoiceConfig

        controller = LocalVoiceController(
            VoiceConfig.from_environment(self.resource_directory), self
        )
        controller.statusChanged.connect(self._set_voice_status)
        controller.commandRecognized.connect(self.executeVoiceCommand)
        controller.confirmationRequested.connect(self.confirmPending)
        controller.cancellationRequested.connect(self.cancelPending)
        self.commandOutcome.connect(controller.submitOutcome)
        self._voice_controller = controller
        controller.start()

    @Slot(str, str)
    def _set_voice_status(self, status: str, label: str) -> None:
        self._voice_status = status
        self._voice_status_label = label
        self.voiceStatusChanged.emit()
        if status in {"awake", "listening"}:
            self._set_state("listening")
        elif status == "recognizing":
            self._set_state("recognizing")
        elif status == "error":
            self._set_message(CommandOutcome("error", "Голосовое управление недоступно", label))
            self._set_state("error", restore=True)

    def _set_message(self, outcome: CommandOutcome) -> None:
        self._message_token += 1
        token = self._message_token
        self._last_message = {
            "status": outcome.status,
            "title": outcome.title,
            "detail": outcome.detail,
        }
        self.lastMessageChanged.emit()

        def clear_if_current() -> None:
            if self._message_token == token:
                self.dismissMessage()

        QTimer.singleShot(4200, clear_if_current)

    @Slot()
    def dismissMessage(self) -> None:
        if not self._last_message:
            return
        self._message_token += 1
        self._last_message = {}
        self.lastMessageChanged.emit()

    @Slot()
    def confirmPending(self) -> None:
        pending_id = str(self._pending_action.get("pending_id", ""))
        if not pending_id:
            return
        self._run_task(lambda: self.service.confirm(pending_id), self._handle_outcome)

    @Slot()
    def cancelPending(self) -> None:
        pending_id = str(self._pending_action.get("pending_id", ""))
        if not pending_id:
            return
        self._handle_outcome(self.service.cancel(pending_id))

    @Slot(str)
    def removeHistory(self, entry_id: str) -> None:
        if self.service.history.remove(entry_id):
            self.historyChanged.emit()

    @Slot(str)
    def setPage(self, page: str) -> None:
        if page not in {
            "home",
            "apps",
            "game",
            "notes",
            "statistics",
            "customization",
            "settings",
        }:
            return
        if self._current_page != page:
            self._current_page = page
            self.currentPageChanged.emit()
        if page == "statistics":
            self.refreshSystemStats()
            if not self._stats_timer.isActive():
                self._stats_timer.start()
        else:
            self._stats_timer.stop()

    @Slot(str)
    def launchProgram(self, name: str) -> None:
        self.executeCommand(name)

    @Slot(str)
    def launchPreset(self, number: str) -> None:
        if number in assistant.PRESET_COMMANDS:
            self.executeCommand(number)

    @Slot(str)
    def runProtocol(self, protocol_id: str) -> None:
        commands = {
            "game_mode": "/game",
            "vpn": "vpn",
            "claude_code": "claude code",
        }
        command = commands.get(protocol_id)
        if command:
            self.executeCommand(command)

    @Slot()
    def refreshSystemStats(self) -> None:
        if self._stats_refreshing:
            return
        self._stats_refreshing = True
        worker = TaskWorker(collect_system_snapshot)
        self._workers.add(worker)

        def finish(snapshot: dict[str, Any]) -> None:
            self._workers.discard(worker)
            self._stats_refreshing = False
            self._system_stats = dict(snapshot.get("resources") or self._system_stats)
            self._disk_items = list(snapshot.get("disks") or [])
            self._stats_updated_label = "Обновлено только что"
            self.systemStatsChanged.emit()

        def fail(_message: str) -> None:
            self._workers.discard(worker)
            self._stats_refreshing = False
            self._stats_updated_label = "Не удалось обновить"
            self.systemStatsChanged.emit()

        worker.signals.finished.connect(finish)
        worker.signals.failed.connect(fail)
        self.thread_pool.start(worker)

    @Slot()
    def refreshPrograms(self) -> None:
        self._run_task(self.service.refresh_programs, self._programs_refreshed)

    def shutdown_workers(self, timeout_ms: int = -1) -> None:
        """Wait for active QRunnables before Qt tears down their signal objects."""
        self._stats_timer.stop()
        if self._voice_controller is not None:
            self._voice_controller.stop()
        self.thread_pool.waitForDone(timeout_ms)

    def _programs_refreshed(self, outcome: CommandOutcome) -> None:
        self.programsChanged.emit()
        self._handle_outcome(outcome)

    @Slot(str)
    def runKill(self, name: str) -> None:
        value = name.strip()
        if value:
            self.executeCommand(f"kill {value}")

    @Slot()
    def previewGameMode(self) -> None:
        self.executeCommand("/game preview")

    @Slot()
    def activateGameMode(self) -> None:
        self.executeCommand("/game")

    @Slot(str, result=bool)
    def addNote(self, text: str) -> bool:
        try:
            self.notes_store.add(text)
        except OSError as error:
            self._handle_outcome(CommandOutcome("error", "Не удалось сохранить заметку", str(error)))
            return False
        self.notesChanged.emit()
        self._set_message(CommandOutcome("success", "Заметка добавлена"))
        self._set_state("success", restore=True)
        return True

    @Slot(int, str, result=bool)
    def updateNote(self, index: int, text: str) -> bool:
        try:
            self.notes_store.update(index, text)
        except (OSError, ValueError) as error:
            self._handle_outcome(CommandOutcome("error", "Не удалось изменить заметку", str(error)))
            return False
        self.notesChanged.emit()
        self._set_message(CommandOutcome("success", "Заметка изменена"))
        self._set_state("success", restore=True)
        return True

    @Slot(int)
    def removeNote(self, index: int) -> None:
        try:
            self.notes_store.remove(index)
        except (OSError, ValueError) as error:
            self._handle_outcome(CommandOutcome("error", "Не удалось удалить заметку", str(error)))
            return
        self.notesChanged.emit()
        self._set_message(CommandOutcome("success", "Заметка удалена"))

    @Slot(result=bool)
    def clearNotes(self) -> bool:
        try:
            self.notes_store.clear()
        except OSError as error:
            self._handle_outcome(CommandOutcome("error", "Не удалось очистить заметки", str(error)))
            return False
        self.notesChanged.emit()
        self._set_message(CommandOutcome("success", "Заметки очищены"))
        return True

    @Slot(int, int)
    def savePetPosition(self, x: int, y: int) -> None:
        work_areas = get_work_areas()
        position = clamp_position(Point(x, y), WINDOW_SIZE, work_areas) if work_areas else Point(x, y)
        self._pet_position = position
        self.petPositionChanged.emit()
        try:
            save_position(pet_state_path(), position)
        except OSError:
            pass

    @Slot()
    def togglePet(self) -> None:
        self._pet_visible = not self._pet_visible
        self.petVisibleChanged.emit()

    @Slot()
    def showMainWindow(self) -> None:
        if self._main_window is None:
            self.showMainRequested.emit()
            return
        if self._main_window.visibility() == QWindow.Visibility.Minimized:
            self._main_window.showNormal()
        else:
            self._main_window.show()
        self._main_window.raise_()
        self._main_window.requestActivate()

    @Slot()
    def toggleMainWindow(self) -> None:
        if self._main_window is not None and self._main_window.isVisible():
            self._main_window.hide()
        else:
            self.showMainWindow()

    @Slot()
    def quitApplication(self) -> None:
        if self._quitting:
            return
        self._quitting = True
        self.quittingChanged.emit()
        self.quitRequested.emit()
        self.shutdown_workers()
        app = QGuiApplication.instance()
        if app is not None:
            app.quit()
