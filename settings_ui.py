import os
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import (
    QPixmap, QIcon, QGuiApplication, QPainter,
    QColor, QLinearGradient, QPen, QBrush
)
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QSlider, QLabel, QHBoxLayout,
    QSpinBox, QComboBox, QCheckBox, QTextEdit, QPushButton
)
from config import (
    APP_NAME, APP_VERSION, ICON_PNG_PATH, ICON_ICO_PATH,
    DEFAULT_CONFIG, get_autostart_enabled, set_autostart_enabled
)


def ensure_app_icon() -> QIcon:
    """Генерирует фирменную иконку приложения (PNG + ICO), если её ещё нет."""
    if not os.path.exists(ICON_PNG_PATH) or not os.path.exists(ICON_ICO_PATH):
        size = 256
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        grad = QLinearGradient(0, 0, size, size)
        grad.setColorAt(0.0, QColor("#0F294A"))
        grad.setColorAt(1.0, QColor("#1D63B8"))
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(QColor("#3B82F6"), 6))
        painter.drawRoundedRect(QRectF(8, 8, size - 16, size - 16), 54, 54)

        pen_globe = QPen(QColor("#E0F2FE"), 10)
        painter.setPen(pen_globe)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(48, 48, 160, 160))
        painter.drawEllipse(QRectF(88, 48, 80, 160))
        painter.drawLine(48, 128, 208, 128)

        painter.setBrush(QBrush(QColor("#10B981")))
        painter.setPen(QPen(QColor("#0F294A"), 8))
        painter.drawEllipse(QRectF(164, 164, 56, 56))

        painter.end()

        pm.save(ICON_PNG_PATH, "PNG")
        pm.save(ICON_ICO_PATH, "ICO")

    return QIcon(ICON_ICO_PATH if os.path.exists(ICON_ICO_PATH) else ICON_PNG_PATH)


class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Настройки {APP_NAME} (v{APP_VERSION})")
        self.setFixedWidth(370)
        self.config = config

        layout = QFormLayout(self)
        layout.setSpacing(10)

        # Прозрачность
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(25, 100)
        self.opacity_slider.setValue(int(config["opacity"] * 100))
        self.opacity_label = QLabel(f"{int(config['opacity'] * 100)}%")
        self.opacity_label.setFixedWidth(38)
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(f"{v}%")
        )
        op_row = QHBoxLayout()
        op_row.addWidget(self.opacity_slider)
        op_row.addWidget(self.opacity_label)
        layout.addRow("Непрозрачность:", op_row)

        # Масштаб окна
        self.scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.scale_slider.setRange(70, 150)
        self.scale_slider.setValue(int(config.get("scale", 100)))
        self.scale_label = QLabel(f"{int(config.get('scale', 100))}%")
        self.scale_label.setFixedWidth(38)
        self.scale_slider.valueChanged.connect(
            lambda v: self.scale_label.setText(f"{v}%")
        )
        sc_row = QHBoxLayout()
        sc_row.addWidget(self.scale_slider)
        sc_row.addWidget(self.scale_label)
        layout.addRow("Масштаб окна:", sc_row)

        # Угол экрана
        self.pos_combo = QComboBox()
        self.pos_combo.addItem("Правый нижний (возле трея)", "bottom-right")
        self.pos_combo.addItem("Левый нижний", "bottom-left")
        self.pos_combo.addItem("Правый верхний", "top-right")
        self.pos_combo.addItem("Левый верхний", "top-left")
        idx_pos = self.pos_combo.findData(config.get("position", "bottom-right"))
        if idx_pos >= 0:
            self.pos_combo.setCurrentIndex(idx_pos)
        layout.addRow("Угол экрана:", self.pos_combo)

        # Период обновления
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(2, 3600)
        self.interval_spin.setSuffix(" сек.")
        self.interval_spin.setValue(config["interval"])
        layout.addRow("Обновлять каждые:", self.interval_spin)

        # Тема оформления
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Системная (как в Windows)", "system")
        self.theme_combo.addItem("Светлая", "light")
        self.theme_combo.addItem("Тёмная", "dark")
        idx_th = self.theme_combo.findData(config.get("theme", "system"))
        if idx_th >= 0:
            self.theme_combo.setCurrentIndex(idx_th)
        layout.addRow("Тема окна:", self.theme_combo)

        # Уведомление при смене страны / обрыве VPN (на всю ширину от левого края)
        self.notify_cb = QCheckBox("Уведомлять при смене страны или IP")
        self.notify_cb.setChecked(config.get("notify_on_change", True))
        layout.addRow(self.notify_cb)

        # Автозапуск (на всю ширину от левого края)
        self.autostart_cb = QCheckBox("Запускать вместе с Windows")
        self.autostart_cb.setChecked(get_autostart_enabled())
        layout.addRow(self.autostart_cb)

        # Список серверов
        self.apis_edit = QTextEdit()
        self.apis_edit.setPlainText("\n".join(config["apis"]))
        self.apis_edit.setFixedHeight(80)
        layout.addRow("Серверы (JSON API):", self.apis_edit)

        # Версия и кнопка сохранения
        bottom_row = QHBoxLayout()
        ver_label = QLabel(f"Версия {APP_VERSION}")
        ver_label.setStyleSheet("color: #888888; font-size: 11px;")
        save_btn = QPushButton("Сохранить и применить")
        save_btn.clicked.connect(self.accept)
        bottom_row.addWidget(ver_label)
        bottom_row.addStretch()
        bottom_row.addWidget(save_btn)
        layout.addRow(bottom_row)

    def showEvent(self, event):
        """Открывает настройки рядом с виджетом (над или под ним), не перекрывая его."""
        super().showEvent(event)
        screen = QGuiApplication.primaryScreen().availableGeometry()
        pos = self.config.get("position", "bottom-right")

        x = screen.left() + 8 if "left" in pos else screen.right() - self.width() - 8

        if self.parent() and self.parent().isVisible():
            if "top" in pos:
                y = self.parent().y() + self.parent().height() + 4
            else:
                y = self.parent().y() - self.height() - 4
        else:
            y = screen.top() + 10 if "top" in pos else screen.bottom() - self.height() - 10

        self.move(
            max(screen.left() + 8, min(x, screen.right() - self.width() - 8)),
            max(screen.top() + 8, min(y, screen.bottom() - self.height() - 8))
        )

    def get_updated_config(self) -> dict:
        set_autostart_enabled(self.autostart_cb.isChecked())
        apis = [line.strip() for line in self.apis_edit.toPlainText().splitlines() if line.strip()]
        return {
            "opacity": self.opacity_slider.value() / 100.0,
            "scale": self.scale_slider.value(),
            "position": self.pos_combo.currentData(),
            "interval": self.interval_spin.value(),
            "theme": self.theme_combo.currentData(),
            "notify_on_change": self.notify_cb.isChecked(),
            "apis": apis or DEFAULT_CONFIG["apis"]
        }