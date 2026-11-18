import os
import tempfile
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor


def ensure_checkmark_icon() -> str:
    icon_path = os.path.join(tempfile.gettempdir(), "ipwidget_checkmark_v1.png")
    if not os.path.exists(icon_path):
        pix = QPixmap(11, 11)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#ffffff"), 1.8)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(2, 5, 4, 8)
        painter.drawLine(4, 8, 9, 3)
        painter.end()
        pix.save(icon_path, "PNG")
    return icon_path.replace("\\", "/")


def get_card_stylesheet(
    is_light: bool,
    active: bool,
    loc_px: int,
    ip_px: int,
    is_offline: bool = False
) -> str:
    if is_light:
        bg = "rgba(255, 255, 255, 252)" if active else "rgba(255, 255, 255, 238)"
        border = "#3b82f6" if active else "#cbd5e1"
        fg, sub_fg = "#0f172a", "#475569"
    else:
        bg = "rgba(34, 34, 40, 248)" if active else "rgba(24, 24, 27, 238)"
        border = "#60a5fa" if active else "#3f3f46"
        fg, sub_fg = "#f4f4f5", "#a1a1aa"

    border_width = "1px"
    if is_offline:
        border = "rgba(239, 68, 68, 0.92)" if active else "rgba(239, 68, 68, 0.78)"
        border_width = "1.5px"

    return f"""
        QWidget#mainCard {{
            background-color: {bg};
            border: {border_width} solid {border};
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
    """


def get_settings_stylesheet(is_light: bool, check_icon_path: str) -> tuple[str, str]:
    if is_light:
        bg, fg, sub_fg, border = "#f8fafc", "#0f172a", "#475569", "#cbd5e1"
        ctrl_bg, ctrl_hover, groove_bg = "#ffffff", "#f1f5f9", "#e2e8f0"
        accent, accent_hover, link_color = "#2563eb", "#1d4ed8", "#2563eb"
    else:
        bg, fg, sub_fg, border = "#18181b", "#f4f4f5", "#a1a1aa", "#3f3f46"
        ctrl_bg, ctrl_hover, groove_bg = "#27272a", "#323238", "#2e2e34"
        accent, accent_hover, link_color = "#3b82f6", "#2563eb", "#60a5fa"

    qss = f"""
        QDialog {{
            background-color: {bg};
            color: {fg};
            font-family: "Segoe UI", sans-serif;
            font-size: 12px;
        }}
        QLabel {{
            color: {fg};
            background: transparent;
        }}
        QLabel#valueLabel {{
            color: {sub_fg};
            font-weight: 600;
        }}
        QLabel#footerText {{
            color: {sub_fg};
            font-size: 10.5px;
        }}
        QFrame#footerLine {{
            color: {border};
            background-color: {border};
            border: none;
            max-height: 1px;
        }}
        QProgressBar {{
            background-color: {ctrl_bg};
            color: {fg};
            border: 1px solid {border};
            border-radius: 5px;
            text-align: center;
            font-size: 10.5px;
        }}
        QProgressBar::chunk {{
            background-color: {accent};
            border-radius: 4px;
        }}
        QSlider {{
            min-height: 20px;
        }}
        QSlider::groove:horizontal {{
            height: 4px;
            background: {groove_bg};
            border-radius: 2px;
        }}
        QSlider::sub-page:horizontal {{
            background: {accent};
            border-radius: 2px;
        }}
        QSlider::handle:horizontal {{
            background: #ffffff;
            border: 2px solid {accent};
            width: 12px;
            height: 12px;
            margin: -6px 0;
            border-radius: 8px;
        }}
        QComboBox, QSpinBox {{
            background-color: {ctrl_bg};
            color: {fg};
            border: 1px solid {border};
            border-radius: 5px;
            padding: 3px 8px;
            min-width: 155px;
            selection-background-color: {accent};
            selection-color: #ffffff;
        }}
        QComboBox:hover, QSpinBox:hover {{
            background-color: {ctrl_hover};
            border-color: {accent};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {ctrl_bg};
            color: {fg};
            border: 1px solid {border};
            selection-background-color: {accent};
            selection-color: #ffffff;
            outline: 0;
        }}
        QCheckBox {{
            color: {fg};
            spacing: 8px;
            padding: 1px 0;
            background: transparent;
        }}
        QCheckBox::indicator {{
            width: 15px;
            height: 15px;
            border-radius: 4px;
            border: 1px solid {border};
            background-color: {ctrl_bg};
        }}
        QCheckBox::indicator:hover {{
            border-color: {accent};
        }}
        QCheckBox::indicator:checked {{
            background-color: {accent};
            border-color: {accent};
            image: url("{check_icon_path}");
        }}
        QPushButton {{
            background-color: {ctrl_bg};
            color: {fg};
            border: 1px solid {border};
            border-radius: 5px;
            padding: 5px 11px;
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {ctrl_hover};
            border-color: {accent};
        }}
        QPushButton:disabled {{
            color: {sub_fg};
        }}
        QPushButton#primaryBtn {{
            background-color: {accent};
            color: #ffffff;
            border: none;
            font-weight: 600;
        }}
        QPushButton#primaryBtn:hover {{
            background-color: {accent_hover};
        }}
    """
    return qss, link_color
