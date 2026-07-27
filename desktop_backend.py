from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import Property, QObject, QRunnable, QThreadPool, QTimer, Signal, Slot
from PySide6.QtGui import QGuiApplication

import assistant
from command_service import CommandOutcome, CommandService, NotesStore
from desktop_pet import WINDOW_SIZE, Point, clamp_position, default_position, get_work_areas, load_position, pet_state_path, save_position


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
        self._pet_visible = True
        self._quitting = False
        self._reduced_motion = reduced_motion_enabled()

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
        }.get(self._state, "Готов к работе")

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

    def _set_state(self, value: str, *, restore: bool = False) -> None:
        if self._state != value:
            self._state = value
            self.stateChanged.emit()
        if restore and not self._reduced_motion:
            QTimer.singleShot(1800, self._restore_idle)

    def _restore_idle(self) -> None:
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
        if page not in {"home", "apps", "game", "notes"}:
            return
        if self._current_page != page:
            self._current_page = page
            self.currentPageChanged.emit()

    @Slot(str)
    def launchProgram(self, name: str) -> None:
        self.executeCommand(name)

    @Slot()
    def refreshPrograms(self) -> None:
        self._run_task(self.service.refresh_programs, self._programs_refreshed)

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
        app = QGuiApplication.instance()
        if app is not None:
            app.quit()
