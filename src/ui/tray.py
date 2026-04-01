from __future__ import annotations

from PySide6 import QtWidgets, QtGui, QtCore

from ..logic.dnd import DndController


def _default_tray_icon() -> QtGui.QIcon:
    # Ensure a non-null icon on Windows (standardIcon can be null on some setups).
    pm = QtGui.QPixmap(64, 64)
    pm.fill(QtCore.Qt.GlobalColor.transparent)
    p = QtGui.QPainter(pm)
    p.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    p.setBrush(QtGui.QColor(30, 30, 30, 220))
    p.setPen(QtCore.Qt.PenStyle.NoPen)
    p.drawEllipse(4, 4, 56, 56)
    p.setPen(QtGui.QPen(QtGui.QColor(245, 245, 245)))
    f = p.font()
    f.setBold(True)
    f.setPointSize(18)
    p.setFont(f)
    p.drawText(pm.rect(), QtCore.Qt.AlignmentFlag.AlignCenter, "摸")
    p.end()
    return QtGui.QIcon(pm)


class TrayController:
    def __init__(self, settings, pet_window, proactive_talker=None):
        self.settings = settings
        self.pet_window = pet_window
        self.proactive_talker = proactive_talker

        self.dnd = DndController(settings)

        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            # No tray support (or explorer not ready). We'll still run without tray.
            self.tray = None
            return

        icon = _default_tray_icon()
        self.tray = QtWidgets.QSystemTrayIcon(icon)
        self.tray.setToolTip(settings.cfg.get("app", {}).get("name", "Cyber Slacker"))

        menu = QtWidgets.QMenu()

        self.action_dnd = QtGui.QAction("勿扰：开")
        self.action_dnd.setCheckable(True)
        self.action_dnd.setChecked(self.dnd.enabled)
        self.action_dnd.triggered.connect(self._toggle_dnd)
        menu.addAction(self.action_dnd)

        self.action_click_through = QtGui.QAction("鼠标穿透")
        self.action_click_through.setCheckable(True)
        self.action_click_through.setChecked(self.pet_window.is_click_through())
        self.action_click_through.triggered.connect(self._toggle_click_through)
        menu.addAction(self.action_click_through)

        if self.proactive_talker is not None:
            menu.addSeparator()
            say_now = QtGui.QAction("现在说一句（测试）")
            say_now.triggered.connect(self.proactive_talker.trigger_once)
            menu.addAction(say_now)

        menu.addSeparator()

        quit_action = QtGui.QAction("退出")
        quit_action.triggered.connect(QtWidgets.QApplication.quit)
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_activated)

    def show(self):
        if self.tray is None:
            return
        self.tray.show()

    def _toggle_dnd(self):
        if self.tray is None:
            return
        self.dnd.enabled = self.action_dnd.isChecked()
        self.action_dnd.setText(f"勿扰：{'开' if self.dnd.enabled else '关'}")

    def _toggle_click_through(self):
        if self.tray is None:
            return
        enabled = self.action_click_through.isChecked()
        self.pet_window.set_click_through(enabled)

    def _on_activated(self, reason: QtWidgets.QSystemTrayIcon.ActivationReason):
        if self.tray is None:
            return
        # single click: toggle visibility
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Trigger:
            self.pet_window.setVisible(not self.pet_window.isVisible())
