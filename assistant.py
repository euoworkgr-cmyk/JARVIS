from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Literal
import warnings

warnings.filterwarnings(
    "ignore",
    message="Using slow pure-python SequenceMatcher.*",
    module="fuzzywuzzy.fuzz",
)
from fuzzywuzzy import fuzz, process
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from game_mode import (
    GameModeResult,
    GameModeScan,
    activate_game_mode,
    scan_game_mode,
    scan_named_processes,
)


APP_NAME = "JARVIS"
APP_VERSION = "3.0"


def user_desktop_directory() -> Path:
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        return Path(user_profile) / "Desktop"
    return Path.home() / "Desktop"


def resolve_claude_code_launcher(desktop: Path | None = None) -> Path:
    root = desktop or user_desktop_directory()
    candidates = (
        root / "Claude code.lnk",
        root / "Claude code.bat",
        root / "Claude code.cmd",
    )
    return next((candidate for candidate in candidates if candidate.is_file()), candidates[0])


VPN_EXECUTABLE = Path(
    r"C:\Users\Евгений\Documents\02_Код и проекты\VPN\HappTerminalVPN_CodexPowered\HappTerminalVPN_CodexPowered.exe"
)
CLAUDE_CODE_LAUNCHER = resolve_claude_code_launcher()
YANDEX_BROWSER_EXECUTABLE = Path(
    r"C:\Program Files\Yandex\YandexBrowser\Application\browser.exe"
)
SPECIAL_LAUNCH_COMMANDS = {
    "vpn": ("VPN", VPN_EXECUTABLE, True),
    "claude code": ("Claude Code", CLAUDE_CODE_LAUNCHER, False),
}
PRESET_COMMANDS = {
    "1": ("Новое окно Яндекс Браузера", None),
    "2": ("ChatGPT", "chatgpt"),
    "3": ("VS Code", "visual studio code"),
    "4": ("Telegram", "telegram"),
    "5": ("Камера", "камера"),
}
PRESET_LIST_COMMANDS = {"пресеты", "presets", "/presets"}
NOTES_COMMANDS = {"заметки", "notes", "/notes"}
KILL_PROCESS_ALIASES = {
    "vs code": "code",
    "вс код": "code",
    "яндекс": "browser",
    "яндекс браузер": "browser",
    "яндекс музыка": "яндекс музыка",
    "яндекс музыку": "яндекс музыка",
    "яндекс.музыка": "яндекс музыка",
    "телеграмм": "telegram",
}

THEME = Theme(
    {
        "jarvis.accent": "bold #D97757",
        "jarvis.text": "#E8E3DC",
        "jarvis.heading": "bold #E8E3DC",
        "jarvis.muted": "#8C8882",
        "jarvis.border": "#514B46",
        "jarvis.success": "bold #A6C26F",
        "jarvis.error": "bold #E06C75",
        "jarvis.prompt": "bold #F0EAE2",
    }
)

console = Console(theme=THEME, highlight=False)


def reset_console() -> None:
    global console
    console = Console(theme=THEME, highlight=False)


# Common spoken/transliterated names that do not fuzzy-match their Start menu names.
TRANSLIT_MAP = {
    "вс код": "vs code",
    "хром": "chrome",
    "телеграм": "telegram",
    "дискорд": "discord",
    "ворд": "word",
    "эксель": "excel",
    "пауэрпоинт": "powerpoint",
    "блокнот": "notepad",
    "калькулятор": "calculator",
    "проводник": "explorer",
    "настройки": "settings",
    "почта": "mail",
    "карты": "maps",
    "фотографии": "photos",
    "музыка": "music",
    "видео": "movies & tv",
    "магазин": "store",
    "параметры": "settings",
    "календарь": "calendar",
    "погода": "weather",
    "новости": "news",
    "заметки": "sticky notes",
    "рисование": "paint",
    "камера": "camera",
    "запись голоса": "voice recorder",
    "ножницы": "snipping tool",
    "центр отзывов": "feedback hub",
    "часы": "alarms & clock",
    "экранная клавиатура": "on-screen keyboard",
    "экранная лупа": "magnifier",
    "экранный диктор": "narrator",
    "яндекс музыка": "яндекс.музыка",
}

