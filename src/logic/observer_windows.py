from __future__ import annotations

import sys
import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from typing import Optional

import psutil


@dataclass
class ActiveAppInfo:
    pid: int
    process_name: str


class WindowsActiveAppObserver:
    """Lightweight foreground-process observer.

    Uses Win32 APIs to get foreground window PID, then resolves process name via psutil.
    Does NOT capture screenshots.
    """

    def __init__(self):
        if sys.platform != "win32":
            raise RuntimeError("WindowsActiveAppObserver is only supported on Windows")

        self._user32 = ctypes.WinDLL("user32", use_last_error=True)

        self._GetForegroundWindow = self._user32.GetForegroundWindow
        self._GetForegroundWindow.argtypes = []
        self._GetForegroundWindow.restype = wintypes.HWND

        self._GetWindowThreadProcessId = self._user32.GetWindowThreadProcessId
        self._GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
        self._GetWindowThreadProcessId.restype = wintypes.DWORD

    def get_active_app(self) -> Optional[ActiveAppInfo]:
        hwnd = self._GetForegroundWindow()
        if not hwnd:
            return None

        pid = wintypes.DWORD(0)
        self._GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return None

        try:
            p = psutil.Process(pid.value)
            name = p.name()
        except Exception:
            return None

        return ActiveAppInfo(pid=pid.value, process_name=name)
