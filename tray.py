import os
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor
from PyQt6.QtCore import QObject, Qt, pyqtSignal
from config import APP_NAME, ICON_PNG_PATH, ICON_ICO_PATH


def _build_tray_icon() -> QIcon:
    for path in (ICON_PNG_PATH, ICON_ICO_PATH):
        if os.path.exists(path):
            icon = QIcon(path)
            if not icon.isNull():
                return icon

    pm = QPixmap(32, 32)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor("#2563eb"))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(2, 2, 28, 28, 8, 8)
    p.setBrush(QColor("#22c55e"))
    p.drawEllipse(10, 10, 12, 12)
    p.end()
    return QIcon(pm)


class WidgetTray(QObject):
    toggle_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    copy_requested = pyqtSignal()
    copy_ipv6_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    update_notice_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_notice_type = ""

        self.tray = QSystemTrayIcon(_build_tray_icon(), self)
        self.tray.setToolTip(APP_NAME)

        self.menu = QMenu()

        self.status_action = QAction("Определение IP...", self)
        self.status_action.setEnabled(False)
        self.menu.addAction(self.status_action)
        self.menu.addSeparator()

        self.toggle_action = QAction("Скрыть виджет", self)
        self.toggle_action.triggered.connect(self.toggle_requested.emit)
        self.menu.addAction(self.toggle_action)

        self.refresh_action = QAction("Обновить сейчас", self)
        self.refresh_action.triggered.connect(self.refresh_requested.emit)
        self.menu.addAction(self.refresh_action)

        self.copy_action = QAction("Копировать IP", self)
        self.copy_action.triggered.connect(self.copy_requested.emit)
        self.menu.addAction(self.copy_action)

        self.copy_ipv6_action = QAction("Копировать IPv6", self)
        self.copy_ipv6_action.triggered.connect(self.copy_ipv6_requested.emit)
        self.copy_ipv6_action.setVisible(False)
        self.menu.addAction(self.copy_ipv6_action)

        self.menu.addSeparator()

        self.settings_action = QAction("Настройки...", self)
        self.settings_action.triggered.connect(self.settings_requested.emit)
        self.menu.addAction(self.settings_action)

        self.quit_action = QAction("Выход", self)
        self.quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(self.quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)
        self.tray.messageClicked.connect(self._on_message_clicked)
        self.tray.show()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.toggle_requested.emit()

    def _on_message_clicked(self):
        if self._last_notice_type == "update":
            self.update_notice_clicked.emit()

    def set_widget_visible(self, visible: bool):
        self.toggle_action.setText("Скрыть виджет" if visible else "Показать виджет")

    def update_status(self, ip: str, loc_desc: str, ipv6: str = ""):
        self.status_action.setText(f"{loc_desc} · {ip}")
        self.tray.setToolTip(f"{APP_NAME}: {loc_desc} ({ip})")
        self.copy_ipv6_action.setVisible(bool(ipv6))

    def notify_ip_change(self, ip: str, loc_desc: str):
        self._last_notice_type = "ip"
        self.tray.showMessage(
            f"{APP_NAME}: сменился адрес",
            f"Новое подключение: {loc_desc}\nIP: {ip}",
            QSystemTrayIcon.MessageIcon.Information,
            3500
        )

    def notify_update_available(self, version: str):
        self._last_notice_type = "update"
        self.tray.showMessage(
            f"{APP_NAME}: доступно обновление v{version}",
            "Нажмите на уведомление или откройте Настройки, чтобы обновиться.",
            QSystemTrayIcon.MessageIcon.Information,
            5000
        )

    def hide(self):
        self.tray.hide()