import sys
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon, QAction, QGuiApplication, QColor, QFontMetrics
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QSystemTrayIcon, QMenu, QFrame, QGraphicsDropShadowEffect
)

from config import (
    APP_NAME, APP_VERSION, load_config, save_config, is_windows_light_theme
)
from network import format_country, get_flag_pixmap, IpFetcherThread
from settings_ui import ensure_app_icon, SettingsDialog


class IPWidget(QWidget):
    def __init__(self, app_icon: QIcon):
        super().__init__()
        self.app_icon = app_icon
        self.config = load_config()
        self.current_ip = ""
        self.current_country_text = "---"
        self.current_code_lower = ""
        self.muted_color = "#6B7280"
        self.fetcher = None

        self.init_ui()
        self.init_tray()
        self.apply_styles()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fetch_ip)
        self.timer.start(self.config["interval"] * 1000)

        self.fetch_ip()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.container = QFrame(self)
        self.container.setObjectName("container")

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(14)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 95))
        self.container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.addWidget(self.container)

        self.box_layout = QVBoxLayout(self.container)

        self.top_row = QHBoxLayout()
        self.top_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.flag_label = QLabel()
        self.flag_label.setScaledContents(True)
        self.flag_label.setObjectName("flag")

        self.country_label = QLabel(self.current_country_text)
        self.country_label.setObjectName("country")

        self.status_dot = QLabel()
        self.status_dot.setObjectName("dot")

        self.top_row.addWidget(self.flag_label)
        self.top_row.addWidget(self.country_label)
        self.top_row.addWidget(self.status_dot)

        self.ip_label = QLabel("---")
        self.ip_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ip_label.setObjectName("ip")

        self.box_layout.addLayout(self.top_row)
        self.box_layout.addWidget(self.ip_label)

    def init_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self.app_icon)
        self.tray.setToolTip(f"{APP_NAME} v{APP_VERSION}: загрузка...")

        menu = QMenu()
        self.toggle_action = QAction("Свернуть в трей", self)
        self.toggle_action.triggered.connect(self.toggle_window)

        refresh_action = QAction("Обновить сейчас", self)
        refresh_action.triggered.connect(self.fetch_ip)

        settings_action = QAction("Настройки...", self)
        settings_action.triggered.connect(self.open_settings)

        quit_action = QAction("Выход", self)
        quit_action.triggered.connect(QApplication.instance().quit)

        menu.addAction(self.toggle_action)
        menu.addAction(refresh_action)
        menu.addAction(settings_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def set_status_color(self, color_hex: str):
        dot_size = self.status_dot.width()
        radius = dot_size // 2
        self.status_dot.setStyleSheet(
            f"background-color: {color_hex}; border-radius: {radius}px;"
        )

    def render_ip_text(self):
        if self.current_ip:
            self.ip_label.setText(
                f"<span style='color:{self.muted_color}; font-weight:normal;'>IP</span> {self.current_ip}"
            )
        else:
            self.ip_label.setText(
                f"<span style='color:{self.muted_color}; font-weight:normal;'>IP</span> ---"
            )

    def apply_styles(self):
        self.setWindowOpacity(self.config["opacity"])
        scale = self.config.get("scale", 100) / 100.0

        flag_w = max(14, round(22 * scale))
        flag_h = max(9, round(14 * scale))
        dot_sz = max(5, round(6 * scale))
        pad_x = max(8, round(12 * scale))
        pad_y = max(5, round(7 * scale))
        spacing_v = max(2, round(3 * scale))
        spacing_h = max(4, round(6 * scale))
        radius = max(8, round(12 * scale))
        font_country = max(8, round(11 * scale))
        font_ip = max(9, round(12 * scale))

        self.flag_label.setFixedSize(flag_w, flag_h)
        self.status_dot.setFixedSize(dot_sz, dot_sz)
        self.box_layout.setContentsMargins(pad_x, pad_y, pad_x, pad_y)
        self.box_layout.setSpacing(spacing_v)
        self.top_row.setSpacing(spacing_h)

        theme = self.config.get("theme", "system")
        is_light = is_windows_light_theme() if theme == "system" else (theme == "light")

        if is_light:
            bg = "#FBFBFD"
            bg_hover = "#FFFFFF"
            fg = "#111827"
            self.muted_color = "#6B7280"
            subtle_edge = "rgba(0, 0, 0, 28)"
        else:
            bg = "#202024"
            bg_hover = "#2A2A30"
            fg = "#F9FAFB"
            self.muted_color = "#9CA3AF"
            subtle_edge = "rgba(255, 255, 255, 32)"

        self.setStyleSheet(f"""
            QFrame#container {{
                background-color: {bg};
                border: 1px solid {subtle_edge};
                border-radius: {radius}px;
            }}
            QFrame#container:hover {{
                background-color: {bg_hover};
            }}
            QLabel#flag {{
                border: 1px solid {subtle_edge};
                border-radius: 2px;
            }}
            QLabel#country {{
                color: {fg};
                font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif;
                font-size: {font_country}px;
                font-weight: bold;
            }}
            QLabel#ip {{
                color: {fg};
                font-family: 'Segoe UI Variable', 'Segoe UI', sans-serif;
                font-size: {font_ip}px;
                font-weight: bold;
            }}
        """)

        self.set_status_color("#10B981" if self.current_ip else "#F59E0B")
        self.render_ip_text()

        self.ip_label.ensurePolished()
        fm = QFontMetrics(self.ip_label.font())
        sample_w = fm.horizontalAdvance("IP 888.888.888.888") + 6
        self.ip_label.setMinimumWidth(sample_w)

        self.position_widget()

    def position_widget(self):
        if self.layout():
            self.layout().activate()
        hint = self.sizeHint()
        w = max(self.minimumWidth(), hint.width())
        h = max(self.minimumHeight(), hint.height())
        self.resize(w, h)

        screen = QGuiApplication.primaryScreen().availableGeometry()
        pos = self.config.get("position", "bottom-right")

        x = screen.left() if "left" in pos else screen.right() - w
        y = screen.top() if "top" in pos else screen.bottom() - h + 2
        self.move(x, y)

    def showEvent(self, event):
        super().showEvent(event)
        self.position_widget()

    def fetch_ip(self):
        if self.fetcher and self.fetcher.isRunning():
            return
        self.set_status_color("#F59E0B")
        self.fetcher = IpFetcherThread(self.config["apis"])
        self.fetcher.result_ready.connect(self.on_ip_updated)
        self.fetcher.error_occurred.connect(self.on_ip_error)
        self.fetcher.start()

    def on_ip_updated(self, ip: str, cc: str):
        prev_ip = self.current_ip
        prev_country = self.current_country_text

        self.current_ip = ip
        country_code3, code_lower = format_country(cc)
        self.current_country_text = country_code3
        self.current_code_lower = code_lower

        pixmap = get_flag_pixmap(code_lower)
        self.flag_label.setPixmap(pixmap)
        self.country_label.setText(country_code3)
        self.render_ip_text()
        self.set_status_color("#10B981")

        self.tray.setIcon(QIcon(pixmap))
        self.tray.setToolTip(f"{country_code3} — IP: {ip}\n(Клик — скопировать IP)")
        self.position_widget()

        # Уведомление при смене страны или IP (если это не первый старт)
        if (
            prev_ip
            and (prev_ip != ip or prev_country != country_code3)
            and self.config.get("notify_on_change", True)
        ):
            self.tray.showMessage(
                f"{APP_NAME}: сменился IP-адрес",
                f"{prev_country} → {country_code3}\nНовый IP: {ip}",
                QSystemTrayIcon.MessageIcon.Information,
                3500
            )

    def on_ip_error(self, msg: str):
        self.country_label.setText(msg)
        self.current_ip = ""
        self.render_ip_text()
        self.set_status_color("#EF4444")
        self.tray.setToolTip(f"{APP_NAME} v{APP_VERSION}: {msg}")
        self.position_widget()

    def copy_ip_to_clipboard(self):
        if not self.current_ip:
            return
        QApplication.clipboard().setText(self.current_ip)
        self.ip_label.setText("<span style='color:#10B981;'>Скопировано!</span>")
        QTimer.singleShot(1000, self.render_ip_text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.copy_ip_to_clipboard()
        elif event.button() == Qt.MouseButton.RightButton:
            self.tray.contextMenu().exec(event.globalPosition().toPoint())

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.copy_ip_to_clipboard()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_window()

    def toggle_window(self):
        if self.isVisible():
            self.hide()
            self.toggle_action.setText("Показать окно")
        else:
            self.show()
            self.position_widget()
            self.toggle_action.setText("Свернуть в трей")

    def open_settings(self):
        dlg = SettingsDialog(self.config, self)
        if dlg.exec():
            self.config = dlg.get_updated_config()
            save_config(self.config)
            self.timer.setInterval(self.config["interval"] * 1000)
            self.apply_styles()
            self.fetch_ip()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Защита от двойного запуска: если программа уже запущена, пробуждаем её
    server_name = f"{APP_NAME}_SingleInstance_Lock"
    socket = QLocalSocket()
    socket.connectToServer(server_name)
    if socket.waitForConnected(250):
        socket.write(b"SHOW")
        socket.waitForBytesWritten(250)
        socket.disconnectFromServer()
        sys.exit(0)

    QLocalServer.removeServer(server_name)
    local_server = QLocalServer()
    local_server.listen(server_name)

    icon = ensure_app_icon()
    app.setWindowIcon(icon)
    widget = IPWidget(icon)

    def on_second_instance():
        conn = local_server.nextPendingConnection()
        if conn:
            conn.close()
        if not widget.isVisible():
            widget.toggle_window()
        widget.raise_()

    local_server.newConnection.connect(on_second_instance)
    widget.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()