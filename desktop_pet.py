from __future__ import annotations

from dataclasses import dataclass
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import random
import sys
import threading
from typing import Callable, Protocol


WINDOW_SIZE = 128
DRAG_THRESHOLD = 5
DEFAULT_MARGIN = 24
TRANSPARENT_COLOR = "#00ff00"
SW_SHOW = 5
SW_RESTORE = 9
MONITORINFOF_PRIMARY = 1
STD_OUTPUT_HANDLE = -11
ENABLE_PROCESSED_OUTPUT = 0x0001
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
UTF8_CODE_PAGE = 65001


@dataclass(frozen=True)
class Point:
    x: int
    y: int


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


def is_drag(start: Point, current: Point, threshold: int = DRAG_THRESHOLD) -> bool:
    delta_x = current.x - start.x
    delta_y = current.y - start.y
    return delta_x * delta_x + delta_y * delta_y >= threshold * threshold


def _clamp_to_rect(position: Point, window_size: int, area: Rect) -> Point:
    max_x = max(area.left, area.right - window_size)
    max_y = max(area.top, area.bottom - window_size)
    return Point(
        min(max(position.x, area.left), max_x),
        min(max(position.y, area.top), max_y),
    )


def clamp_position(
    position: Point,
    window_size: int,
    work_areas: list[Rect],
) -> Point:
    if not work_areas:
        return position

    candidates = [
        _clamp_to_rect(position, window_size, area) for area in work_areas
    ]
    return min(
        candidates,
        key=lambda candidate: (
            (candidate.x - position.x) ** 2 + (candidate.y - position.y) ** 2
        ),
    )


def default_position(
    work_area: Rect,
    window_size: int = WINDOW_SIZE,
    margin: int = DEFAULT_MARGIN,
) -> Point:
    return _clamp_to_rect(
        Point(work_area.right - window_size - margin, work_area.bottom - window_size - margin),
        window_size,
        work_area,
    )


def pet_state_path() -> Path:
    configured_directory = os.environ.get("JARVIS_DATA_DIR")
    if configured_directory:
        return Path(configured_directory) / "pet_state.json"
    return Path(__file__).resolve().parent / "data" / "pet_state.json"


def load_position(path: Path) -> Point | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    x = payload.get("x")
    y = payload.get("y")
    if type(x) is not int or type(y) is not int:
        return None
    return Point(x, y)


def save_position(path: Path, position: Point) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(
            {"version": 1, "x": position.x, "y": position.y},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    temporary_path.replace(path)


def random_delay_ms(
    rng: random.Random,
    minimum_seconds: int,
    maximum_seconds: int,
) -> int:
    return rng.randint(minimum_seconds * 1000, maximum_seconds * 1000)


class ConsoleApi(Protocol):
    def get_console_window(self) -> int: ...

    def alloc_console(self) -> bool: ...

    def set_console_title(self, title: str) -> None: ...

    def is_iconic(self, window: int) -> bool: ...

    def show_window(self, window: int, command: int) -> None: ...

    def set_foreground_window(self, window: int) -> None: ...


class Win32ConsoleApi:
    def __init__(self) -> None:
        self.kernel32 = ctypes.windll.kernel32
        self.user32 = ctypes.windll.user32

    def get_console_window(self) -> int:
        return int(self.kernel32.GetConsoleWindow())

    def alloc_console(self) -> bool:
        return bool(self.kernel32.AllocConsole())

    def set_console_title(self, title: str) -> None:
        self.kernel32.SetConsoleTitleW(title)

    def is_iconic(self, window: int) -> bool:
        return bool(self.user32.IsIconic(window))

    def show_window(self, window: int, command: int) -> None:
        self.user32.ShowWindow(window, command)

    def set_foreground_window(self, window: int) -> None:
        self.user32.SetForegroundWindow(window)


def enable_virtual_terminal_processing(kernel32=None) -> bool:
    api = kernel32 or ctypes.windll.kernel32
    output_handle = api.GetStdHandle(STD_OUTPUT_HANDLE)
    if not output_handle:
        return False

    current_mode = wintypes.DWORD()
    if not api.GetConsoleMode(output_handle, ctypes.byref(current_mode)):
        return False

    requested_mode = (
        current_mode.value
        | ENABLE_PROCESSED_OUTPUT
        | ENABLE_VIRTUAL_TERMINAL_PROCESSING
    )
    if not api.SetConsoleMode(output_handle, requested_mode):
        return False

    api.SetConsoleOutputCP(UTF8_CODE_PAGE)
    api.SetConsoleCP(UTF8_CODE_PAGE)
    return True


def bind_console_streams() -> None:
    sys.stdin = open("CONIN$", "r", encoding="utf-8", errors="replace")
    sys.stdout = open(
        "CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1
    )
    sys.stderr = open(
        "CONOUT$", "w", encoding="utf-8", errors="replace", buffering=1
    )
    enable_virtual_terminal_processing()


class ConsoleWindowController:
    def __init__(
        self,
        session_target: Callable[[], object],
        on_session_exit: Callable[[], None],
        *,
        api: ConsoleApi | None = None,
        stream_binder: Callable[[], None] = bind_console_streams,
        title: str = "JARVIS · Desktop launcher",
    ) -> None:
        self._api = api or Win32ConsoleApi()
        self._session_target = session_target
        self._on_session_exit = on_session_exit
        self._stream_binder = stream_binder
        self._title = title
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    @property
    def session_started(self) -> bool:
        return self._thread is not None

    def open_or_restore(self) -> None:
        with self._lock:
            window = self._api.get_console_window()
            if not window:
                if not self._api.alloc_console():
                    raise OSError("Windows не удалось создать консоль JARVIS")
                self._stream_binder()
                self._api.set_console_title(self._title)
                window = self._api.get_console_window()
                if not window:
                    raise OSError("Windows не вернула дескриптор консоли JARVIS")

            command = SW_RESTORE if self._api.is_iconic(window) else SW_SHOW
            self._api.show_window(window, command)
            self._api.set_foreground_window(window)

            if self._thread is None:
                self._thread = threading.Thread(
                    target=self._run_session,
                    name="jarvis-console",
                    daemon=True,
                )
                self._thread.start()

    def _run_session(self) -> None:
        try:
            self._session_target()
        finally:
            self._on_session_exit()


class _RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class _MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", _RECT),
        ("rcWork", _RECT),
        ("dwFlags", wintypes.DWORD),
    ]


