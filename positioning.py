from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QPoint, QRect


def mask_ip_address(ip: str) -> str:
    if not ip:
        return ip
    if "." in ip:
        parts = ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.•••.•••"
    if ":" in ip:
        parts = [p for p in ip.split(":") if p]
        if len(parts) >= 2:
            return f"{parts[0]}:{parts[1]}:••••:••••"
    return "•••.•••.•••.•••"


def snap_to_edges(raw_x: int, raw_y: int, w: int, h: int) -> QPoint:
    screen = QApplication.screenAt(QPoint(raw_x + w // 2, raw_y + h // 2)) or QApplication.primaryScreen()
    if not screen:
        return QPoint(raw_x, raw_y)

    geo = screen.availableGeometry()
    margin = 6
    snap_dist = 18

    min_x, max_x = geo.left() + margin, geo.right() - w - margin
    min_y, max_y = geo.top() + margin, geo.bottom() - h - margin

    x = max(min_x, min(raw_x, max_x))
    y = max(min_y, min(raw_y, max_y))

    if abs(x - min_x) <= snap_dist:
        x = min_x
    elif abs(x - max_x) <= snap_dist:
        x = max_x

    if abs(y - min_y) <= snap_dist:
        y = min_y
    elif abs(y - max_y) <= snap_dist:
        y = max_y

    return QPoint(x, y)


def calculate_widget_pos(cfg: dict, w: int, h: int, old_w: int = 0, old_h: int = 0) -> QPoint:
    screen = QApplication.primaryScreen()
    if not screen:
        return QPoint(0, 0)

    geo = screen.availableGeometry()
    margin = 6
    pos = cfg.get("position", "bottom-right")

    if pos == "custom" and cfg.get("custom_x") is not None and cfg.get("custom_y") is not None:
        cx, cy = int(cfg["custom_x"]), int(cfg["custom_y"])
        if old_w > 0 and abs((cx + old_w) - (geo.right() - margin)) <= 4:
            cx = geo.right() - w - margin
        if old_h > 0 and abs((cy + old_h) - (geo.bottom() - margin)) <= 4:
            cy = geo.bottom() - h - margin
        return snap_to_edges(cx, cy, w, h)

    x = (geo.left() + margin) if pos.endswith("left") else (geo.right() - w - margin)
    y = (geo.top() + margin) if pos.startswith("top") else (geo.bottom() - h - margin)
    return QPoint(x, y)


def calculate_hover_card_pos(w_geo: QRect, c_w: int, c_h: int, fallback_pos: str) -> QPoint:
    screen = QApplication.screenAt(w_geo.center()) or QApplication.primaryScreen()
    if screen:
        s_geo = screen.availableGeometry()
        show_below = w_geo.center().y() < s_geo.center().y()
        align_left = w_geo.center().x() < s_geo.center().x()
    else:
        show_below = fallback_pos.startswith("top")
        align_left = fallback_pos.endswith("left")

    y = (w_geo.bottom() - 4) if show_below else (w_geo.top() - c_h + 4)
    x = w_geo.left() if align_left else (w_geo.right() - c_w)
    return QPoint(x, y)


def calculate_dialog_pos(w_geo: QRect, d_w: int, d_h: int) -> QPoint:
    screen = QApplication.screenAt(w_geo.center()) or QApplication.primaryScreen()
    if not screen:
        return QPoint(100, 100)

    s_geo = screen.availableGeometry()
    margin = 8
    x = (w_geo.right() - d_w) if w_geo.center().x() > s_geo.center().x() else w_geo.left()
    x = max(s_geo.left() + margin, min(x, s_geo.right() - d_w - margin))

    if w_geo.top() - d_h - margin >= s_geo.top():
        y = w_geo.top() - d_h - margin
    else:
        y = min(w_geo.bottom() + margin, s_geo.bottom() - d_h - margin)

    return QPoint(x, y)