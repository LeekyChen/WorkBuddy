from __future__ import annotations

import ctypes
from ctypes import wintypes

from PySide6 import QtWidgets, QtCore, QtGui


# Win32 constants
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

        # Simple placeholder: a colored circle + text
        self.label = QtWidgets.QLabel("摸")
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(
            "QLabel { color: white; font-size: 18px; font-weight: 700; }"
        )

        self.setFixedSize(90, 90)

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.label)

        pos = settings.cfg.get("ui", {}).get("start_position", {})
        self.move(int(pos.get("x", 30)), int(pos.get("y", 30)))

        self._click_through = False
        default_ct = settings.cfg.get("ui", {}).get("click_through_default", True)
        QtCore.QTimer.singleShot(0, lambda: self.set_click_through(bool(default_ct)))

    def paintEvent(self, event):
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
        hwnd = int(self.winId())
        ex_style = GetWindowLongW(hwnd, GWL_EXSTYLE)
        if enabled:
            ex_style = ex_style | WS_EX_LAYERED | WS_EX_TRANSPARENT
        else:
            ex_style = ex_style & (~WS_EX_TRANSPARENT)
        SetWindowLongW(hwnd, GWL_EXSTYLE, ex_style)

    def is_click_through(self) -> bool:
        return self._click_through
