from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import List, Dict


def _parse_hhmm(s: str) -> time:
    hh, mm = s.split(":")
    return time(hour=int(hh), minute=int(mm))


@dataclass
class DndWindow:
    start: time
    end: time

    def contains(self, t: time) -> bool:
        # supports overnight windows
        if self.start <= self.end:
            return self.start <= t <= self.end
        return (t >= self.start) or (t <= self.end)


class DndController:
    def __init__(self, settings):
        self.settings = settings
        self.enabled = bool(settings.cfg.get("dnd", {}).get("enabled", True))
        self.windows: List[DndWindow] = []

        for w in settings.cfg.get("dnd", {}).get("windows", []) or []:
            self.windows.append(DndWindow(start=_parse_hhmm(w["start"]), end=_parse_hhmm(w["end"])))

    def is_dnd_now(self, now: datetime | None = None) -> bool:
        if not self.enabled:
            return False
        if not self.windows:
            return False
        now = now or datetime.now()
        t = now.time()
        return any(w.contains(t) for w in self.windows)
