from __future__ import annotations

from dataclasses import dataclass
import argparse
import ctypes
import json
import math
import os
import subprocess
import sys

import psutil


DEFAULT_GPU_THRESHOLD = 5.0

BROWSER_NAMES = {
    "arc.exe",
    "brave.exe",
    "browser.exe",
    "chrome.exe",
    "chromium.exe",
    "comet.exe",
    "firefox.exe",
    "floorp.exe",
    "iexplore.exe",
    "librewolf.exe",
    "msedge.exe",
    "opera.exe",
    "opera_gx.exe",
    "vivaldi.exe",
    "waterfox.exe",
    "yandex.exe",
    "yandex_browser.exe",
    "zen.exe",
}

# These Windows processes either are critical or are part of the desktop shell.
# Closing them can log the user out, blank the desktop, or destabilize Windows.
PROTECTED_PROCESS_NAMES = {
    "applicationframehost.exe",
    "audiodg.exe",
    "csrss.exe",
    "ctfmon.exe",
    "dwm.exe",
    "explorer.exe",
    "fontdrvhost.exe",
    "idle.exe",
    "lsass.exe",
    "memory compression",
    "msmpeng.exe",
    "nvcontainer.exe",
    "nvdisplay.container.exe",
    "registry",
    "runtimebroker.exe",
    "searchhost.exe",
    "securityhealthservice.exe",
    "services.exe",
    "shellhost.exe",
    "shellexperiencehost.exe",
    "sihost.exe",
    "smss.exe",
    "spoolsv.exe",
    "startmenuexperiencehost.exe",
    "system",
    "system idle process",
    "systemsettings.exe",
    "taskhostw.exe",
    "textinputhost.exe",
    "wininit.exe",
    "winlogon.exe",
}

# Game and launcher processes must remain available while Game Mode starts.
GAME_PROCESS_PATTERNS = (
    "brokenarrow",
    "easyanticheat",
    "epicgameslauncher",
    "fortniteclient",
    "steam.exe",
    "steamservice.exe",
)


@dataclass(frozen=True)
class ProcessCandidate:
    pid: int
    name: str
    create_time: float
    gpu_usage: float
    reason: str


@dataclass(frozen=True)
class GameModeScan:
    candidates: list[ProcessCandidate]
    gpu_monitor_available: bool
    warning: str = ""


@dataclass(frozen=True)
class GameModeResult:
    closed: list[ProcessCandidate]
    failed: list[tuple[ProcessCandidate, str]]


def _powershell_flags() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def get_gpu_usage_windows(sample_interval: float = 1.0) -> tuple[dict[int, float], str]:
    """Return summed Windows GPU-engine utilization for every process.

    NVIDIA's compute-app query misses browsers and DirectX applications under
    WDDM. Windows performance counters include 3D, video decode/encode and copy
    engines, which makes them a better source for a desktop game mode.
    """
    interval = max(1, round(sample_interval))
    script = rf"""
$ErrorActionPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$sets = Get-Counter '\GPU Engine(*)\Utilization Percentage' -SampleInterval {interval} -MaxSamples 2
$response = [ordered]@{{ ok = $false; error = ''; items = @() }}
if ($sets) {{
    $last = @($sets)[-1].CounterSamples
    $valid = @($last | Where-Object {{ $_.Status -eq 0 -and $_.Path -match 'pid_(\d+)' }})
    if ($valid.Count -gt 0) {{
        $response.ok = $true
        $response.items = @($valid |
            Group-Object {{ [regex]::Match($_.Path, 'pid_(\d+)').Groups[1].Value }} |
            ForEach-Object {{
                [pscustomobject]@{{
                    pid = [int]$_.Name
                    utilization = [math]::Round((($_.Group | Measure-Object CookedValue -Sum).Sum), 1)
                }}
            }})
    }} else {{
        $response.error = 'Windows returned no valid GPU counter samples.'
    }}
}} else {{
    $response.error = 'GPU Engine performance counters are unavailable.'
}}
$response | ConvertTo-Json -Compress -Depth 4
"""
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoLogo",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=12,
            creationflags=_powershell_flags(),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {}, f"Счётчик GPU недоступен: {error}"

    output = result.stdout.strip()
    if not output:
        detail = result.stderr.strip() or "Windows не вернула данные счётчика GPU."
        return {}, detail

    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return {}, "Windows вернула данные GPU в неизвестном формате."

    if not isinstance(payload, dict) or "ok" not in payload:
        return {}, "Windows вернула неполный результат измерения GPU."
    if not payload.get("ok"):
        detail = str(payload.get("error") or "Счётчики GPU недоступны.")
        return {}, detail

    raw_data = payload.get("items", [])
    if isinstance(raw_data, dict):
        raw_data = [raw_data]
    if not isinstance(raw_data, list):
        return {}, "Windows вернула неполный список процессов GPU."

    usage: dict[int, float] = {}
    for item in raw_data:
        try:
            pid = int(item["pid"])
            value = max(0.0, float(item["utilization"]))
        except (KeyError, TypeError, ValueError):
            continue
        usage[pid] = value
    return usage, ""


