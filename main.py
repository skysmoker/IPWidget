import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QIcon, QColor, QCursor

from config import (
    ICON_ICO_PATH, load_config, save_config, is_windows_light_theme,
    get_autostart_enabled, set_autostart_enabled
)
from network import fetch_ip_info
from settings_ui import SettingsDialog
from hover_card import HoverCard
from tray import WidgetTray
from updater import SilentUpdateWatcher
from styles import get_card_stylesheet
from positioning import (
    mask_ip_address, snap_to_edges, calculate_widget_pos,
    calculate_hover_card_pos, calculate_dialog_pos
)
from win_utils import (
    register_app_user_model_id,
    acquire_single_instance_mutex,
    is_other_app_fullscreen,
    SessionPowerWatcher,
    get_user_idle_seconds
)


class IpWorker(QThread):
    result_ready = pyqtSignal(object)

    def __init__(self, apis: list):
        super().__init__()
        self.apis = apis

    def run(self):
        self.result_ready.emit(fetch_ip_info(self.apis))


class IPWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = load_config()
        if get_autostart_enabled():
            set_autostart_enabled(True)

        self.current_ip = ""
        self.current_alpha3 = ""
        self.current_isp = ""
        self.current_iface = ""
        self.current_ping = None
        self.current_timezone = ""
        self.worker = None
        self.pending_update = None
        self.manually_hidden = False
        self.hidden_by_fullscreen = False
        self._is_hovered = False
        self._copy_feedback_active = False
        self._is_afk_paused = False
        self._dragging = False
        self._drag_offset = QPoint()

        self.hover_card = HoverCard()
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.setInterval(1000)
        self.hover_timer.timeout.connect(self._show_hover_card)

        self._init_ui()
        self._init_services()
        self._apply_window_flags(initial=True)
        self._apply_theme_and_scale()

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self._on_poll_tick)
        self.poll_timer.start(int(self.cfg["interval"]) * 1000)

        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self._check_user_activity)
        self.idle_timer.start(1000)

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

    def _init_services(self):
        self.tray = WidgetTray(self)
        self.tray.toggle_requested.connect(self._toggle_visibility)
        self.tray.refresh_requested.connect(self.fetch_ip)
        self.tray.copy_requested.connect(self._copy_ip_to_clipboard)
        self.tray.settings_requested.connect(self._open_settings)
        self.tray.quit_requested.connect(self._quit_app)
        self.tray.update_notice_clicked.connect(self._open_settings)

        self.update_watcher = SilentUpdateWatcher(self.cfg, self)
        self.update_watcher.update_available.connect(self._on_update_found)

        self.session_watcher = SessionPowerWatcher(int(self.winId()), self)
        self.session_watcher.resumed_or_unlocked.connect(self._on_session_resumed)
        app = QApplication.instance()
        if app:
            app.installNativeEventFilter(self.session_watcher)

    def _on_session_resumed(self):
        self._is_afk_paused = False
        QTimer.singleShot(1500, self.fetch_ip)

    def _on_update_found(self, info: dict):
        self.pending_update = info
        self.tray.notify_update_available(info.get("version", ""))

    def _is_light(self) -> bool:
        theme = self.cfg.get("theme", "system")
        return is_windows_light_theme() if theme == "system" else (theme == "light")

    def _displayed_ip_text(self) -> str:
        if not self.current_ip:
            return "Загрузка..."
        if self.cfg.get("mask_ip", False) and not (self._is_hovered or self._dragging):
            return mask_ip_address(self.current_ip)
        return self.current_ip

    def _refresh_ip_label_text(self, resize_window: bool = True):
        if self._copy_feedback_active or not self.current_ip:
            return
        new_text = self._displayed_ip_text()
        if self.ip_label.text() != new_text:
            self.ip_label.setText(new_text)
            if resize_window:
                self._position_window()

    def _apply_window_flags(self, initial: bool = False):
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.cfg.get("always_on_top", True):
            flags |= Qt.WindowType.WindowStaysOnTopHint
        was_visible = self.isVisible()
        self.setWindowFlags(flags)
        if not initial and was_visible and not self.manually_hidden:
            self.show()

    def _apply_theme_and_scale(self):
        scale = int(self.cfg.get("scale", 100)) / 100.0
        self._loc_px = max(10, int(round(12 * scale)))
        self._ip_px = max(11, int(round(13.5 * scale)))
        self.flag_label.setFixedSize(max(15, int(round(20 * scale))), max(10, int(round(14 * scale))))

        self._update_card_style()
        self._refresh_ip_label_text(resize_window=False)
        self._position_window()

    def _update_card_style(self):
        base_opacity = float(self.cfg.get("opacity", 0.88))
        active = self._is_hovered or self._dragging
        self.setWindowOpacity(min(1.0, base_opacity + 0.08) if active else base_opacity)
        self.card.setStyleSheet(
            get_card_stylesheet(self._is_light(), active, self._loc_px, self._ip_px)
        )

    def _position_window(self):
        old_w, old_h = self.width(), self.height()

        self.card.setMinimumSize(0, 0)
        self.card.setMaximumSize(16777215, 16777215)
        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)

        self.card.adjustSize()
        self.adjustSize()
        w, h = self.sizeHint().width(), self.sizeHint().height()
        self.setFixedSize(w, h)

        self.move(calculate_widget_pos(self.cfg, w, h, old_w, old_h))

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._position_window)

    def _check_user_activity(self):
        if not self.cfg.get("pause_on_idle", True):
            if self._is_afk_paused:
                self._is_afk_paused = False
                self.fetch_ip()
            return

        threshold = int(self.cfg.get("idle_timeout_sec", 300))
        idle_sec = get_user_idle_seconds()

        if idle_sec >= threshold:
            if not self._is_afk_paused:
                self._is_afk_paused = True
                if self.current_ip:
                    self.status_dot.setStyleSheet("color: #64748b;")
        else:
            if self._is_afk_paused:
                self._is_afk_paused = False
                self.fetch_ip()

    def _on_poll_tick(self):
        if self._is_afk_paused:
            return
        self.fetch_ip()

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

        self.status_dot.setStyleSheet("color: #64748b;" if self._is_afk_paused else "color: #22c55e;")
        new_ip, new_alpha3 = info["ip"], info["alpha3"]
        new_city = info.get("city", "")
        self.current_isp = info.get("isp", "")
        self.current_iface = info.get("iface", "")
        self.current_ping = info.get("ping_ms")
        self.current_timezone = info.get("timezone", "")

        changed = bool(self.current_ip) and (
            new_ip != self.current_ip or new_alpha3 != self.current_alpha3
        )
        self.current_ip, self.current_alpha3 = new_ip, new_alpha3

        flag_path = info.get("flag_path", "")
        if flag_path and os.path.exists(flag_path):
            self.flag_label.setPixmap(QPixmap(flag_path))
        else:
            self.flag_label.clear()

        short_city = (new_city[:21] + "…") if len(new_city) > 22 else new_city
        self.location_label.setText(f"{new_alpha3} — {short_city}" if short_city else new_alpha3)
        if not self._copy_feedback_active:
            self.ip_label.setText(self._displayed_ip_text())
        self._position_window()

        loc_desc = f"{new_alpha3}, {new_city}" if new_city else new_alpha3
        self.tray.update_status(new_ip, loc_desc)

        if changed and self.cfg.get("notify_on_change", True):
            self.tray.notify_ip_change(new_ip, loc_desc)

    def _check_fullscreen(self):
        if not self.cfg.get("always_on_top", True):
            if self.hidden_by_fullscreen:
                self.hidden_by_fullscreen = False
                if not self.manually_hidden:
                    self.show()
            return
        if self.manually_hidden or self._dragging:
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
        self._is_hovered = True
        self._update_card_style()
        if self.cfg.get("mask_ip", False):
            self._refresh_ip_label_text(resize_window=True)
        if self.current_ip and not self._dragging:
            self.hover_timer.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self._update_card_style()
        if self.cfg.get("mask_ip", False):
            self._refresh_ip_label_text(resize_window=True)
        self.hover_timer.stop()
        self.hover_card.hide()
        super().leaveEvent(event)

    def _show_hover_card(self):
        if not self.isVisible() or not self.current_ip or self._dragging:
            return
        self.hover_card.update_content(
            self.current_isp,
            self.current_ping,
            self.current_timezone,
            self._is_light(),
            bool(self.cfg.get("mask_ip", False)),
            self.current_iface
        )
        pos = calculate_hover_card_pos(
            self.frameGeometry(),
            self.hover_card.sizeHint().width(),
            self.hover_card.sizeHint().height(),
            self.cfg.get("position", "bottom-right")
        )
        self.hover_card.move(pos)
        self.hover_card.show()

    def mousePressEvent(self, event):
        is_middle = event.button() == Qt.MouseButton.MiddleButton
        is_alt_left = (
            event.button() == Qt.MouseButton.LeftButton
            and bool(event.modifiers() & Qt.KeyboardModifier.AltModifier)
        )
        if is_middle or is_alt_left:
            self._dragging = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.hover_timer.stop()
            self.hover_card.hide()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            self._update_card_style()
            event.accept()
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self._copy_ip_to_clipboard()
        elif event.button() == Qt.MouseButton.RightButton:
            self._open_settings()

    def mouseMoveEvent(self, event):
        if self._dragging:
            target = event.globalPosition().toPoint() - self._drag_offset
            self.move(snap_to_edges(target.x(), target.y(), self.width(), self.height()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging and event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.LeftButton):
            self._dragging = False
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self._update_card_style()

            self.cfg["position"] = "custom"
            self.cfg["custom_x"] = self.x()
            self.cfg["custom_y"] = self.y()
            save_config(self.cfg)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _copy_ip_to_clipboard(self):
        if not self.current_ip:
            return
        QApplication.clipboard().setText(self.current_ip)
        self._copy_feedback_active = True
        self.ip_label.setText("Скопировано!")
        self._position_window()
        QTimer.singleShot(1100, self._restore_ip_text)

    def _restore_ip_text(self):
        self._copy_feedback_active = False
        self.ip_label.setText(self._displayed_ip_text())
        self._position_window()

    def _toggle_visibility(self):
        if self.isVisible():
            self.manually_hidden = True
            self.hover_timer.stop()
            self.hover_card.hide()
            self.hide()
            self.tray.set_widget_visible(False)
        else:
            self.manually_hidden = False
            self.hidden_by_fullscreen = False
            self.show()
            self._position_window()
            self.tray.set_widget_visible(True)

    def _open_settings(self):
        self.hover_timer.stop()
        self.hover_card.hide()
        pending = self.pending_update
        self.pending_update = None

        dlg = SettingsDialog(self.cfg, self, pending_update=pending)
        dlg.settings_changed.connect(self._on_settings_saved)
        dlg.adjustSize()
        dlg.move(calculate_dialog_pos(self.frameGeometry(), dlg.sizeHint().width(), dlg.sizeHint().height()))
        dlg.exec()

    def _on_settings_saved(self, new_cfg: dict):
        self.cfg = new_cfg
        save_config(self.cfg)
        self.poll_timer.setInterval(int(self.cfg["interval"]) * 1000)
        self._apply_window_flags(initial=False)
        self._apply_theme_and_scale()
        self._position_window()

    def _quit_app(self):
        self.session_watcher.cleanup()
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