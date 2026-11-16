from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor


class HoverCard(QWidget):
    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(15, 15, 15, 16)

        self.container = QWidget()
        self.container.setObjectName("hoverBox")
        box_layout = QVBoxLayout(self.container)
        box_layout.setContentsMargins(11, 8, 11, 8)
        box_layout.setSpacing(3)

        self.isp_label = QLabel("Провайдер: —")
        self.ping_label = QLabel("Пинг: —")
        self.tz_label = QLabel("Часовой пояс: —")

        box_layout.addWidget(self.isp_label)
        box_layout.addWidget(self.ping_label)
        box_layout.addWidget(self.tz_label)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(14)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 90))
        self.container.setGraphicsEffect(shadow)

        outer.addWidget(self.container)

    def update_content(self, isp: str, ping_ms: int | None, timezone: str, is_light: bool):
        isp_text = isp if isp else "Не определён"
        if len(isp_text) > 34:
            isp_text = isp_text[:33] + "…"
        ping_text = f"{ping_ms} мс" if ping_ms is not None else "—"
        tz_text = timezone if timezone else "Не определён"

        self.isp_label.setText(f"<b>Провайдер:</b> {isp_text}")
        self.ping_label.setText(f"<b>Пинг:</b> {ping_text}")
        self.tz_label.setText(f"<b>Часовой пояс:</b> {tz_text}")

        if is_light:
            bg, fg, border = "rgba(255, 255, 255, 245)", "#0f172a", "#cbd5e1"
        else:
            bg, fg, border = "rgba(24, 24, 27, 245)", "#f4f4f5", "#3f3f46"

        self.container.setStyleSheet(f"""
            QWidget#hoverBox {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 10px;
            }}
            QLabel {{
                color: {fg};
                font-family: "Segoe UI", sans-serif;
                font-size: 12px;
                background: transparent;
            }}
        """)
        self.container.adjustSize()
        self.adjustSize()