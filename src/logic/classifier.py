from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ClassifiedApp:
    process_name: str
    category: str


class AppClassifier:
    def __init__(self, categories: Dict[str, List[str]] | None):
        self.categories = categories or {}
        # normalize for case-insensitive match
        self._map = {
            cat: {p.lower() for p in (procs or [])}
            for cat, procs in self.categories.items()
        }

    def classify(self, process_name: Optional[str]) -> ClassifiedApp:
        if not process_name:
            return ClassifiedApp(process_name="", category="unknown")
        pn = process_name.strip()
        low = pn.lower()
        for cat, procset in self._map.items():
            if low in procset:
                return ClassifiedApp(process_name=pn, category=cat)
        return ClassifiedApp(process_name=pn, category="other")
