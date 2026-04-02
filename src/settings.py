from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


@dataclass
class Settings:
    base_dir: Path
    env: Dict[str, str]
    cfg: Dict[str, Any]


def _read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_settings(base_dir: Path) -> Settings:
    # 1) env
    load_dotenv(base_dir / ".env")
    env = {
        # Endpoint root (no trailing /v1)
        "BASE_URL": os.getenv("BASE_URL", "http://localhost:11434"),
        "API_KEY": os.getenv("API_KEY", ""),
        "MODEL_NAME": os.getenv("MODEL_NAME", "qwen3.5:0.8b"),
        "HTTP_TIMEOUT_SECONDS": os.getenv("HTTP_TIMEOUT_SECONDS", "20"),
        # Adapter override (optional):
        # - ollama_chat / ollama   -> POST {BASE_URL}/api/chat
        # - completions / openai_compat -> POST {BASE_URL}/v1/completions
        "LLM_ADAPTER": os.getenv("LLM_ADAPTER", ""),
    }

    # 2) yaml config (user config.yaml overrides example)
    cfg = _read_yaml(base_dir / "config.yaml")
    if not cfg:
        cfg = _read_yaml(base_dir / "config.example.yaml")

    return Settings(base_dir=base_dir, env=env, cfg=cfg)
