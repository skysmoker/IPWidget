import os
import sys
import time
import tempfile
import subprocess
import requests
from PyQt6.QtCore import QObject, QThread, QTimer, pyqtSignal
from config import APP_NAME, APP_VERSION, GITHUB_API_LATEST, save_config
from i18n import t

WEEKLY_CHECK_SECONDS = 7 * 24 * 60 * 60


def parse_version(ver_str: str) -> tuple[int, ...]:
    cleaned = ver_str.strip().lstrip("vV").split("-")[0]
    parts = []
    for item in cleaned.split("."):
        try:
            parts.append(int(item))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def check_github_release() -> dict | None:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{APP_NAME}/{APP_VERSION}"
    }
    resp = requests.get(GITHUB_API_LATEST, headers=headers, timeout=8)
    resp.raise_for_status()
    data = resp.json()

    tag = data.get("tag_name", "")
    if not tag:
        return None

    remote_ver = parse_version(tag)
    local_ver = parse_version(APP_VERSION)
    is_newer = remote_ver > local_ver

    exe_url = ""
    for asset in data.get("assets", []):
        name = asset.get("name", "").lower()
        if name.endswith(".exe"):
            exe_url = asset.get("browser_download_url", "")
            break

    return {
        "has_update": is_newer,
        "version": tag.lstrip("vV"),
        "tag": tag,
        "notes": (data.get("body") or "").strip(),
        "exe_url": exe_url,
        "html_url": data.get("html_url", "")
    }


class UpdateCheckWorker(QThread):
    finished_check = pyqtSignal(object, str)  # (release_info | None, error_msg)

    def run(self):
        try:
            info = check_github_release()
            self.finished_check.emit(info, "")
        except Exception as e:
            self.finished_check.emit(None, str(e))


class UpdateDownloadWorker(QThread):
    progress = pyqtSignal(int)
    finished_download = pyqtSignal(str, str)  # (downloaded_path, error_msg)

    def __init__(self, download_url: str):
        super().__init__()
        self.download_url = download_url

    def run(self):
        try:
            headers = {"User-Agent": f"{APP_NAME}/{APP_VERSION}"}
            resp = requests.get(self.download_url, headers=headers, stream=True, timeout=20)
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0))
            target_path = os.path.join(tempfile.gettempdir(), "IPWidget_update.exe")

            downloaded = 0
            with open(target_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = min(100, int(downloaded * 100 / total))
                            self.progress.emit(pct)

            self.progress.emit(100)
            self.finished_download.emit(target_path, "")
        except Exception as e:
            self.finished_download.emit("", str(e))


def apply_update_and_restart(new_exe_path: str) -> tuple[bool, str]:
    if not getattr(sys, "frozen", False):
        dest = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "IPWidget_latest.exe")
        try:
            if os.path.exists(dest):
                os.remove(dest)
            os.replace(new_exe_path, dest)
            return False, t("upd_dev_saved", dest=dest)
        except Exception as e:
            return False, t("upd_save_err", error=e)

    current_exe = os.path.abspath(sys.executable)
    pid = os.getpid()
    bat_path = os.path.join(tempfile.gettempdir(), "ipwidget_apply_update.bat")

    bat_content = f"""@echo off
chcp 65001 >nul
set "PYINSTALLER_RESET_ENVIRONMENT=1"
set "_MEIPASS="
set "_MEIPASS2="
set "_PYI_PARENT_PROCESS_LEVEL="
set "_PYI_ARCHIVE_FILE="
set "_PYI_SPLASH_IPC="

:waitloop
tasklist /FI "PID eq {pid}" 2>NUL | find /I "{pid}" >NUL
if not errorlevel 1 (
    timeout /t 1 /nobreak >NUL
    goto waitloop
)

timeout /t 2 /nobreak >NUL

set /a tries=0
:moveloop
move /Y "{new_exe_path}" "{current_exe}" >NUL 2>&1
if errorlevel 1 (
    set /a tries+=1
    if %tries% LSS 10 (
        timeout /t 1 /nobreak >NUL
        goto moveloop
    )
)

start "" "{current_exe}"
del "%~f0"
"""
    try:
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

        clean_env = {
            k: v for k, v in os.environ.items()
            if not k.startswith("_PYI_") and not k.startswith("_MEIPASS")
        }
        clean_env["PYINSTALLER_RESET_ENVIRONMENT"] = "1"

        CREATE_NO_WINDOW = 0x08000000
        subprocess.Popen(
            ["cmd.exe", "/c", bat_path],
            env=clean_env,
            creationflags=CREATE_NO_WINDOW,
            close_fds=True
        )
        return True, ""
    except Exception as e:
        return False, t("upd_bat_err", error=e)


class SilentUpdateWatcher(QObject):
    update_available = pyqtSignal(dict)

    def __init__(self, cfg: dict, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.worker = None
        QTimer.singleShot(10000, self._check_if_due)

    def _check_if_due(self):
        now = int(time.time())
        last_check = int(self.cfg.get("last_update_check", 0))
        if now - last_check < WEEKLY_CHECK_SECONDS:
            return
        self.worker = UpdateCheckWorker()
        self.worker.finished_check.connect(self._on_finished)
        self.worker.start()

    def _on_finished(self, info: dict | None, error: str):
        if error or not info:
            return
        self.cfg["last_update_check"] = int(time.time())
        save_config(self.cfg)
        if info.get("has_update"):
            self.update_available.emit(info)