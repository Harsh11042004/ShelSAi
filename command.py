import os
import shutil
import subprocess
import winreg


APP_PATHS_KEY = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"


def _normalize_app_name(command):
    words = [word.strip(".,!?;:") for word in command.casefold().split()]
    if words and words[0] in {"kestrel", "castrol", "castor"}:
        words = words[1:]
    if words and words[0] in {"open", "launch", "start"}:
        words.pop(0)
    if words and words[0] in {"the", "application", "app"}:
        words.pop(0)
    return " ".join(words).strip()


def _find_app_in_registry(app_name):
    registry_locations = (
        (winreg.HKEY_CURRENT_USER, 0),
        (winreg.HKEY_LOCAL_MACHINE, 0),
        (winreg.HKEY_LOCAL_MACHINE, getattr(winreg, "KEY_WOW64_32KEY", 0)),
    )

    for hive, view_flag in registry_locations:
        try:
            with winreg.OpenKey(hive, APP_PATHS_KEY, 0, winreg.KEY_READ | view_flag) as key:
                subkey_count = winreg.QueryInfoKey(key)[0]
                for index in range(subkey_count):
                    try:
                        subkey_name = winreg.EnumKey(key, index)
                        if app_name not in os.path.splitext(subkey_name.casefold())[0]:
                            continue
                        with winreg.OpenKey(key, subkey_name) as app_key:
                            executable, _ = winreg.QueryValueEx(app_key, "")
                    except OSError:
                        continue

                    executable = os.path.expandvars(executable.strip().strip('"'))
                    if os.path.isfile(executable):
                        return executable
        except OSError:
            continue
    return None


def _find_app_path(app_name):
    executable_name = app_name if app_name.casefold().endswith(".exe") else f"{app_name}.exe"
    where_result = subprocess.run(
        ["where.exe", executable_name],
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )
    search_output = where_result.stdout.strip()
    if search_output:
        print(f"CMD search results for {executable_name}:\n{search_output}")
        for candidate in search_output.splitlines():
            candidate = candidate.strip().strip('"')
            if os.path.isfile(candidate):
                return candidate
    elif where_result.stderr.strip():
        print(f"CMD search output: {where_result.stderr.strip()}")
    else:
        print(f"CMD could not find {executable_name} on PATH.")

    registry_path = _find_app_in_registry(os.path.splitext(executable_name.casefold())[0])
    if registry_path:
        print(f"Registry search result: {registry_path}")
        return registry_path
    return None


def execute_command(command):
    app_name = _normalize_app_name(command)
    if not app_name:
        print("Please say which application to open.")
        return

    app_aliases = {
        "google": "chrome",
        "google chrome": "chrome",
        "brave": "brave",
        "edge": "msedge",
        "visual studio code": "code",
        "notepad": "notepad++.exe",
        "notes": "notepad++.exe",
        "workbench": "MySQLWorkbench.exe",
        "mysql": "MySQLWorkbench.exe",
        "compass": "MongoDBCompass.exe",
        "database": "MongoDBCompass.exe",
        "virtual box": "VirtualBox.exe",
        "epic": "EpicGamesLauncher.exe",
        "games": "EpicGamesLauncher.exe",
        "zoom": "Zoom.exe",
    }
    app_name = app_aliases.get(app_name, app_name)
    print(f"Searching for {app_name}...")

    try:
        executable_path = _find_app_path(app_name)
    except subprocess.TimeoutExpired:
        print(f"CMD search timed out while looking for {app_name}.")
        return
    except OSError as error:
        print(f"Could not search for {app_name}: {error}")
        return

    if executable_path is None:
        executable_path = shutil.which(app_name)

    if executable_path is None:
        print(f"Could not find {app_name}. Check the application name or install location.")
        return

    print(f"Launching: {executable_path}")
    try:
        subprocess.Popen([executable_path])
    except OSError as error:
        print(f"Could not launch {app_name}: {error}")
