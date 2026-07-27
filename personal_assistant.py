from __future__ import annotations

from desktop_app import run_desktop_app


def main() -> int:
    return run_desktop_app(
        main_qml="personal/PersonalMain.qml",
        main_window_title="Supersonic",
        instance_name="Supersonic.Personal.Instance",
        display_name="Supersonic",
        open_action_text="Открыть Supersonic",
        load_pet=True,
        autostart_name="Supersonic",
        legacy_autostart_names=("JARVIS Personal",),
    )


if __name__ == "__main__":
    raise SystemExit(main())