def _protected_pids() -> set[int]:
    protected = {0, 4, os.getpid()}
    try:
        process = psutil.Process()
        while process:
            protected.add(process.pid)
            process = process.parent()
    except (psutil.Error, OSError):
        pass
    return protected


def _is_protected(pid: int, name: str, protected_pids: set[int]) -> bool:
    lowered = name.casefold()
    return (
        pid in protected_pids
        or lowered in PROTECTED_PROCESS_NAMES
        or any(pattern in lowered for pattern in GAME_PROCESS_PATTERNS)
    )


def _find_application_root(
    process: psutil.Process,
    protected_pids: set[int],
) -> psutil.Process:
    """Walk to the oldest same-executable parent of a multi-process app."""
    current = process
    try:
        current_name = current.name().casefold()
        while True:
            parent = current.parent()
            if parent is None:
                break
            parent_name = parent.name()
            if _is_protected(parent.pid, parent_name, protected_pids):
                break
            if parent_name.casefold() != current_name:
                break
            current = parent
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error):
        pass
    return current


def scan_game_mode(gpu_threshold: float = DEFAULT_GPU_THRESHOLD) -> GameModeScan:
    """Find whole applications that are browsers or significantly use the GPU."""
    gpu_usage, warning = get_gpu_usage_windows()
    protected_pids = _protected_pids()
    groups: dict[tuple[int, float], dict[str, object]] = {}

    for process in psutil.process_iter(["pid", "name", "create_time"]):
        try:
            pid = int(process.info["pid"])
            name = str(process.info["name"] or f"PID {pid}")
        except (psutil.Error, TypeError, ValueError):
            continue

        if _is_protected(pid, name, protected_pids):
            continue

        root = _find_application_root(process, protected_pids)
        try:
            root_pid = root.pid
            root_name = root.name()
            root_create_time = root.create_time()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error):
            continue

        if _is_protected(root_pid, root_name, protected_pids):
            continue

        key = (root_pid, root_create_time)
        group = groups.setdefault(
            key,
            {
                "pid": root_pid,
                "name": root_name,
                "create_time": root_create_time,
                "gpu_usage": 0.0,
                "is_browser": False,
            },
        )
        group["gpu_usage"] = float(group["gpu_usage"]) + gpu_usage.get(pid, 0.0)
        group["is_browser"] = bool(group["is_browser"]) or (
            name.casefold() in BROWSER_NAMES
            or root_name.casefold() in BROWSER_NAMES
        )

    candidates: list[ProcessCandidate] = []
    for group in groups.values():
        usage = float(group["gpu_usage"])
        is_browser = bool(group["is_browser"])
        if not is_browser and usage < gpu_threshold:
            continue
        reasons = []
        if is_browser:
            reasons.append("браузер")
        if usage >= gpu_threshold:
            reasons.append(f"GPU {usage:.1f}%")
        candidates.append(
            ProcessCandidate(
                pid=int(group["pid"]),
                name=str(group["name"]),
                create_time=float(group["create_time"]),
                gpu_usage=usage,
                reason=" · ".join(reasons),
            )
        )

    candidates.sort(
        key=lambda item: (
            item.name.casefold() not in BROWSER_NAMES,
            -item.gpu_usage,
            item.name.casefold(),
            item.pid,
        )
    )
    return GameModeScan(
        candidates=candidates,
        gpu_monitor_available=not warning,
        warning=warning,
    )


def _request_window_close(processes: list[psutil.Process]) -> None:
    if os.name != "nt" or not processes:
        return

    process_by_pid = {process.pid: process for process in processes}
    user32 = ctypes.windll.user32
    wm_close = 0x0010
    enum_callback = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        ctypes.c_void_p,
        ctypes.c_void_p,
    )

    @enum_callback
    def close_window(window: int, _parameter: int) -> bool:
        window_pid = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(window, ctypes.byref(window_pid))
        process = process_by_pid.get(window_pid.value)
        if process is not None and _is_process_running(process) and user32.IsWindowVisible(window):
            user32.PostMessageW(window, wm_close, 0, 0)
        return True

    user32.EnumWindows(close_window, 0)


def _is_process_running(process: psutil.Process) -> bool:
    try:
        return process.is_running()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error):
        return False


def _matches_candidate(process: psutil.Process, candidate: ProcessCandidate) -> bool:
    try:
        return (
            process.name().casefold() == candidate.name.casefold()
            and math.isclose(
                process.create_time(),
                candidate.create_time,
                rel_tol=0.0,
                abs_tol=0.01,
            )
        )
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error):
        return False


