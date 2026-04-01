from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml


@dataclass
class Persona:
    meta: Dict[str, Any]
    body: str


def _parse_front_matter(text: str) -> Tuple[Dict[str, Any], str]:
    t = text.lstrip("\ufeff")
    if not t.startswith("---"):
        return {}, text

    parts = t.split("---", 2)
    if len(parts) < 3:
        return {}, text

    _, yaml_block, rest = parts
    meta = yaml.safe_load(yaml_block) or {}
    return meta, rest.strip()


def load_persona(agent_md_path: Path) -> Persona:
    if not agent_md_path.exists():
        return Persona(meta={}, body="")

    text = agent_md_path.read_text(encoding="utf-8")
    meta, body = _parse_front_matter(text)
    return Persona(meta=meta, body=body)
