from __future__ import annotations

import json
import subprocess
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import game_mode


class FakeProcess:
    def __init__(
        self,
        pid: int,
        name: str,
        create_time: float,
        parent: "FakeProcess | None" = None,
    ) -> None:
        self.pid = pid
        self._name = name
        self._create_time = create_time
        self._parent = parent
        self.info = {
            "pid": pid,
            "name": name,
            "create_time": create_time,
        }

    def name(self) -> str:
        return self._name

    def create_time(self) -> float:
        return self._create_time

    def parent(self) -> "FakeProcess | None":
        return self._parent


class GameModeTests(unittest.TestCase):
    def test_comet_is_recognized_as_browser(self) -> None:
        self.assertIn("comet.exe", game_mode.BROWSER_NAMES)

    def test_nvidia_display_service_is_protected(self) -> None:
        self.assertTrue(
            game_mode._is_protected(2608, "NVDisplay.Container.exe", set())
        )

    @patch("game_mode.subprocess.run")
    def test_gpu_counter_failure_is_reported(self, run_mock) -> None:
        run_mock.return_value = SimpleNamespace(
            stdout=json.dumps(
                {
                    "ok": False,
                    "error": "GPU Engine performance counters are unavailable.",
                    "items": [],
                }
            ),
            stderr="",
            returncode=0,
        )

        usage, warning = game_mode.get_gpu_usage_windows()

        self.assertEqual(usage, {})
        self.assertIn("unavailable", warning)

    @patch("game_mode._protected_pids", return_value=set())
    @patch("game_mode.get_gpu_usage_windows")
    @patch("game_mode.psutil.process_iter")
    def test_gpu_child_is_grouped_into_application_root(
        self,
        process_iter_mock,
        gpu_usage_mock,
        _protected_mock,
    ) -> None:
        root = FakeProcess(100, "ChatGPT.exe", 10.0)
        gpu_child = FakeProcess(101, "ChatGPT.exe", 11.0, root)
        process_iter_mock.return_value = [root, gpu_child]
        gpu_usage_mock.return_value = ({101: 7.5}, "")

        scan = game_mode.scan_game_mode(5.0)

        self.assertEqual(len(scan.candidates), 1)
        candidate = scan.candidates[0]
        self.assertEqual(candidate.pid, root.pid)
        self.assertEqual(candidate.create_time, root.create_time())
        self.assertEqual(candidate.gpu_usage, 7.5)

    def test_reused_pid_does_not_match_candidate(self) -> None:
        candidate = game_mode.ProcessCandidate(
            pid=100,
            name="chrome.exe",
            create_time=10.0,
            gpu_usage=0.0,
            reason="браузер",
        )
        replacement = FakeProcess(100, "notepad.exe", 20.0)

        self.assertFalse(game_mode._matches_candidate(replacement, candidate))

    def test_termination_closes_owned_process_tree(self) -> None:
        parent = subprocess.Popen(
            [
                sys.executable,
                "-c",
                (
                    "import subprocess,sys,time; "
                    "subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
                    "time.sleep(60)"
                ),
            ],
            creationflags=game_mode._powershell_flags(),
        )
        root = game_mode.psutil.Process(parent.pid)
        children: list[game_mode.psutil.Process] = []
        try:
            for _attempt in range(50):
                children = root.children()
                if children:
                    break
                time.sleep(0.02)
            self.assertTrue(children, "Тестовый дочерний процесс не запустился")
            candidate = game_mode.ProcessCandidate(
                pid=root.pid,
                name=root.name(),
                create_time=root.create_time(),
                gpu_usage=10.0,
                reason="GPU 10.0%",
            )

            result = game_mode.terminate_processes(
                [candidate],
                graceful_timeout=0.05,
                force_timeout=1.0,
            )

            self.assertEqual(result.failed, [])
            self.assertEqual([item.pid for item in result.closed], [root.pid])
            self.assertFalse(root.is_running())
            self.assertTrue(all(not child.is_running() for child in children))
        finally:
            for process in [*children, root]:
                try:
                    process.kill()
                except game_mode.psutil.Error:
                    pass
            try:
                parent.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                parent.kill()
                parent.wait(timeout=1.0)


if __name__ == "__main__":
    unittest.main()