def get_work_areas() -> list[Rect]:
    if os.name != "nt":
        return []

    user32 = ctypes.windll.user32
    entries: list[tuple[bool, Rect]] = []
    callback_type = ctypes.WINFUNCTYPE(
        wintypes.BOOL,
        wintypes.HMONITOR,
        wintypes.HDC,
        ctypes.POINTER(_RECT),
        wintypes.LPARAM,
    )

    @callback_type
    def collect_monitor(monitor, _device_context, _rect, _data):
        info = _MONITORINFO()
        info.cbSize = ctypes.sizeof(_MONITORINFO)
        if user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            work = info.rcWork
            entries.append(
                (
                    bool(info.dwFlags & MONITORINFOF_PRIMARY),
                    Rect(work.left, work.top, work.right, work.bottom),
                )
            )
        return True

    if not user32.EnumDisplayMonitors(None, None, collect_monitor, 0):
        return []
    entries.sort(key=lambda entry: not entry[0])
    return [area for _primary, area in entries]


def enable_dpi_awareness() -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


class DesktopPetApp:
    SPRITE_NAMES = ("idle", "blink", "emotion", "gesture", "laptop", "jump")
    SPECIAL_DURATIONS = {"gesture": 1200, "laptop": 4000, "jump": 1200}

    def __init__(
        self,
        assets_directory: Path,
        session_target: Callable[[], object],
        *,
        state_path: Path | None = None,
        rng: random.Random | None = None,
    ) -> None:
        import tkinter as tk

        enable_dpi_awareness()
        self._tk = tk
        self._rng = rng or random.Random()
        self._state_path = state_path or pet_state_path()
        self._shutdown_requested = threading.Event()
        self._mouse_down = False
        self._dragging = False
        self._busy = False
        self._press_position: Point | None = None
        self._drag_origin: Point | None = None
        self._temporary_job: str | None = None
        self._bob_index = 0

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("JARVIS Pet")
        self.root.overrideredirect(True)
        self.root.configure(background=TRANSPARENT_COLOR)
        self.root.wm_attributes("-topmost", True)
        try:
            self.root.wm_attributes("-transparentcolor", TRANSPARENT_COLOR)
        except tk.TclError:
            pass

        self.canvas = tk.Canvas(
            self.root,
            width=WINDOW_SIZE,
            height=WINDOW_SIZE,
            background=TRANSPARENT_COLOR,
            highlightthickness=0,
            borderwidth=0,
        )
        self.canvas.pack()

        self._images = {}
        for name in self.SPRITE_NAMES:
            path = assets_directory / f"{name}.png"
            if not path.is_file():
                raise FileNotFoundError(f"Не найден спрайт питомца: {path}")
            self._images[name] = tk.PhotoImage(file=str(path))

        self._image_item = self.canvas.create_image(
            WINDOW_SIZE // 2,
            WINDOW_SIZE // 2,
            image=self._images["idle"],
        )

        work_areas = get_work_areas()
        if not work_areas:
            work_areas = [
                Rect(0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight())
            ]
        self._work_areas = work_areas
        stored_position = load_position(self._state_path)
        self.position = clamp_position(
            stored_position or default_position(work_areas[0]),
            WINDOW_SIZE,
            work_areas,
        )
        self._move_window(self.position)

        self.console = ConsoleWindowController(
            session_target,
            self.request_close,
        )

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.root.protocol("WM_DELETE_WINDOW", self.request_close)
        self.root.deiconify()

        self.root.after(180, self._tick_bob)
        self.root.after(random_delay_ms(self._rng, 3, 7), self._blink)
        self.root.after(random_delay_ms(self._rng, 20, 40), self._special_pose)
        self.root.after(100, self._poll_shutdown)

    def run(self) -> int:
        self.root.mainloop()
        return 0

    def request_close(self) -> None:
        self._shutdown_requested.set()

    def _poll_shutdown(self) -> None:
        if self._shutdown_requested.is_set():
            try:
                save_position(self._state_path, self.position)
            except OSError:
                pass
            self.root.destroy()
            return
        self.root.after(100, self._poll_shutdown)

    def _move_window(self, position: Point) -> None:
        self.position = position
        self.root.geometry(
            f"{WINDOW_SIZE}x{WINDOW_SIZE}{position.x:+d}{position.y:+d}"
        )

    def _set_sprite(self, name: str) -> None:
        self.canvas.itemconfigure(self._image_item, image=self._images[name])

    def _cancel_temporary(self) -> None:
        if self._temporary_job is not None:
            try:
                self.root.after_cancel(self._temporary_job)
            except self._tk.TclError:
                pass
        self._temporary_job = None
        self._busy = False

    def _temporary_sprite(self, name: str, duration_ms: int) -> None:
        self._cancel_temporary()
        self._busy = True
        self._set_sprite(name)
        self._temporary_job = self.root.after(duration_ms, self._restore_idle)

    def _restore_idle(self) -> None:
        self._temporary_job = None
        self._busy = False
        self._set_sprite("idle")

    def _tick_bob(self) -> None:
        offsets = (0, -1, -2, -1)
        offset = 0 if self._dragging else offsets[self._bob_index % len(offsets)]
        self._bob_index += 1
        self.canvas.coords(
            self._image_item,
            WINDOW_SIZE // 2,
            WINDOW_SIZE // 2 + offset,
        )
        self.root.after(180, self._tick_bob)

    def _blink(self) -> None:
        if not self._busy and not self._mouse_down:
            self._temporary_sprite("blink", 140)
        self.root.after(random_delay_ms(self._rng, 3, 7), self._blink)

    def _special_pose(self) -> None:
        duration = 0
        if not self._busy and not self._mouse_down:
            name = self._rng.choice(tuple(self.SPECIAL_DURATIONS))
            duration = self.SPECIAL_DURATIONS[name]
            self._temporary_sprite(name, duration)
        self.root.after(
            duration + random_delay_ms(self._rng, 20, 40),
            self._special_pose,
        )

    def _on_press(self, event) -> None:
        self._mouse_down = True
        self._dragging = False
        self._press_position = Point(int(event.x_root), int(event.y_root))
        self._drag_origin = self.position

    def _on_motion(self, event) -> None:
        if self._press_position is None or self._drag_origin is None:
            return
        current = Point(int(event.x_root), int(event.y_root))
        if not self._dragging and is_drag(self._press_position, current):
            self._dragging = True
            self._cancel_temporary()
            self._busy = True
            self._set_sprite("gesture")
        if not self._dragging:
            return

        candidate = Point(
            self._drag_origin.x + current.x - self._press_position.x,
            self._drag_origin.y + current.y - self._press_position.y,
        )
        self._move_window(clamp_position(candidate, WINDOW_SIZE, self._work_areas))

    def _on_release(self, event) -> None:
        was_dragging = self._dragging
        self._mouse_down = False
        self._dragging = False
        self._press_position = None
        self._drag_origin = None

        if was_dragging:
            self._busy = False
            self._set_sprite("idle")
            try:
                save_position(self._state_path, self.position)
            except OSError:
                pass
            return

        self._temporary_sprite("emotion", 500)
        try:
            self.console.open_or_restore()
        except OSError:
            self._restore_idle()