EXIT_COMMANDS = {"/exit", "/quit", "выход", "выйти", "exit", "quit"}
GAME_MODE_COMMANDS = {
    "/game",
    "game mode",
    "игровой режим",
    "протокол игры",
    "включи игровой режим",
    "запусти игровой режим",
}
GAME_MODE_PREVIEW_COMMANDS = {
    "/game preview",
    "проверь игровой режим",
    "что закроет игровой режим",
}


@dataclass(frozen=True)
class LaunchResult:
    kind: Literal["success", "error", "not_found"]
    title: str
    detail: str = ""


@dataclass(frozen=True)
class PowerCommand:
    action: Literal["shutdown", "restart", "sleep", "abort"]
    delay_seconds: int = 0


def resource_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def user_data_directory() -> Path:
    configured_directory = os.environ.get("JARVIS_DATA_DIR")
    if configured_directory:
        return Path(configured_directory)
    return resource_directory() / "data"


def program_index_path() -> Path:
    return user_data_directory() / "programs.json"


def current_jarvis_executable() -> Path | None:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    source_build = resource_directory() / "dist" / "assistant.exe"
    return source_build.resolve() if source_build.is_file() else None


def with_current_jarvis_target(program_map: dict[str, str]) -> dict[str, str]:
    result = dict(program_map)
    if "jarvis" not in result:
        return result
    executable = current_jarvis_executable()
    if executable is not None:
        result["jarvis"] = str(executable)
    return result


def notes_file_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "notes.json"
    return Path(__file__).resolve().parent / "notes.json"


