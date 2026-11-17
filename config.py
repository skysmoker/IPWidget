import os
import json
import sys
import winreg

APP_NAME = "IPWidget"
APP_VERSION = "0.5.0"
AUTHOR_NAME = "SkySmoker"
AUTHOR_URL = "https://t.me/SkySmoker"
GITHUB_REPO = "skysmoker/IPWidget"
GITHUB_URL = f"https://github.com/{GITHUB_REPO}"
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
RESOURCE_DIR = getattr(sys, "_MEIPASS", BASE_DIR)
LEGACY_CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

APPDATA_DIR = os.path.join(os.getenv("APPDATA") or BASE_DIR, APP_NAME)
os.makedirs(APPDATA_DIR, exist_ok=True)
CONFIG_PATH = os.path.join(APPDATA_DIR, "config.json")

FLAGS_DIR = os.path.join(APPDATA_DIR, "flags")
ICON_PNG_PATH = os.path.join(RESOURCE_DIR, "app.png")
ICON_ICO_PATH = os.path.join(RESOURCE_DIR, "app.ico")

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
    "custom_x": None,
    "custom_y": None,
    "interval": 15,
    "theme": "system",
    "notify_on_change": True,
    "always_on_top": True,
    "mask_ip": False,
    "pause_on_idle": True,
    "idle_timeout_sec": 300,
    "last_update_check": 0,
    "apis": DEFAULT_APIS.copy()
}


def load_config() -> dict:
    source_path = CONFIG_PATH if os.path.exists(CONFIG_PATH) else LEGACY_CONFIG_PATH
    if os.path.exists(source_path):
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                merged = {**DEFAULT_CONFIG, **data}
                saved_apis = merged.get("apis", [])
                if not saved_apis or saved_apis[0].startswith("https://api.country.is"):
                    merged["apis"] = DEFAULT_APIS.copy()
                else:
                    updated = [
                        DEFAULT_APIS[1] if u.startswith("http://ip-api.com/json/") else u
                        for u in saved_apis
                    ]
                    if "https://get.geojs.io/v1/ip/geo.json" not in updated:
                        updated.insert(2, "https://get.geojs.io/v1/ip/geo.json")
                    merged["apis"] = updated
                if source_path == LEGACY_CONFIG_PATH:
                    save_config(merged)
                return merged
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg: dict):
    try:
        os.makedirs(APPDATA_DIR, exist_ok=True)
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
