import os
import ctypes
import winreg
from ctypes import wintypes
from config import APP_NAME, ICON_ICO_PATH

user32 = ctypes.windll.user32
MONITOR_DEFAULTTONEAREST = 2


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
    ]


def register_app_user_model_id():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_NAME)
        key_path = rf"Software\Classes\AppUserModelId\{APP_NAME}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, APP_NAME)
            if os.path.exists(ICON_ICO_PATH):
                winreg.SetValueEx(key, "IconUri", 0, winreg.REG_SZ, os.path.abspath(ICON_ICO_PATH))
    except Exception:
        pass


def acquire_single_instance_mutex(name: str = "IPWidget_SingleInstance_Mutex_SkySmoker"):
    kernel32 = ctypes.windll.kernel32
    mutex = kernel32.CreateMutexW(None, False, name)
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        return None
    return mutex


def is_other_app_fullscreen(ignore_hwnds: set[int]) -> bool:
    try:
        hwnd = user32.GetForegroundWindow()
        if not hwnd or hwnd in ignore_hwnds:
            return False
        if not user32.IsWindowVisible(hwnd) or user32.IsIconic(hwnd):
            return False

        class_buf = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_buf, 256)
        if class_buf.value in ("Progman", "WorkerW", "Shell_TrayWnd", "NotifyIconOverflowWindow"):
            return False

        win_rect = RECT()
        if not user32.GetWindowRect(hwnd, ctypes.byref(win_rect)):
            return False

        hmon = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
        if not hmon:
            return False

        mon_info = MONITORINFO()
        mon_info.cbSize = ctypes.sizeof(MONITORINFO)
        if not user32.GetMonitorInfoW(hmon, ctypes.byref(mon_info)):
            return False

        m = mon_info.rcMonitor
        return (
            win_rect.left <= m.left
            and win_rect.top <= m.top
            and win_rect.right >= m.right
            and win_rect.bottom >= m.bottom
        )
    except Exception:
        return False