def load_notes(path: Path | None = None) -> list[str]:
    notes_path = path or notes_file_path()
    if not notes_path.exists():
        return []
    try:
        data = json.loads(notes_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(data, list):
        return []
    return [str(note) for note in data if isinstance(note, str) and note.strip()]


def save_notes(notes: list[str], path: Path | None = None) -> None:
    notes_path = path or notes_file_path()
    notes_path.write_text(
        json.dumps(notes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_program_map() -> dict[str, str]:
    paths = [program_index_path(), resource_directory() / "programs.json"]
    for json_path in paths:
        if not json_path.exists():
            continue
        try:
            with json_path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            return with_current_jarvis_target({
                str(name).lower(): str(app_id)
                for name, app_id in data.items()
                if name and app_id
            })
    return {}


def generate_program_map() -> tuple[dict[str, str], str | None]:
    try:
        from get_programs import get_installed_programs

        program_map = with_current_jarvis_target(get_installed_programs())
    except (ImportError, OSError, subprocess.SubprocessError) as error:
        return {}, f"Не удалось обновить список: {error}"
    if not program_map:
        return {}, "Windows не вернула установленные приложения."
    path = program_index_path()
    temporary = path.with_suffix(".json.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(
            json.dumps(program_map, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)
    except OSError as error:
        return {}, f"Не удалось сохранить список: {error}"
    return program_map, None


def normalize_program_name(program_name: str) -> str:
    normalized = " ".join(program_name.lower().split())
    return TRANSLIT_MAP.get(normalized, normalized)


def find_program(
    program_name: str, program_map: dict[str, str]
) -> tuple[str | None, int]:
    if not program_map:
        return None, 0

    exact_name = " ".join(program_name.casefold().split())
    if exact_name in program_map:
        return exact_name, 100

    normalized = normalize_program_name(program_name)
    if normalized in program_map:
        return normalized, 100

    match = process.extractOne(
        normalized,
        program_map.keys(),
        scorer=fuzz.token_set_ratio,
    )
    if not match:
        return None, 0

    best_name, best_score = match
    if best_score < 80:
        for name in program_map:
            if normalized in name:
                score = fuzz.partial_ratio(normalized, name)
                if score > best_score:
                    best_name, best_score = name, score

    if best_score < 70:
        return None, best_score
    return best_name, best_score


def launch_target(app_id: str) -> None:
    expanded = os.path.expandvars(app_id)
    is_existing_file = os.path.isabs(expanded) and os.path.exists(expanded)
    is_uri = bool(re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", app_id))

    if is_existing_file and Path(expanded).suffix.casefold() in {".lnk", ".bat", ".cmd"}:
        os.startfile(expanded)
    elif is_existing_file:
        subprocess.Popen([expanded])
    elif is_uri:
        os.startfile(app_id)
    else:
        subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{app_id}"])


def launch_console_target(path: Path) -> None:
    """Start a console app with input isolated from the JARVIS console."""
    creation_flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    subprocess.Popen(
        [str(path)],
        cwd=str(path.parent),
        creationflags=creation_flags,
        close_fds=True,
    )


def open_special_command(command: str) -> LaunchResult:
    target = SPECIAL_LAUNCH_COMMANDS.get(command.casefold())
    if target is None:
        return LaunchResult("not_found", f"Неизвестная команда «{command}»")

    title, path, new_console = target
    if not path.is_file():
        return LaunchResult(
            "error",
            f"Не нашёл {title}",
            str(path),
        )

    try:
        if new_console:
            launch_console_target(path)
        else:
            launch_target(str(path))
    except (OSError, subprocess.SubprocessError) as error:
        return LaunchResult("error", f"Не удалось открыть {title}", str(error))
    return LaunchResult("success", f"Открываю {title}", str(path))


def open_preset(number: str, program_map: dict[str, str]) -> LaunchResult:
    preset = PRESET_COMMANDS.get(number)
    if preset is None:
        return LaunchResult("not_found", f"Неизвестный пресет №{number}")

    title, program_name = preset
    if number == "1":
        if not YANDEX_BROWSER_EXECUTABLE.is_file():
            return LaunchResult(
                "error",
                "Не нашёл Яндекс Браузер",
                str(YANDEX_BROWSER_EXECUTABLE),
            )
        try:
            subprocess.Popen(
                [str(YANDEX_BROWSER_EXECUTABLE), "--new-window"],
                cwd=str(YANDEX_BROWSER_EXECUTABLE.parent),
            )
        except (OSError, subprocess.SubprocessError) as error:
            return LaunchResult("error", f"Не удалось открыть {title}", str(error))
        return LaunchResult("success", f"Открываю: {title}")

    return open_program(str(program_name), program_map)


def open_program(program_name: str, program_map: dict[str, str]) -> LaunchResult:
    best_name, score = find_program(program_name, program_map)
    if best_name is None:
        return LaunchResult(
            "not_found",
            f"Не нашёл «{program_name}»",
            "Попробуйте название из меню «Пуск» или более короткий вариант.",
        )

    app_id = program_map.get(best_name)
    if not app_id:
        return LaunchResult(
            "error",
            f"У «{best_name}» нет команды запуска",
            "Обновите programs.json и попробуйте снова.",
        )

    try:
        launch_target(app_id)
    except (OSError, subprocess.SubprocessError) as error:
        return LaunchResult(
            "error",
            f"Не удалось открыть {best_name}",
            str(error),
        )

    return LaunchResult(
        "success",
        f"Открываю {best_name}",
        f"Совпадение {score}% · команда выполнена",
    )


def extract_program_name(command: str) -> str:
    value = " ".join(command.strip().split())
    lowered = value.lower()
    for prefix in ("открой", "запусти", "open", "run"):
        if lowered == prefix:
            return ""
        marker = f"{prefix} "
        if lowered.startswith(marker):
            return value[len(marker) :].strip()
    return value


def extract_kill_target(command: str) -> str | None:
    value = " ".join(command.strip().split())
    lowered = value.casefold()
    for prefix in (
        "kill",
        "закрой",
        "закрыть",
        "заверши",
        "завершить",
        "останови",
        "close",
        "terminate",
    ):
        if lowered == prefix:
            return ""
        marker = f"{prefix} "
        if lowered.startswith(marker):
            return value[len(marker) :].strip()
    return None


def extract_power_command(command: str) -> PowerCommand | None:
    value = " ".join(command.strip().casefold().split())
    shutdown_match = re.fullmatch(r"выключить пк(?:\s*\(\s*(\d+)\s*\))?", value)
    if shutdown_match:
        minutes = int(shutdown_match.group(1) or 0)
        return PowerCommand("shutdown", minutes * 60)
    if value.startswith("выключить пк"):
        raise ValueError("Укажите время целым числом минут: выключить пк(30)")
    if value in {"перезагрузка", "перезагрузить пк", "перезагрузить компьютер"}:
        return PowerCommand("restart")
    if value in {"спящий режим", "сон", "усыпить пк", "усыпить компьютер"}:
        return PowerCommand("sleep")
    if value in {"отменить выключение", "отмена выключения"}:
        return PowerCommand("abort")
    return None


def execute_power_command(command: PowerCommand) -> LaunchResult:
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    if command.action == "shutdown":
        args = ["shutdown.exe", "-s", "-t", str(command.delay_seconds)]
        if command.delay_seconds:
            title = f"Выключение запланировано через {command.delay_seconds // 60} мин."
        else:
            title = "Выключаю компьютер"
    elif command.action == "restart":
        args = ["shutdown.exe", "-r", "-t", "0"]
        title = "Перезагружаю компьютер"
    elif command.action == "abort":
        args = ["shutdown.exe", "-a"]
        title = "Запланированное выключение отменено"
    else:
        args = ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"]
        title = "Перевожу компьютер в спящий режим"
    try:
        subprocess.Popen(args, creationflags=creation_flags)
    except (OSError, subprocess.SubprocessError) as error:
        return LaunchResult("error", "Не удалось выполнить команду питания", str(error))
    return LaunchResult("success", title)


def normalize_kill_target(target: str) -> str:
    normalized = normalize_program_name(target)
    return KILL_PROCESS_ALIASES.get(normalized, normalized)


class JarvisUI:
    def __init__(self, program_count: int) -> None:
        self.program_count = program_count

    def render_welcome(self) -> None:
        console.clear()
        brand = Text()
        brand.append("✦  ", style="jarvis.accent")
        brand.append(APP_NAME, style="jarvis.heading")
        brand.append(f"  v{APP_VERSION}\n", style="jarvis.muted")
        brand.append("   Desktop launcher", style="jarvis.muted")

        status = Text()
        status.append("● ", style="jarvis.success")
        status.append("готов к работе", style="jarvis.text")
        status.append(
            f"   ·   {self.program_count} программ в индексе",
            style="jarvis.muted",
        )

        header = Table.grid(expand=True)
        header.add_column(ratio=1)
        header.add_row(brand)
        header.add_row("")
        header.add_row(status)

        console.print(
            Panel(
                header,
                border_style="jarvis.border",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
        console.print()
        console.print("  Что запустить?", style="jarvis.heading")
        console.print(
            "  Введите название программы или команду «открой …».",
            style="jarvis.muted",
        )
        console.print(
            "  [jarvis.muted]/help[/] — команды   "
            "[jarvis.muted]/apps[/] — программы   "
            "[jarvis.muted]/game[/] — игровой режим   "
            "[jarvis.muted]/clear[/] — очистить   "
            "[jarvis.muted]/exit[/] — выйти"
        )

    def prompt(self) -> str:
        line_width = max(24, min(console.width - 6, 92))
        console.print()
        console.print(
            f"  ╭{'─' * line_width}",
            style="jarvis.border",
        )
        value = console.input(
            "[jarvis.border]  │[/] [jarvis.prompt]❯[/] "
        )
        console.print(
            f"  ╰{'─' * line_width}",
            style="jarvis.border",
        )
        return value.strip()

    def message(self, result: LaunchResult) -> None:
        styles = {
            "success": ("✓", "jarvis.success"),
            "error": ("!", "jarvis.error"),
            "not_found": ("?", "jarvis.accent"),
        }
        symbol, style = styles[result.kind]

        message = Table.grid(padding=(0, 1))
        message.add_column(width=3)
        message.add_column()
        message.add_row(Text(symbol, style=style), Text(result.title, style="jarvis.text"))
        if result.detail:
            message.add_row("", Text(result.detail, style="jarvis.muted"))
        console.print()
        console.print(message)

    def show_help(self) -> None:
        commands = Table.grid(padding=(0, 2))
        commands.add_column(style="jarvis.accent", no_wrap=True)
        commands.add_column(style="jarvis.text")
        commands.add_row("chrome", "Открыть программу по названию")
        commands.add_row("открой vs code", "Открыть программой-командой")
        commands.add_row("/apps", "Показать установленные программы")
        commands.add_row("VPN", "Открыть интерфейс Happ Terminal VPN")
        commands.add_row("Claude code", "Запустить ярлык Claude Code")
        commands.add_row("заметки", "Открыть встроенные заметки")
        commands.add_row("выключить пк(30)", "Выключить компьютер через 30 минут")
        commands.add_row("перезагрузка", "Немедленно перезагрузить компьютер")
        commands.add_row("спящий режим", "Перевести компьютер в спящий режим")
        commands.add_row("отменить выключение", "Отменить таймер выключения")
        commands.add_row("1", "Новое окно Яндекс Браузера")
        commands.add_row("2", "Открыть ChatGPT")
        commands.add_row("3", "Открыть VS Code")
        commands.add_row("4", "Открыть Telegram")
        commands.add_row("5", "Открыть Камеру")
        commands.add_row("пресеты", "Показать список цифровых пресетов")
        commands.add_row("kill chrome", "Принудительно завершить запущенное приложение")
        commands.add_row("Протокол игры", "Найти и принудительно завершить GPU-нагрузку")
        commands.add_row("/game preview", "Показать, что будет закрыто")
        commands.add_row("/clear", "Очистить текущую сессию")
        commands.add_row("/help", "Показать эту справку")
        commands.add_row("/exit", "Завершить JARVIS")
        console.print()
        console.print(
            Panel(
                commands,
                title="[jarvis.muted]КОМАНДЫ[/]",
                title_align="left",
                border_style="jarvis.border",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    def show_programs(self, program_names: list[str]) -> None:
        if not program_names:
            self.message(
                LaunchResult(
                    "not_found",
                    "Список программ пуст",
                    "Запустите get_programs.py, чтобы обновить индекс.",
                )
            )
            return

        entries = [
            Text(f"• {name}", style="jarvis.text")
            for name in sorted(program_names, key=str.casefold)
        ]
        console.print()
        console.print(
            Panel(
                Columns(entries, equal=True, expand=True, padding=(0, 2)),
                title=f"[jarvis.muted]ПРОГРАММЫ · {len(entries)}[/]",
                title_align="left",
                subtitle="[jarvis.muted]Введите любое название для запуска[/]",
                subtitle_align="left",
                border_style="jarvis.border",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    def show_game_mode_scan(self, scan: GameModeScan) -> None:
        console.print()
        if scan.warning:
            console.print(f"  !  {scan.warning}", style="jarvis.accent")
        if not scan.candidates:
            self.message(
                LaunchResult(
                    "success",
                    "Закрывать нечего",
                    "Браузеры не запущены, заметной GPU-нагрузки нет.",
                )
            )
            return

        table = Table(box=box.SIMPLE, show_header=True, header_style="jarvis.muted")
        table.add_column("Процесс", style="jarvis.text")
        table.add_column("PID", justify="right", style="jarvis.muted")
        table.add_column("Причина", style="jarvis.accent")
        for candidate in scan.candidates:
            table.add_row(candidate.name, str(candidate.pid), candidate.reason)
        console.print(
            Panel(
                table,
                title=f"[jarvis.muted]ИГРОВОЙ РЕЖИМ · {len(scan.candidates)}[/]",
                title_align="left",
                border_style="jarvis.border",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    def show_presets(self) -> None:
        table = Table(box=box.SIMPLE, show_header=True, header_style="jarvis.muted")
        table.add_column("№", justify="right", style="jarvis.accent")
        table.add_column("Пресет", style="jarvis.text")
        for number, (title, _program_name) in PRESET_COMMANDS.items():
            table.add_row(number, title)
        console.print()
        console.print(
            Panel(
                table,
                title="[jarvis.muted]ПРЕСЕТЫ[/]",
                title_align="left",
                border_style="jarvis.border",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    def show_notes(self, notes: list[str]) -> None:
        table = Table(box=box.SIMPLE, show_header=True, header_style="jarvis.muted")
        table.add_column("№", justify="right", style="jarvis.accent")
        table.add_column("Заметка", style="jarvis.text", overflow="fold")
        if notes:
            for number, note in enumerate(notes, start=1):
                table.add_row(str(number), note)
        else:
            table.add_row("—", "Заметок пока нет")
        console.print()
        console.print(
            Panel(
                table,
                title="[jarvis.muted]ЗАМЕТКИ[/]",
                subtitle="[jarvis.muted]добавить <текст> · удалить <№> · очистить · назад[/]",
                title_align="left",
                border_style="jarvis.border",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    def show_kill_scan(self, target: str, scan: GameModeScan) -> None:
        if not scan.candidates:
            self.message(
                LaunchResult(
                    "not_found",
                    f"Не нашёл запущенный процесс «{target}»",
                    "Защищённые системные процессы не показываются.",
                )
            )
            return
        table = Table(box=box.SIMPLE, show_header=True, header_style="jarvis.muted")
        table.add_column("Процесс", style="jarvis.text")
        table.add_column("PID", justify="right", style="jarvis.muted")
        table.add_column("Совпадение", style="jarvis.accent")
        for candidate in scan.candidates:
            table.add_row(candidate.name, str(candidate.pid), candidate.reason)
        console.print()
        console.print(
            Panel(
                table,
                title=f"[jarvis.muted]KILL · {target}[/]",
                title_align="left",
                border_style="jarvis.border",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    def show_kill_result(self, target: str, result: GameModeResult) -> None:
        if result.failed:
            details = "; ".join(
                f"{candidate.name} (PID {candidate.pid}): {error}"
                for candidate, error in result.failed
            )
            self.message(
                LaunchResult(
                    "error",
                    f"Не удалось завершить «{target}»",
                    details,
                )
            )
            return
        self.message(
            LaunchResult(
                "success",
                f"Принудительно завершено: {target}",
                f"Деревьев процесов: {len(result.closed)}",
            )
        )

    def confirm_game_mode(self) -> bool:
        answer = console.input(
            "  [jarvis.prompt]Принудительно завершить эти приложения?[/] "
            "[jarvis.muted][д/Н][/] "
        )
        return answer.strip().casefold() in {"д", "да", "y", "yes"}

    def show_game_mode_result(self, result: GameModeResult) -> None:
        if result.failed:
            details = "; ".join(
                f"{candidate.name} (PID {candidate.pid})"
                for candidate, _error in result.failed
            )
            self.message(
                LaunchResult(
                    "error",
                    f"Закрыто {len(result.closed)}, не удалось {len(result.failed)}",
                    details,
                )
            )
            return
        self.message(
            LaunchResult(
                "success",
                "Игровой режим включён",
                f"Закрыто процессов: {len(result.closed)}",
            )
        )

    def goodbye(self) -> None:
        console.print()
        farewell = Text()
        farewell.append("✦  ", style="jarvis.accent")
        farewell.append("Сессия завершена.", style="jarvis.text")
        console.print(farewell)


def run_notes_mode(ui: JarvisUI, path: Path | None = None) -> None:
    notes_path = path or notes_file_path()
    notes = load_notes(notes_path)
    ui.show_notes(notes)

    while True:
        try:
            command = ui.prompt()
        except (EOFError, KeyboardInterrupt):
            console.print()
            return
        normalized = " ".join(command.casefold().split())
        if normalized in {"назад", "выход", "back", "exit", "/exit"}:
            return
        if not normalized or normalized in {"список", "показать", "list"}:
            ui.show_notes(notes)
            continue
        if normalized in {"очистить", "clear"}:
            notes.clear()
        elif normalized.startswith("добавить ") or normalized.startswith("add "):
            note = command.split(maxsplit=1)[1].strip()
            if note:
                notes.append(note)
        elif normalized.startswith("удалить ") or normalized.startswith("delete "):
            raw_number = command.split(maxsplit=1)[1].strip()
            try:
                index = int(raw_number) - 1
                if index < 0:
                    raise ValueError
                notes.pop(index)
            except (ValueError, IndexError):
                ui.message(LaunchResult("not_found", f"Нет заметки №{raw_number}"))
                continue
        else:
            ui.message(
                LaunchResult(
                    "not_found",
                    "Неизвестная команда заметок",
                    "Используйте: добавить <текст>, удалить <№>, очистить или назад.",
                )
            )
            continue
        try:
            save_notes(notes, notes_path)
        except OSError as error:
            ui.message(LaunchResult("error", "Не удалось сохранить заметки", str(error)))
            continue
        ui.show_notes(notes)


def configure_terminal() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleTitleW(f"{APP_NAME} · Desktop launcher")
        except OSError:
            pass


def run_cli() -> int:
    program_map = get_program_map()
    startup_error = None
    if not program_map:
        program_map, startup_error = generate_program_map()

    ui = JarvisUI(len(program_map))
    ui.render_welcome()
    if startup_error:
        ui.message(LaunchResult("error", "Список программ недоступен", startup_error))

    while True:
        try:
            command = ui.prompt()
        except (EOFError, KeyboardInterrupt):
            ui.goodbye()
            return 0

        lowered = command.lower()
        if not command:
            continue
        if lowered in EXIT_COMMANDS:
            ui.goodbye()
            return 0
        if lowered in {"/clear", "clear", "очистить"}:
            ui.render_welcome()
            continue
        if lowered in {"/help", "help", "помощь"}:
            ui.show_help()
            continue
        if lowered in {"/apps", "apps", "программы", "список программ"}:
            ui.show_programs(list(program_map))
            continue
        if lowered in PRESET_LIST_COMMANDS:
            ui.show_presets()
            continue
        if lowered in NOTES_COMMANDS:
            run_notes_mode(ui)
            continue
        try:
            power_command = extract_power_command(command)
        except ValueError as error:
            ui.message(LaunchResult("error", "Некорректная команда выключения", str(error)))
            continue
        if power_command is not None:
            ui.message(execute_power_command(power_command))
            continue
        kill_target = extract_kill_target(command)
        if kill_target is not None:
            if not kill_target:
                ui.message(
                    LaunchResult(
                        "not_found",
                        "После kill нужно название программы",
                        "Например: kill chrome",
                    )
                )
                continue
            normalized_target = normalize_kill_target(kill_target)
            scan = scan_named_processes(normalized_target)
            ui.show_kill_scan(kill_target, scan)
            if not scan.candidates:
                continue
            try:
                confirmed = ui.confirm_game_mode()
            except (EOFError, KeyboardInterrupt):
                confirmed = False
                console.print()
            if not confirmed:
                ui.message(LaunchResult("success", "Kill отменён"))
                continue
            ui.show_kill_result(kill_target, activate_game_mode(scan, force=True))
            continue
        if lowered in SPECIAL_LAUNCH_COMMANDS:
            ui.message(open_special_command(lowered))
            continue
        if lowered in PRESET_COMMANDS:
            ui.message(open_preset(lowered, program_map))
            continue
        if lowered in GAME_MODE_PREVIEW_COMMANDS:
            ui.show_game_mode_scan(scan_game_mode())
            continue
        if lowered in GAME_MODE_COMMANDS:
            scan = scan_game_mode()
            ui.show_game_mode_scan(scan)
            if not scan.candidates:
                continue
            try:
                confirmed = ui.confirm_game_mode()
            except (EOFError, KeyboardInterrupt):
                confirmed = False
                console.print()
            if not confirmed:
                ui.message(LaunchResult("success", "Игровой режим отменён"))
                continue
            ui.show_game_mode_result(activate_game_mode(scan))
            continue

        program_name = extract_program_name(command)
        if not program_name:
            ui.message(
                LaunchResult(
                    "not_found",
                    "После команды нужно название",
                    "Например: открой VS Code",
                )
            )
            continue
        ui.message(open_program(program_name, program_map))


def main() -> int:
    if os.name != "nt":
        configure_terminal()
        reset_console()
        return run_cli()

    from desktop_app import run_desktop_app

    return run_desktop_app()


if __name__ == "__main__":
    raise SystemExit(main())
