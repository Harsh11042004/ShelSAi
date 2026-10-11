import winreg

def get_installed_apps():
    apps = set()
    # Paths to look inside the Windows Registry
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
    ]
    
    for hive, path in registry_paths:
        try:
            with winreg.OpenKey(hive, path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            app_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                            if app_name:
                                apps.add(app_name)
                    except WindowsError:
                        continue
        except WindowsError:
            continue

    # Save them directly to a text file in your project folder
    with open("my_installed_apps.txt", "w", encoding="utf-8") as f:
        for app in sorted(apps):
            f.write(app + "\n")
            
    print("Success! Open 'my_installed_apps.txt' inside your project folder to see the list.")

if __name__ == "__main__":
    get_installed_apps()
