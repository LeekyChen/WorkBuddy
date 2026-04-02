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
        # - ollama_chat / ollama        -> POST {BASE_URL}/api/chat
        # - completions / openai_compat -> POST {BASE_URL}/v1/completions
        "LLM_ADAPTER": os.getenv("LLM_ADAPTER", ""),
        # Debug logging (NEVER prints API_KEY; may print prompt/context)
        "LLM_LOG_PROMPT": os.getenv("LLM_LOG_PROMPT", "0"),
        "LLM_LOG_PROMPT_MAX_CHARS": os.getenv("LLM_LOG_PROMPT_MAX_CHARS", "4000"),
        "LLM_LOG_RESPONSE": os.getenv("LLM_LOG_RESPONSE", "0"),
        "LLM_LOG_RESPONSE_MAX_CHARS": os.getenv("LLM_LOG_RESPONSE_MAX_CHARS", "8000"),

        # Ollama-specific: whether to enable "thinking" mode.
        # When think=true, some models/UIs may produce long reasoning or even blank user-visible output.
        # Default: false.
        "OLLAMA_THINK": os.getenv("OLLAMA_THINK", "0"),
    }

    # 2) yaml config (user config.yaml overrides example)
    cfg = _read_yaml(base_dir / "config.yaml")
    if not cfg:
        cfg = _read_yaml(base_dir / "config.example.yaml")

    return Settings(base_dir=base_dir, env=env, cfg=cfg)
