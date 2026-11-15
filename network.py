import os
import requests
import pycountry
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor
from config import FLAGS_DIR


def format_country(alpha2: str) -> tuple[str, str]:
    """Превращает 'FI' в ('FIN', 'fi')."""
    if not alpha2:
        return "---", ""
    code = alpha2.strip().upper()
    country = pycountry.countries.get(alpha_2=code)
    if country:
        return country.alpha_3, code.lower()
    return code, code.lower()


def get_flag_pixmap(code_lower: str) -> QPixmap:
    """Возвращает QPixmap флага (берет из кэша или скачивает с flagcdn)."""
    os.makedirs(FLAGS_DIR, exist_ok=True)
    if code_lower:
        flag_path = os.path.join(FLAGS_DIR, f"{code_lower}.png")
        if not os.path.exists(flag_path):
            try:
                resp = requests.get(f"https://flagcdn.com/w80/{code_lower}.png", timeout=4)
                if resp.status_code == 200:
                    with open(flag_path, "wb") as f:
                        f.write(resp.content)
            except Exception:
                pass
        if os.path.exists(flag_path):
            return QPixmap(flag_path)

    pm = QPixmap(22, 14)
    pm.fill(QColor("#CCCCCC"))
    return pm


class IpFetcherThread(QThread):
    result_ready = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, apis: list[str]):
        super().__init__()
        self.apis = apis

    def run(self):
        for url in self.apis:
            url = url.strip()
            if not url:
                continue
            try:
                r = requests.get(url, timeout=4)
                if r.status_code != 200:
                    continue
                data = r.json()

                ip = data.get("ip") or data.get("query")
                cc = (
                    data.get("country")
                    or data.get("country_code")
                    or data.get("countryCode")
                )
                if ip and cc and len(cc) == 2:
                    self.result_ready.emit(str(ip), str(cc))
                    return
            except Exception:
                continue

        self.error_occurred.emit("Нет сети")