def terminate_processes(
    candidates: list[ProcessCandidate],
    graceful_timeout: float = 4.0,
    force_timeout: float = 2.0,
) -> GameModeResult:
    """Validate app roots, then close each root and its complete process tree."""
    closed: list[ProcessCandidate] = []
    failed_by_pid: dict[int, list[str]] = {}
    precheck_failed_pids: set[int] = set()
    members_by_candidate: dict[int, list[psutil.Process]] = {}
    owner_by_identity: dict[tuple[int, float], ProcessCandidate] = {}
    process_by_identity: dict[tuple[int, float], psutil.Process] = {}

    for candidate in candidates:
        try:
            root = psutil.Process(candidate.pid)
        except psutil.NoSuchProcess:
            closed.append(candidate)
            continue
        except (psutil.AccessDenied, psutil.Error) as error:
            failed_by_pid.setdefault(candidate.pid, []).append(str(error))
            precheck_failed_pids.add(candidate.pid)
            continue

        if not _matches_candidate(root, candidate):
            failed_by_pid.setdefault(candidate.pid, []).append(
                "PID уже принадлежит другому процессу; закрытие пропущено."
            )
            precheck_failed_pids.add(candidate.pid)
            continue

        try:
            members = root.children(recursive=True) + [root]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error):
            members = [root]
        members_by_candidate[candidate.pid] = members
        for process in members:
            try:
                identity = (process.pid, process.create_time())
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error):
                continue
            process_by_identity[identity] = process
            owner_by_identity[identity] = candidate

    all_processes = list(process_by_identity.values())
    _request_window_close(all_processes)
    _gone, alive = psutil.wait_procs(all_processes, timeout=graceful_timeout)

    terminating: list[psutil.Process] = []
    for process in alive:
        try:
            identity = (process.pid, process.create_time())
            candidate = owner_by_identity[identity]
        except (KeyError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error):
            continue
        try:
            process.terminate()
            terminating.append(process)
        except psutil.NoSuchProcess:
            pass
        except (psutil.AccessDenied, psutil.Error) as error:
            failed_by_pid.setdefault(candidate.pid, []).append(str(error))

    _gone, alive = psutil.wait_procs(terminating, timeout=force_timeout)

    for process in alive:
        try:
            identity = (process.pid, process.create_time())
            candidate = owner_by_identity[identity]
        except (KeyError, psutil.NoSuchProcess, psutil.AccessDenied, psutil.Error):
            continue
        try:
            process.kill()
            process.wait(timeout=force_timeout)
        except psutil.NoSuchProcess:
            pass
        except (psutil.AccessDenied, psutil.TimeoutExpired, psutil.Error) as error:
            failed_by_pid.setdefault(candidate.pid, []).append(str(error))

    initially_closed = {candidate.pid for candidate in closed}
    for candidate in candidates:
        if candidate.pid in initially_closed or candidate.pid in precheck_failed_pids:
            continue
        members = members_by_candidate.get(candidate.pid, [])
        if any(_is_process_running(process) for process in members):
            failed_by_pid.setdefault(candidate.pid, []).append(
                "Часть процессов приложения осталась запущена."
            )
        else:
            failed_by_pid.pop(candidate.pid, None)
            closed.append(candidate)

    unique_closed = {candidate.pid: candidate for candidate in closed}
    candidate_by_pid = {candidate.pid: candidate for candidate in candidates}
    return GameModeResult(
        closed=[unique_closed[pid] for pid in sorted(unique_closed)],
        failed=[
            (candidate_by_pid[pid], "; ".join(dict.fromkeys(errors)))
            for pid, errors in failed_by_pid.items()
        ],
    )


def activate_game_mode(
    scan: GameModeScan | None = None,
    gpu_threshold: float = DEFAULT_GPU_THRESHOLD,
) -> GameModeResult:
    current_scan = scan or scan_game_mode(gpu_threshold)
    return terminate_processes(current_scan.candidates)


def _print_scan(scan: GameModeScan) -> None:
    if scan.warning:
        print(f"Предупреждение: {scan.warning}")
    if not scan.candidates:
        print("Процессов для закрытия не найдено.")
        return
    print("Будут закрыты:")
    for candidate in scan.candidates:
        print(f"- {candidate.name} (PID {candidate.pid}) — {candidate.reason}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="JARVIS Game Mode")
    parser.add_argument("--yes", action="store_true", help="закрыть без подтверждения")
    parser.add_argument("--preview", action="store_true", help="только показать процессы")
    parser.add_argument("--threshold", type=float, default=DEFAULT_GPU_THRESHOLD)
    args = parser.parse_args()

    scan = scan_game_mode(max(0.1, args.threshold))
    _print_scan(scan)
    if args.preview or not scan.candidates:
        return 0

    if not args.yes:
        try:
            answer = input("Закрыть эти процессы? [д/Н]: ").strip().casefold()
        except (EOFError, KeyboardInterrupt):
            print("\nОтменено.")
            return 0
        if answer not in {"д", "да", "y", "yes"}:
            print("Отменено.")
            return 0

    result = activate_game_mode(scan)
    print(f"Закрыто процессов: {len(result.closed)}")
    for candidate, error in result.failed:
        print(f"Не удалось закрыть {candidate.name} (PID {candidate.pid}): {error}")
    return 1 if result.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
