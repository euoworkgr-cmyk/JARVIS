from __future__ import annotations

from desktop_app import run_desktop_app


def main() -> int:
    return run_desktop_app(
        main_qml="personal/PersonalMain.qml",
        main_window_title="JARVIS Personal",
        instance_name="JARVIS.Personal.Instance",
        display_name="JARVIS Personal",
        open_action_text="Открыть JARVIS Personal",
        load_pet=True,
        autostart_name="JARVIS Personal",
    )


if __name__ == "__main__":
    raise SystemExit(main())
