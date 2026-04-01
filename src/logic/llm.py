from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass
class LlmResult:
    text: str
    raw: Dict[str, Any]


class LlmClient:
    def __init__(self, *, base_url: str, api_key: str, model_name: str, timeout_seconds: float = 20.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def complete_openai_compat(
        self,
        *,
        prompt: str,
        temperature: float = 0.8,
        max_tokens: int = 80,
    ) -> LlmResult:
        """OpenAI-compatible /v1/completions."""
        url = f"{self.base_url}/v1/completions"
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }

        r = requests.post(url, headers=headers, json=payload, timeout=self.timeout_seconds)
        r.raise_for_status()
        data = r.json()

        text = ""
        try:
            # OpenAI-style completions
            text = (data.get("choices") or [{}])[0].get("text") or ""
        except Exception:
            text = ""

        return LlmResult(text=text.strip(), raw=data)

    def chat_ollama(
        self,
        *,
        prompt: str,
        temperature: float = 0.8,
        num_predict: int = 96,
    ) -> LlmResult:
        """Ollama /api/chat.

        Example:
          POST http://localhost:11434/api/chat
          {"model":"qwen3.5:0.8b","messages":[{"role":"user","content":"Hello"}],"stream":false}
        """
        url = f"{self.base_url}/api/chat"
        headers = {"Content-Type": "application/json"}

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "options": {
                "temperature": float(temperature),
                "num_predict": int(num_predict),
            },
        }

        r = requests.post(url, headers=headers, json=payload, timeout=self.timeout_seconds)
        r.raise_for_status()
        data = r.json()

        text = ""
        try:
            # Ollama returns { message: { content: "..." } }
            text = (data.get("message") or {}).get("content") or ""
        except Exception:
            text = ""

        return LlmResult(text=text.strip(), raw=data)
