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
        # base_url should be the server root, e.g. http://localhost:11434 or https://cpa.oldbird.cn
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def _post(self, url: str, *, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        r = requests.post(url, headers=headers, json=payload, timeout=self.timeout_seconds)
        r.raise_for_status()
        return r.json()

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

        data = self._post(url, headers=headers, payload=payload)

        text = ""
        try:
            # OpenAI-style completions
            choice0 = (data.get("choices") or [{}])[0] or {}
            text = choice0.get("text") or ""
            # Some gateways accidentally return chat-like shape
            if not text:
                text = ((choice0.get("message") or {}).get("content")) or ""
        except Exception:
            text = ""

        return LlmResult(text=str(text).strip(), raw=data)

    def chat_ollama(
        self,
        *,
        prompt: str,
        temperature: float = 0.8,
        num_predict: int = 96,
        think: bool | None = None,
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
        # Ollama-specific: toggle "thinking" mode (some UIs/models may output only thinking or even blank content).
        # Your curl example uses: {"think": false}
        if think is not None:
            payload["think"] = bool(think)

        data = self._post(url, headers=headers, payload=payload)

        # Ollama sometimes returns an empty assistant message (e.g. context too long, model refusing,
        # or generation constrained). Keep extraction tolerant.
        text = ""
        try:
            msg = (data.get("message") or {})
            text = msg.get("content") or ""
            if not text:
                text = data.get("response") or ""  # /api/generate-style
            if not text:
                # OpenAI-chat style fallback
                text = (((data.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""

            # If still empty, surface some debug hints (kept in raw; caller prints keys only).
            # Some Ollama builds return a 'done_reason' like 'length'/'stop'.
            if not text:
                done_reason = data.get("done_reason")
                if done_reason and isinstance(done_reason, str):
                    text = ""  # keep empty; reason available in raw
        except Exception:
            text = ""

        return LlmResult(text=text.strip(), raw=data)
