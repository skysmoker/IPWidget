import os
import time
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QComboBox, QSpinBox, QCheckBox, QPushButton, QFrame,
    QMessageBox, QProgressBar, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices
from config import (
    APP_NAME, APP_VERSION, AUTHOR_NAME, AUTHOR_URL, GITHUB_URL,
    ICON_ICO_PATH, get_autostart_enabled, set_autostart_enabled,
    is_windows_light_theme, save_config
)
from styles import ensure_checkmark_icon, get_settings_stylesheet
from updater import UpdateCheckWorker, UpdateDownloadWorker, apply_update_and_restart


class SettingsDialog(QDialog):
    settings_changed = pyqtSignal(dict)

    def __init__(self, current_cfg: dict, parent=None, pending_update: dict | None = None):
        super().__init__(parent)
        self.cfg = current_cfg.copy()
        self.pending_update = pending_update
        self.check_worker = None
        self.download_worker = None
        self.check_icon_path = ensure_checkmark_icon()
        self.setWindowTitle(f"{APP_NAME} — Настройки")
        self.setFixedWidth(355)
        self.setWindowFlags(
            (self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
            | Qt.WindowType.WindowStaysOnTopHint
        )
        if os.path.exists(ICON_ICO_PATH):
            self.setWindowIcon(QIcon(ICON_ICO_PATH))

        self._init_ui()
        self._apply_theme()

        if self.pending_update and self.pending_update.get("has_update"):
            self._prompt_update(self.pending_update)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 14, 16, 11)

        # Прозрачность
        op_row = QHBoxLayout()
        op_row.addWidget(QLabel("Прозрачность окна:"))
        self.op_val_label = QLabel(f"{int(self.cfg['opacity'] * 100)}%")
        self.op_val_label.setObjectName("valueLabel")
        self.op_val_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        op_row.addWidget(self.op_val_label)
        layout.addLayout(op_row)

        self.op_slider = QSlider(Qt.Orientation.Horizontal)
        self.op_slider.setRange(25, 100)
        self.op_slider.setValue(int(self.cfg["opacity"] * 100))
        self.op_slider.valueChanged.connect(lambda v: self.op_val_label.setText(f"{v}%"))
        layout.addWidget(self.op_slider)

        # Масштаб
        sc_row = QHBoxLayout()
        sc_row.addWidget(QLabel("Масштаб виджета:"))
        self.sc_val_label = QLabel(f"{self.cfg['scale']}%")
        self.sc_val_label.setObjectName("valueLabel")
        self.sc_val_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        sc_row.addWidget(self.sc_val_label)
        layout.addLayout(sc_row)

        self.sc_slider = QSlider(Qt.Orientation.Horizontal)
        self.sc_slider.setRange(75, 150)
        self.sc_slider.setValue(int(self.cfg["scale"]))
        self.sc_slider.valueChanged.connect(lambda v: self.sc_val_label.setText(f"{v}%"))
        layout.addWidget(self.sc_slider)

        # Позиция отображения
        pos_row = QHBoxLayout()
        pos_row.addWidget(QLabel("Позиция отображения:"))
        self.pos_combo = QComboBox()
        self.pos_items = [
            ("bottom-right", "Снизу справа"),
            ("bottom-left", "Снизу слева"),
            ("top-right", "Сверху справа"),
            ("top-left", "Сверху слева"),
            ("custom", "Произвольная (Alt / СКМ)"),
        ]
        for _, title in self.pos_items:
            self.pos_combo.addItem(title)
        idx = next((i for i, (k, _) in enumerate(self.pos_items) if k == self.cfg["position"]), 0)
        self.pos_combo.setCurrentIndex(idx)
        pos_row.addWidget(self.pos_combo)
        layout.addLayout(pos_row)

        # Тема оформления
        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Тема оформления:"))
        self.theme_combo = QComboBox()
        self.theme_items = [
            ("system", "Системная (Windows)"),
            ("dark", "Тёмная"),
            ("light", "Светлая"),
        ]
        for _, title in self.theme_items:
            self.theme_combo.addItem(title)
        t_idx = next((i for i, (k, _) in enumerate(self.theme_items) if k == self.cfg["theme"]), 0)
        self.theme_combo.setCurrentIndex(t_idx)
        self.theme_combo.currentIndexChanged.connect(self._on_theme_preview)
        theme_row.addWidget(self.theme_combo)
        layout.addLayout(theme_row)

        # Период опроса
        int_row = QHBoxLayout()
        int_row.addWidget(QLabel("Период проверки (сек):"))
        self.int_spin = QSpinBox()
        self.int_spin.setRange(5, 3600)
        self.int_spin.setValue(int(self.cfg["interval"]))
        int_row.addWidget(self.int_spin)
        layout.addLayout(int_row)

        # Переключатели
        self.mask_ip_cb = QCheckBox("Скрывать IP до наведения курсора (приватность)")
        self.mask_ip_cb.setChecked(bool(self.cfg.get("mask_ip", False)))
        layout.addWidget(self.mask_ip_cb)

        self.idle_pause_cb = QCheckBox("Пауза опросов при простое более 5 мин (AFK)")
        self.idle_pause_cb.setChecked(bool(self.cfg.get("pause_on_idle", True)))
        layout.addWidget(self.idle_pause_cb)

        self.on_top_cb = QCheckBox("Отображать поверх других окон\n(автоскрытие в полноэкранном режиме)")
        self.on_top_cb.setChecked(bool(self.cfg.get("always_on_top", True)))
        layout.addWidget(self.on_top_cb)

        self.notify_cb = QCheckBox("Уведомлять при смене IP или страны")
        self.notify_cb.setChecked(bool(self.cfg.get("notify_on_change", True)))
        layout.addWidget(self.notify_cb)

        self.autostart_cb = QCheckBox("Запускать вместе с Windows")
        self.autostart_cb.setChecked(get_autostart_enabled())
        layout.addWidget(self.autostart_cb)

        # Прогресс-бар загрузки обновления
        self.update_progress = QProgressBar()
        self.update_progress.setRange(0, 100)
        self.update_progress.setTextVisible(True)
        self.update_progress.setFormat("Загрузка обновления: %p%")
        self.update_progress.setFixedHeight(16)
        self.update_progress.hide()
        layout.addWidget(self.update_progress)

        # Кнопки
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 3, 0, 1)

        self.check_upd_btn = QPushButton("Проверить обновления")
        self.check_upd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.check_upd_btn.clicked.connect(self._on_check_updates)
        btn_row.addWidget(self.check_upd_btn)

        btn_row.addStretch()

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("primaryBtn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        # Футер
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("footerLine")
        layout.addWidget(line)

        footer_row = QHBoxLayout()
        self.ver_label = QLabel(f"v{APP_VERSION}")
        self.ver_label.setObjectName("footerText")

        self.author_label = QLabel()
        self.author_label.setObjectName("footerText")
        self.author_label.setOpenExternalLinks(True)
        self.author_label.setTextFormat(Qt.TextFormat.RichText)

        footer_row.addWidget(self.ver_label)
        footer_row.addStretch()
        footer_row.addWidget(self.author_label)
        layout.addLayout(footer_row)

    def _on_check_updates(self):
        if self.check_worker and self.check_worker.isRunning():
            return
        self.check_upd_btn.setEnabled(False)
        self.check_upd_btn.setText("Проверка...")
        self.check_worker = UpdateCheckWorker()
        self.check_worker.finished_check.connect(self._on_check_finished)
        self.check_worker.start()

    def _on_check_finished(self, info: dict | None, error: str):
        self.check_upd_btn.setEnabled(True)
        self.check_upd_btn.setText("Проверить обновления")

        if error or not info:
            QMessageBox.warning(
                self, f"{APP_NAME} — Обновления",
                f"Не удалось проверить обновления.\nПроверьте подключение к интернету.\n\nДетали: {error}"
            )
            return

        self.cfg["last_update_check"] = int(time.time())
        save_config(self.cfg)

        if not info.get("has_update"):
            QMessageBox.information(
                self, f"{APP_NAME} — Обновления",
                f"У вас установлена актуальная версия (v{APP_VERSION})."
            )
            return

        self._prompt_update(info)

    def _prompt_update(self, info: dict):
        new_ver = info.get("version", "")
        notes = info.get("notes", "")
        short_notes = (notes[:320] + "…") if len(notes) > 320 else notes
        msg = f"Доступна новая версия {APP_NAME} v{new_ver} (текущая: v{APP_VERSION})."
        if short_notes:
            msg += f"\n\nЧто нового:\n{short_notes}"
        msg += "\n\nСкачать и установить обновление сейчас?"

        reply = QMessageBox.question(
            self, f"{APP_NAME} — Доступно обновление", msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        exe_url = info.get("exe_url", "")
        if not exe_url:
            html_url = info.get("html_url") or f"{GITHUB_URL}/releases/latest"
            QDesktopServices.openUrl(QUrl(html_url))
            return

        self.check_upd_btn.setEnabled(False)
        self.update_progress.setValue(0)
        self.update_progress.show()
        self.adjustSize()

        self.download_worker = UpdateDownloadWorker(exe_url)
        self.download_worker.progress.connect(self.update_progress.setValue)
        self.download_worker.finished_download.connect(self._on_download_finished)
        self.download_worker.start()

    def _on_download_finished(self, file_path: str, error: str):
        self.update_progress.hide()
        self.check_upd_btn.setEnabled(True)
        self.adjustSize()

        if error or not file_path:
            QMessageBox.critical(self, f"{APP_NAME} — Ошибка загрузки", f"Не удалось скачать обновление:\n{error}")
            return

        restarting, info_msg = apply_update_and_restart(file_path)
        if restarting:
            QApplication.quit()
        else:
            QMessageBox.information(self, f"{APP_NAME} — Обновление", info_msg)

    def _on_theme_preview(self):
        self._apply_theme(self.theme_items[self.theme_combo.currentIndex()][0])

    def _apply_theme(self, theme_override: str | None = None):
        theme = theme_override or self.cfg.get("theme", "system")
        is_light = is_windows_light_theme() if theme == "system" else (theme == "light")
        qss, link_color = get_settings_stylesheet(is_light, self.check_icon_path)

        self.author_label.setText(
            f'© Иван Черкез · '
            f'<a href="{AUTHOR_URL}" style="color: {link_color}; text-decoration: none; font-weight: 600;">@{AUTHOR_NAME}</a> · '
            f'<a href="{GITHUB_URL}" style="color: {link_color}; text-decoration: none; font-weight: 600;">GitHub</a>'
        )
        self.setStyleSheet(qss)

    def _on_save(self):
        self.cfg["opacity"] = round(self.op_slider.value() / 100.0, 2)
        self.cfg["scale"] = self.sc_slider.value()
        self.cfg["position"] = self.pos_items[self.pos_combo.currentIndex()][0]
        self.cfg["theme"] = self.theme_items[self.theme_combo.currentIndex()][0]
        self.cfg["interval"] = self.int_spin.value()
        self.cfg["mask_ip"] = self.mask_ip_cb.isChecked()
        self.cfg["pause_on_idle"] = self.idle_pause_cb.isChecked()
        self.cfg["always_on_top"] = self.on_top_cb.isChecked()
        self.cfg["notify_on_change"] = self.notify_cb.isChecked()

        set_autostart_enabled(self.autostart_cb.isChecked())
        self.settings_changed.emit(self.cfg)
        self.accept()