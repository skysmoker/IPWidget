from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from i18n import t


def _mask_ipv6(addr: str) -> str:
    parts = addr.split(":")
    if len(parts) >= 3:
        return f"{parts[0]}:{parts[1]}:••••:••••"
    return "••••:••••"


class HoverCard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        self.box = QWidget()
        self.box.setObjectName("hoverBox")
        box_layout = QVBoxLayout(self.box)
        box_layout.setContentsMargins(12, 8, 12, 8)
        box_layout.setSpacing(3)

        self.isp_label = QLabel()
        self.isp_label.setObjectName("detailRow")

        self.iface_label = QLabel()
        self.iface_label.setObjectName("detailRow")

        self.ipv6_label = QLabel()
        self.ipv6_label.setObjectName("detailRow")

        self.ping_label = QLabel()
        self.ping_label.setObjectName("detailRow")

        self.tz_label = QLabel()
        self.tz_label.setObjectName("detailRow")

        self.privacy_label = QLabel()
        self.privacy_label.setObjectName("privacyRow")
        self.privacy_label.hide()

        box_layout.addWidget(self.isp_label)
        box_layout.addWidget(self.iface_label)
        box_layout.addWidget(self.ipv6_label)
        box_layout.addWidget(self.ping_label)
        box_layout.addWidget(self.tz_label)
        box_layout.addWidget(self.privacy_label)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.box.setGraphicsEffect(shadow)

        outer.addWidget(self.box)

    def update_content(
        self,
        isp: str,
        ping_ms: int | None,
        timezone: str,
        is_light: bool,
        is_private: bool = False,
        iface: str = "",
        ipv6: str = ""
    ):
        isp_text = isp if isp else t("unknown")
        if len(isp_text) > 34:
            isp_text = isp_text[:33] + "…"
        ping_text = t("ping_ms", ms=ping_ms) if ping_ms is not None else "—"
        tz_text = timezone if timezone else "—"

        self.isp_label.setText(t("hover_isp", isp=isp_text))
        if iface:
            self.iface_label.setText(t("hover_iface", iface=iface))
            self.iface_label.show()
        else:
            self.iface_label.hide()

        if ipv6:
            shown_v6 = _mask_ipv6(ipv6) if is_private else ipv6
            if len(shown_v6) > 28:
                shown_v6 = shown_v6[:27] + "…"
            self.ipv6_label.setText(f"IPv6: {shown_v6}")
            self.ipv6_label.show()
        else:
            self.ipv6_label.hide()

        self.ping_label.setText(t("hover_ping", ping=ping_text))
        self.tz_label.setText(t("hover_tz", tz=tz_text))
        self.privacy_label.setText(t("hover_privacy"))
        self.privacy_label.setVisible(is_private)

        if is_light:
            bg, border, fg, accent = "rgba(255, 255, 255, 248)", "#cbd5e1", "#0f172a", "#2563eb"
        else:
            bg, border, fg, accent = "rgba(24, 24, 27, 248)", "#3f3f46", "#f4f4f5", "#60a5fa"

        self.box.setStyleSheet(f"""
            QWidget#hoverBox {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 10px;
            }}
            QLabel#detailRow {{
                color: {fg};
                font-family: "Segoe UI", sans-serif;
                font-size: 11px;
                font-weight: 500;
            }}
            QLabel#privacyRow {{
                color: {accent};
                font-family: "Segoe UI", sans-serif;
                font-size: 10.5px;
                font-weight: 600;
                padding-top: 2px;
            }}
        """)
        self.box.adjustSize()
        self.adjustSize()