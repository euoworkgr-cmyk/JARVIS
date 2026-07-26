
import subprocess
import json
import os

def get_installed_programs():
    try:
        # Force a known encoding instead of guessing between Windows code pages.
        powershell_command = (
            "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); "
            "@(Get-StartApps | Select-Object Name, AppID) | "
            "ConvertTo-Json -Compress"
        )
        process = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", powershell_command],
            capture_output=True,
            check=True,
        )

        output = process.stdout.decode("utf-8-sig").strip()
        apps = json.loads(output)
        if isinstance(apps, dict):
            apps = [apps]
        
        program_map = {}
        for app in apps:
            name = app.get("Name")
            app_id = app.get("AppID")
            
            if name and app_id:
                # Store everything. We will use shell:AppsFolder to launch them in assistant.py
                # This handles both UWP (AppID) and Win32 (Path) apps correctly.
                program_map[name.lower()] = app_id

        return program_map
    except Exception as e:
        print(f"An error occurred: {e}")
        return {}

if __name__ == "__main__":
    programs = get_installed_programs()
    if programs:
        # Ensure we write with utf-8 for the json file
        with open(os.path.join(os.path.dirname(__file__), "programs.json"), "w", encoding="utf-8") as f:
            json.dump(programs, f, ensure_ascii=False, indent=4)
        print("Список программ успешно сохранен в programs.json")
    else:
        print("Не удалось получить список программ.")
