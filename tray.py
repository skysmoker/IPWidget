import os
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from config import APP_NAME, APP_VERSION, ICON_ICO_PATH, ICON_PNG_PATH


class WidgetTray(QObject):
    toggle_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    copy_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    update_notice_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_notice_is_update = False

        self.tray = QSystemTrayIcon(parent)
        if os.path.exists(ICON_ICO_PATH):
            self.tray.setIcon(QIcon(ICON_ICO_PATH))
        elif os.path.exists(ICON_PNG_PATH):
            self.tray.setIcon(QIcon(ICON_PNG_PATH))

        menu = QMenu()
        self.toggle_action = QAction("Скрыть виджет", self)
        self.toggle_action.triggered.connect(self.toggle_requested.emit)

        refresh_action = QAction("Обновить сейчас", self)
        refresh_action.triggered.connect(self.refresh_requested.emit)

        copy_action = QAction("Копировать IP", self)
        copy_action.triggered.connect(self.copy_requested.emit)

        settings_action = QAction("Настройки...", self)
        settings_action.triggered.connect(self.settings_requested.emit)

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.quit_requested.emit)

        menu.addAction(self.toggle_action)
        menu.addAction(refresh_action)
        menu.addAction(copy_action)
        menu.addSeparator()
        menu.addAction(settings_action)
        menu.addSeparator()
        menu.addAction(exit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)
        self.tray.messageClicked.connect(self._on_message_clicked)
        self.tray.setToolTip(f"{APP_NAME} v{APP_VERSION}")
        self.tray.show()

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_requested.emit()

    def _on_message_clicked(self):
        if self._last_notice_is_update:
            self._last_notice_is_update = False
            self.update_notice_clicked.emit()

    def set_widget_visible(self, visible: bool):
        self.toggle_action.setText("Скрыть виджет" if visible else "Показать виджет")

    def update_status(self, ip: str, loc_desc: str):
        self.tray.setToolTip(f"{APP_NAME}: {ip} — {loc_desc}")

    def notify_ip_change(self, ip: str, loc_desc: str):
        self._last_notice_is_update = False
        self.tray.showMessage(
            "Смена подключения",
            f"Новый адрес: {ip} ({loc_desc})",
            QSystemTrayIcon.MessageIcon.Information,
            4000
        )

    def notify_update_available(self, new_version: str):
        self._last_notice_is_update = True
        self.tray.showMessage(
            "Доступно обновление",
            f"Вышла новая версия {APP_NAME} v{new_version}. Нажмите, чтобы установить.",
            QSystemTrayIcon.MessageIcon.Information,
            6000
        )

    def hide(self):
        self.tray.hide()