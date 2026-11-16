import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QSystemTrayIcon, QMenu, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QIcon, QColor, QAction, QCursor

from config import (
    APP_NAME, APP_VERSION, ICON_PNG_PATH, ICON_ICO_PATH,
    load_config, save_config, is_windows_light_theme
)
from network import fetch_ip_info
from settings_ui import SettingsDialog
from hover_card import HoverCard
from win_utils import (
    register_app_user_model_id,
    acquire_single_instance_mutex,
    is_other_app_fullscreen
)


class IpWorker(QThread):
    result_ready = pyqtSignal(object)

    def __init__(self, apis: list):
        super().__init__()
        self.apis = apis

    def run(self):
        info = fetch_ip_info(self.apis)
        self.result_ready.emit(info)


class IPWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        self.current_ip = ""
        self.current_alpha3 = ""
        self.current_city = ""
        self.current_isp = ""
        self.current_ping = None
        self.current_timezone = ""
        self.worker = None
        self.manually_hidden = False
        self.hidden_by_fullscreen = False

        self.hover_card = HoverCard()
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.setInterval(1000)
        self.hover_timer.timeout.connect(self._show_hover_card)

        self._init_ui()
        self._init_tray()
        self._apply_window_flags(initial=True)
        self._apply_theme_and_scale()
        self._position_window()

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.fetch_ip)
        self.poll_timer.start(int(self.cfg["interval"]) * 1000)

        self.fs_timer = QTimer(self)
        self.fs_timer.timeout.connect(self._check_fullscreen)
        self.fs_timer.start(1200)

        QTimer.singleShot(200, self.fetch_ip)

    def _init_ui(self):
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        outer = QVBoxLayout(self)
        outer.setContentsMargins(15, 15, 15, 16)

        self.card = QWidget()
        self.card.setObjectName("mainCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(13, 8, 13, 8)
        card_layout.setSpacing(3)

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(7)

        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("statusDot")

        self.flag_label = QLabel()
        self.flag_label.setFixedSize(20, 14)
        self.flag_label.setScaledContents(True)

        self.location_label = QLabel("...")
        self.location_label.setObjectName("locLabel")

        top_row.addStretch()
        top_row.addWidget(self.status_dot)
        top_row.addWidget(self.flag_label)
        top_row.addWidget(self.location_label)
        top_row.addStretch()

        self.ip_label = QLabel("Загрузка...")
        self.ip_label.setObjectName("ipLabel")
        self.ip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addLayout(top_row)
        card_layout.addWidget(self.ip_label)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(14)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 85))
        self.card.setGraphicsEffect(shadow)

        outer.addWidget(self.card)

    def _init_tray(self):
        self.tray = QSystemTrayIcon(self)
        if os.path.exists(ICON_ICO_PATH):
            self.tray.setIcon(QIcon(ICON_ICO_PATH))
        elif os.path.exists(ICON_PNG_PATH):
            self.tray.setIcon(QIcon(ICON_PNG_PATH))

        menu = QMenu()
        self.toggle_action = QAction("Скрыть виджет", self)
        self.toggle_action.triggered.connect(self._toggle_visibility)

        refresh_action = QAction("Обновить сейчас", self)
        refresh_action.triggered.connect(self.fetch_ip)

        copy_action = QAction("Копировать IP", self)
        copy_action.triggered.connect(self._copy_ip_to_clipboard)

        settings_action = QAction("Настройки...", self)
        settings_action.triggered.connect(self._open_settings)

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self._quit_app)

        menu.addAction(self.toggle_action)
        menu.addAction(refresh_action)
        menu.addAction(copy_action)
        menu.addSeparator()
        menu.addAction(settings_action)
        menu.addSeparator()
        menu.addAction(exit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.setToolTip(f"{APP_NAME} v{APP_VERSION}")
        self.tray.show()

    def _is_light(self) -> bool:
        theme = self.cfg.get("theme", "system")
        return is_windows_light_theme() if theme == "system" else (theme == "light")

    def _apply_window_flags(self, initial: bool = False):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.cfg.get("always_on_top", True):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        was_visible = self.isVisible()
        self.setWindowFlags(flags)
        if not initial and was_visible and not self.manually_hidden:
            self.show()

    def _apply_theme_and_scale(self):
        self.setWindowOpacity(float(self.cfg.get("opacity", 0.88)))
        scale = int(self.cfg.get("scale", 100)) / 100.0
        loc_px = max(10, int(round(12 * scale)))
        ip_px = max(11, int(round(13.5 * scale)))
        flag_w = max(15, int(round(20 * scale)))
        flag_h = max(10, int(round(14 * scale)))
        self.flag_label.setFixedSize(flag_w, flag_h)

        if self._is_light():
            bg, fg, sub_fg, border = "rgba(255, 255, 255, 238)", "#0f172a", "#475569", "#cbd5e1"
        else:
            bg, fg, sub_fg, border = "rgba(24, 24, 27, 238)", "#f4f4f5", "#a1a1aa", "#3f3f46"

        self.card.setStyleSheet(f"""
            QWidget#mainCard {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 12px;
            }}
            QLabel#locLabel {{
                color: {sub_fg};
                font-family: "Segoe UI", sans-serif;
                font-size: {loc_px}px;
                font-weight: 600;
            }}
            QLabel#ipLabel {{
                color: {fg};
                font-family: "Segoe UI", sans-serif;
                font-size: {ip_px}px;
                font-weight: 700;
            }}
            QLabel#statusDot {{
                color: #22c55e;
                font-size: {max(9, loc_px - 2)}px;
            }}
        """)
        self.card.adjustSize()
        self.adjustSize()

    def _position_window(self):
        self.card.adjustSize()
        self.adjustSize()
        w = self.sizeHint().width()
        h = self.sizeHint().height()
        self.resize(w, h)

        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        margin = 6
        pos = self.cfg.get("position", "bottom-right")

        if pos == "top-left":
            x, y = geo.left() + margin, geo.top() + margin
        elif pos == "top-right":
            x, y = geo.right() - w - margin, geo.top() + margin
        elif pos == "bottom-left":
            x, y = geo.left() + margin, geo.bottom() - h - margin
        else:
            x, y = geo.right() - w - margin, geo.bottom() - h - margin

        self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._position_window)

    def _format_location_text(self, alpha3: str, city: str) -> str:
        if city:
            short_city = city if len(city) <= 22 else city[:21] + "…"
            return f"{alpha3} — {short_city}"
        return alpha3

    def fetch_ip(self):
        if self.worker and self.worker.isRunning():
            return
        self.worker = IpWorker(self.cfg["apis"])
        self.worker.result_ready.connect(self._on_ip_result)
        self.worker.start()

    def _on_ip_result(self, info: dict | None):
        if not info:
            self.status_dot.setStyleSheet("color: #ef4444;")
            if not self.current_ip:
                self.ip_label.setText("Нет сети")
                self._position_window()
            return

        self.status_dot.setStyleSheet("color: #22c55e;")
        new_ip = info["ip"]
        new_alpha3 = info["alpha3"]
        new_city = info.get("city", "")
        self.current_isp = info.get("isp", "")
        self.current_ping = info.get("ping_ms")
        self.current_timezone = info.get("timezone", "")

        changed = bool(self.current_ip) and (
            new_ip != self.current_ip or new_alpha3 != self.current_alpha3
        )

        self.current_ip = new_ip
        self.current_alpha3 = new_alpha3
        self.current_city = new_city

        flag_path = info.get("flag_path", "")
        if flag_path and os.path.exists(flag_path):
            self.flag_label.setPixmap(QPixmap(flag_path))
        else:
            self.flag_label.clear()

        self.location_label.setText(self._format_location_text(new_alpha3, new_city))
        self.ip_label.setText(new_ip)
        self._position_window()

        loc_desc = f"{new_alpha3}, {new_city}" if new_city else new_alpha3
        self.tray.setToolTip(f"{APP_NAME}: {new_ip} — {loc_desc}")

        if changed and self.cfg.get("notify_on_change", True):
            self.tray.showMessage(
                "Смена подключения",
                f"Новый адрес: {new_ip} ({loc_desc})",
                QSystemTrayIcon.MessageIcon.Information,
                4000
            )

    def _check_fullscreen(self):
        if not self.cfg.get("always_on_top", True):
            if self.hidden_by_fullscreen:
                self.hidden_by_fullscreen = False
                if not self.manually_hidden:
                    self.show()
            return

        if self.manually_hidden:
            return

        ignore = {int(self.winId()), int(self.hover_card.winId())}
        fs_active = is_other_app_fullscreen(ignore)

        if fs_active and not self.hidden_by_fullscreen:
            self.hidden_by_fullscreen = True
            self.hover_timer.stop()
            self.hover_card.hide()
            self.hide()
        elif not fs_active and self.hidden_by_fullscreen:
            self.hidden_by_fullscreen = False
            self.show()
            self._position_window()

    def enterEvent(self, event):
        if self.current_ip:
            self.hover_timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hover_timer.stop()
        self.hover_card.hide()
        super().leaveEvent(event)

    def _show_hover_card(self):
        if not self.isVisible() or not self.current_ip:
            return
        self.hover_card.update_content(
            self.current_isp,
            self.current_ping,
            self.current_timezone,
            self._is_light()
        )
        w_geo = self.frameGeometry()
        c_w = self.hover_card.sizeHint().width()
        c_h = self.hover_card.sizeHint().height()

        pos = self.cfg.get("position", "bottom-right")
        y = (w_geo.bottom() - 4) if pos.startswith("top") else (w_geo.top() - c_h + 4)
        x = w_geo.left() if pos.endswith("left") else (w_geo.right() - c_w)

        self.hover_card.move(QPoint(x, y))
        self.hover_card.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._copy_ip_to_clipboard()
        elif event.button() == Qt.MouseButton.RightButton:
            self._open_settings()

    def _copy_ip_to_clipboard(self):
        if not self.current_ip:
            return
        QApplication.clipboard().setText(self.current_ip)
        old_text = self.ip_label.text()
        self.ip_label.setText("Скопировано!")
        self._position_window()
        QTimer.singleShot(1100, lambda: self._restore_ip_text(old_text))

    def _restore_ip_text(self, text: str):
        self.ip_label.setText(self.current_ip if self.current_ip else text)
        self._position_window()

    def _toggle_visibility(self):
        if self.isVisible():
            self.manually_hidden = True
            self.hover_timer.stop()
            self.hover_card.hide()
            self.hide()
            self.toggle_action.setText("Показать виджет")
        else:
            self.manually_hidden = False
            self.hidden_by_fullscreen = False
            self.show()
            self._position_window()
            self.toggle_action.setText("Скрыть виджет")

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._toggle_visibility()

    def _open_settings(self):
        self.hover_timer.stop()
        self.hover_card.hide()
        dlg = SettingsDialog(self.cfg, self)
        dlg.settings_changed.connect(self._on_settings_saved)

        dlg.adjustSize()
        d_w = dlg.sizeHint().width()
        d_h = dlg.sizeHint().height()

        w_geo = self.frameGeometry()
        screen = QApplication.primaryScreen()
        if screen:
            s_geo = screen.availableGeometry()
            margin = 8
            x = (w_geo.right() - d_w) if w_geo.center().x() > s_geo.center().x() else w_geo.left()
            x = max(s_geo.left() + margin, min(x, s_geo.right() - d_w - margin))

            if w_geo.top() - d_h - margin >= s_geo.top():
                y = w_geo.top() - d_h - margin
            else:
                y = min(w_geo.bottom() + margin, s_geo.bottom() - d_h - margin)

            dlg.move(QPoint(x, y))

        dlg.exec()

    def _on_settings_saved(self, new_cfg: dict):
        self.cfg = new_cfg
        save_config(self.cfg)
        self.poll_timer.setInterval(int(self.cfg["interval"]) * 1000)
        self._apply_window_flags(initial=False)
        self._apply_theme_and_scale()
        self._position_window()

    def _quit_app(self):
        self.hover_card.hide()
        self.tray.hide()
        QApplication.quit()


def main():
    register_app_user_model_id()
    mutex = acquire_single_instance_mutex()
    if not mutex:
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    if os.path.exists(ICON_ICO_PATH):
        app.setWindowIcon(QIcon(ICON_ICO_PATH))

    widget = IPWidget()
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()