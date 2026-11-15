import json
import os
import sys
import winreg

APP_NAME = "IPWidget"
APP_VERSION = "0.4.0"

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
FLAGS_DIR = os.path.join(BASE_DIR, "flags")
ICON_PNG_PATH = os.path.join(BASE_DIR, "app.png")
ICON_ICO_PATH = os.path.join(BASE_DIR, "app.ico")

DEFAULT_CONFIG = {
    "opacity": 0.92,
    "scale": 100,
    "interval": 5,
    "theme": "system",
    "position": "bottom-right",
    "notify_on_change": True,
    "apis": [
        "https://api.country.is/",
        "https://ipwho.is/",
        "http://ip-api.com/json/?fields=status,countryCode,query",
        "https://ipinfo.io/json"
    ]
}


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def is_windows_light_theme() -> bool:
    """Определяет системную тему Windows (True = светлая, False = тёмная)."""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return bool(val)
    except Exception:
        return True


def get_autostart_enabled() -> bool:
    """Проверяет, включен ли автозапуск в реестре Windows."""
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except Exception:
        return False


def set_autostart_enabled(enable: bool):
    """Включает или отключает автозапуск приложения вместе с Windows."""
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                if getattr(sys, "frozen", False):
                    cmd = f'"{sys.executable}"'
                else:
                    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                    exe = pythonw if os.path.exists(pythonw) else sys.executable
                    script = os.path.join(BASE_DIR, "main.py")
                    cmd = f'"{exe}" "{script}"'
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
    except Exception:
        pass