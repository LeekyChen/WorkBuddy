from __future__ import annotations

from PySide6 import QtWidgets, QtCore, QtGui


class BubbleWindow(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        flags = QtCore.Qt.WindowType.Tool | QtCore.Qt.WindowType.FramelessWindowHint
        flags |= QtCore.Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.label = QtWidgets.QLabel("")
        self.label.setWordWrap(True)
        self.label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label.setStyleSheet(
            "QLabel {"
            "  color: #f5f5f5;"
            "  background-color: rgba(20,20,20,210);"
            "  border-radius: 10px;"
            "  padding: 8px 10px;"
            "  font-size: 13px;"
            "}"
        )

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.label)

        self._hide_timer = QtCore.QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    def show_text_near(self, text: str, anchor: QtWidgets.QWidget, *, ms: int = 4500):
        self.label.setText(text)
        self.adjustSize()

        # Position: above-right of anchor
        g = anchor.geometry()
        top_left = anchor.mapToGlobal(g.topLeft())
        x = top_left.x() + anchor.width() + 8
        y = top_left.y() - self.height() + 8
        self.move(x, y)

        self.show()
        self.raise_()
        self._hide_timer.start(ms)
