import os
import json
import sys
import winreg

APP_NAME = "IPWidget"
APP_VERSION = "0.4.1"
AUTHOR_NAME = "SkySmoker"
AUTHOR_URL = "https://t.me/SkySmoker"
GITHUB_URL = "https://github.com/skysmoker"

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
FLAGS_DIR = os.path.join(BASE_DIR, "flags")
ICON_PNG_PATH = os.path.join(BASE_DIR, "app.png")
ICON_ICO_PATH = os.path.join(BASE_DIR, "app.ico")

DEFAULT_APIS = [
    "https://ipwho.is/",
    "http://ip-api.com/json/?fields=status,countryCode,query,city,isp,org,timezone",
    "https://get.geojs.io/v1/ip/geo.json",
    "https://ipinfo.io/json",
    "https://api.country.is/"
]

DEFAULT_CONFIG = {
    "opacity": 0.88,
    "scale": 100,
    "position": "bottom-right",
    "interval": 15,
    "theme": "system",
    "notify_on_change": True,
    "always_on_top": True,
    "apis": DEFAULT_APIS.copy()
}


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = {**DEFAULT_CONFIG, **data}
                # Гарантируем, что API с полными данными идут раньше api.country.is
                saved_apis = merged.get("apis", [])
                if not saved_apis or saved_apis[0].startswith("https://api.country.is"):
                    merged["apis"] = DEFAULT_APIS.copy()
                else:
                    updated = []
                    for url in saved_apis:
                        if url.startswith("http://ip-api.com/json/"):
                            updated.append(DEFAULT_APIS[1])
                        else:
                            updated.append(url)
                    if "https://get.geojs.io/v1/ip/geo.json" not in updated:
                        updated.insert(2, "https://get.geojs.io/v1/ip/geo.json")
                    merged["apis"] = updated
                return merged
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
    except Exception:
        pass


def is_windows_light_theme() -> bool:
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return bool(val)
    except Exception:
        return False


def get_autostart_enabled() -> bool:
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.QueryValueEx(key, APP_NAME)
            return True
    except FileNotFoundError:
        return False
    except Exception:
        return False


def set_autostart_enabled(enable: bool):
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enable:
                if getattr(sys, "frozen", False):
                    cmd = f'"{sys.executable}"'
                else:
                    script = os.path.abspath(sys.argv[0])
                    cmd = f'"{sys.executable}" "{script}"'
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
            else:
                try:
                    winreg.DeleteValue(key, APP_NAME)
                except FileNotFoundError:
                    pass
    except Exception:
        pass