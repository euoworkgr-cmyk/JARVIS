from __future__ import annotations

from pathlib import Path
import random
import tempfile
import threading
import unittest

from desktop_pet import (
    ConsoleWindowController,
    Point,
    Rect,
    SW_RESTORE,
    SW_SHOW,
    clamp_position,
    default_position,
    enable_virtual_terminal_processing,
    is_drag,
    load_position,
    random_delay_ms,
    save_position,
)


class PositionTests(unittest.TestCase):
    def test_five_pixels_is_a_drag(self) -> None:
        start = Point(10, 10)

        self.assertFalse(is_drag(start, Point(13, 13)))
        self.assertTrue(is_drag(start, Point(13, 14)))

    def test_position_is_clamped_to_nearest_monitor(self) -> None:
        monitors = [
            Rect(-1920, 0, 0, 1040),
            Rect(0, 0, 1920, 1040),
        ]

        self.assertEqual(
            clamp_position(Point(-2200, 1200), 128, monitors),
            Point(-1920, 912),
        )
        self.assertEqual(
            clamp_position(Point(500, 400), 128, monitors),
            Point(500, 400),
        )

    def test_default_position_uses_bottom_right_margin(self) -> None:
        self.assertEqual(
            default_position(Rect(0, 0, 1920, 1040)),
            Point(1768, 888),
        )

    def test_position_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "JARVIS" / "pet_state.json"

            save_position(path, Point(-1200, 450))

            self.assertEqual(load_position(path), Point(-1200, 450))

    def test_invalid_position_file_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "pet_state.json"
            path.write_text('{"x": true, "y": "wrong"}', encoding="utf-8")

            self.assertIsNone(load_position(path))

    def test_animation_delay_stays_in_requested_range(self) -> None:
        rng = random.Random(7)
        delays = [random_delay_ms(rng, 20, 40) for _ in range(30)]

        self.assertGreaterEqual(min(delays), 20_000)
        self.assertLessEqual(max(delays), 40_000)


class FakeConsoleApi:
    def __init__(self, window: int = 0, iconic: bool = False) -> None:
        self.window = window
        self.iconic = iconic
        self.allocations = 0
        self.titles: list[str] = []
        self.show_commands: list[int] = []
        self.foreground_windows: list[int] = []

    def get_console_window(self) -> int:
        return self.window

    def alloc_console(self) -> bool:
        self.allocations += 1
        self.window = 101
        return True

    def set_console_title(self, title: str) -> None:
        self.titles.append(title)

    def is_iconic(self, window: int) -> bool:
        return self.iconic

    def show_window(self, window: int, command: int) -> None:
        self.show_commands.append(command)

    def set_foreground_window(self, window: int) -> None:
        self.foreground_windows.append(window)


class FakeKernel32:
    def __init__(self, mode: int) -> None:
        self.mode = mode
        self.requested_modes: list[int] = []
        self.output_code_pages: list[int] = []
        self.input_code_pages: list[int] = []

    def GetStdHandle(self, _stream: int) -> int:
        return 404

    def GetConsoleMode(self, _handle: int, mode_pointer) -> bool:
        mode_pointer._obj.value = self.mode
        return True

    def SetConsoleMode(self, _handle: int, mode: int) -> bool:
        self.requested_modes.append(mode)
        return True

    def SetConsoleOutputCP(self, code_page: int) -> bool:
        self.output_code_pages.append(code_page)
        return True

    def SetConsoleCP(self, code_page: int) -> bool:
        self.input_code_pages.append(code_page)
        return True


class ConsoleWindowControllerTests(unittest.TestCase):
    def test_new_console_enables_ansi_and_utf8(self) -> None:
        kernel32 = FakeKernel32(mode=0x0002)

        enabled = enable_virtual_terminal_processing(kernel32)

        self.assertTrue(enabled)
        self.assertEqual(kernel32.requested_modes, [0x0007])
        self.assertEqual(kernel32.output_code_pages, [65001])
        self.assertEqual(kernel32.input_code_pages, [65001])

    def test_first_click_allocates_console_and_starts_session_once(self) -> None:
        api = FakeConsoleApi()
        stream_bindings: list[bool] = []
        session_started = threading.Event()
        session_release = threading.Event()

        def session() -> None:
            session_started.set()
            session_release.wait(1)

        controller = ConsoleWindowController(
            session,
            lambda: None,
            api=api,
            stream_binder=lambda: stream_bindings.append(True),
        )

        controller.open_or_restore()
        controller.open_or_restore()

        self.assertTrue(session_started.wait(1))
        self.assertEqual(api.allocations, 1)
        self.assertEqual(stream_bindings, [True])
        self.assertEqual(api.show_commands, [SW_SHOW, SW_SHOW])
        self.assertEqual(api.foreground_windows, [101, 101])
        self.assertTrue(controller.session_started)
        session_release.set()

    def test_minimized_console_is_restored(self) -> None:
        api = FakeConsoleApi(window=202, iconic=True)
        session_release = threading.Event()
        controller = ConsoleWindowController(
            lambda: session_release.wait(1),
            lambda: None,
            api=api,
            stream_binder=lambda: None,
        )

        controller.open_or_restore()

        self.assertEqual(api.allocations, 0)
        self.assertEqual(api.show_commands, [SW_RESTORE])
        self.assertEqual(api.foreground_windows, [202])
        session_release.set()

    def test_session_exit_notifies_pet(self) -> None:
        api = FakeConsoleApi(window=303)
        exit_notified = threading.Event()
        controller = ConsoleWindowController(
            lambda: None,
            exit_notified.set,
            api=api,
            stream_binder=lambda: None,
        )

        controller.open_or_restore()

        self.assertTrue(exit_notified.wait(1))


if __name__ == "__main__":
    unittest.main()
