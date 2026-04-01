from __future__ import annotations

import sys

from PySide6 import QtWidgets, QtCore, QtGui


# Win32 click-through support is Windows-only.
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    GetWindowLongW = user32.GetWindowLongW
    SetWindowLongW = user32.SetWindowLongW
    GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
    GetWindowLongW.restype = ctypes.c_long
    SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
    SetWindowLongW.restype = ctypes.c_long
else:
    GetWindowLongW = None
    SetWindowLongW = None
    GWL_EXSTYLE = 0
    WS_EX_LAYERED = 0
    WS_EX_TRANSPARENT = 0


class PetWindow(QtWidgets.QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings

        self.setWindowTitle(settings.cfg.get("app", {}).get("name", "Cyber Slacker"))

        flags = QtCore.Qt.WindowType.Tool | QtCore.Qt.WindowType.FramelessWindowHint
        flags |= QtCore.Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

        # Transparent background
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._drag_offset = None

        # Avatar (image) label
        self.label = QtWidgets.QLabel("")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("QLabel { background: transparent; }")

        ui_cfg = (settings.cfg.get("ui", {}) or {})
        avatar_path = ui_cfg.get("avatar_path")

        self._pixmap = None
        if avatar_path:
            p = QtGui.QPixmap(str(settings.base_dir / str(avatar_path)))
            if not p.isNull():
                self._pixmap = p

        if self._pixmap is None:
            # Fallback placeholder
            self.label.setText("摸")
            self.label.setStyleSheet(
                "QLabel { color: white; font-size: 18px; font-weight: 700; background: transparent; }"
            )

        # Window size follows avatar (bounded), else default 90x90
        if self._pixmap is not None:
            target_w = int(ui_cfg.get("avatar_width", 90))
            target_h = int(ui_cfg.get("avatar_height", 90))
            self.setFixedSize(target_w, target_h)
            self._apply_pixmap()
            # Click region matches image rect (no mask)
        else:
            self.setFixedSize(90, 90)
            # Make window hit-test region roughly circular (helps avoid a visible square boundary on some setups)
            try:
                self.setMask(
                    QtGui.QRegion(
                        QtCore.QRect(0, 0, self.width(), self.height()),
                        QtGui.QRegion.RegionType.Ellipse,
                    )
                )
            except Exception:
                pass

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.label)

        pos = settings.cfg.get("ui", {}).get("start_position", {})
        self.move(int(pos.get("x", 30)), int(pos.get("y", 30)))

        self._click_through = False
        default_ct = settings.cfg.get("ui", {}).get("click_through_default", True)
        QtCore.QTimer.singleShot(0, lambda: self.set_click_through(bool(default_ct)))

    def _apply_pixmap(self):
        if self._pixmap is None:
            return
        scaled = self._pixmap.scaled(
            self.size(),
            QtCore.Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        # center-crop
        x = max(0, (scaled.width() - self.width()) // 2)
        y = max(0, (scaled.height() - self.height()) // 2)
        cropped = scaled.copy(x, y, self.width(), self.height())
        self.label.setPixmap(cropped)

    def resizeEvent(self, event: QtGui.QResizeEvent):
        super().resizeEvent(event)
        self._apply_pixmap()

    def paintEvent(self, event):
        # If using an avatar image, let the pixmap be the visual.
        if self._pixmap is not None:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setBrush(QtGui.QColor(30, 30, 30, 180))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        if self._drag_offset is not None and event.buttons() & QtCore.Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        self._drag_offset = None

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):
        # Double click toggles click-through for convenience
        self.set_click_through(not self._click_through)

    def set_click_through(self, enabled: bool) -> None:
        self._click_through = enabled
        if sys.platform != "win32" or GetWindowLongW is None or SetWindowLongW is None:
            return
        hwnd = int(self.winId())
        ex_style = GetWindowLongW(hwnd, GWL_EXSTYLE)
        if enabled:
            ex_style = ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT
        else:
            ex_style = ex_style & (~WS_EX_TRANSPARENT)
        SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

    def is_click_through(self) -> bool:
        return self._click_through
