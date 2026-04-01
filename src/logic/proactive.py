from __future__ import annotations

import random
import sys
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6 import QtCore

from .classifier import AppClassifier
from .dnd import DndController
from .llm import LlmClient
from .persona import load_persona
from .prompting import PromptContext, build_proactive_prompt


@dataclass
class ProactiveTalkConfig:
    enabled: bool
    min_minutes: int
    max_minutes: int


class ProactiveTalker(QtCore.QObject):
    say = QtCore.Signal(str)
    debug = QtCore.Signal(str)

    def __init__(self, settings, active_app_getter):
        super().__init__()
        self.settings = settings
        self.active_app_getter = active_app_getter

        cfg = settings.cfg.get("proactive_talk", {}) or {}
        self.cfg = ProactiveTalkConfig(
            enabled=bool(cfg.get("enabled", True)),
            min_minutes=int(cfg.get("interval_min_minutes", 45)),
            max_minutes=int(cfg.get("interval_max_minutes", 90)),
        )
        self.startup_delay_seconds = int(cfg.get("startup_delay_seconds", 12))

        self.dnd = DndController(settings)
        self.classifier = AppClassifier((settings.cfg.get("apps", {}) or {}).get("categories", {}))

        persona_cfg = settings.cfg.get("persona", {}) or {}
        agent_md_path = Path(settings.base_dir) / str(persona_cfg.get("agent_md_path", "AGENT.md"))
        self.persona = load_persona(agent_md_path)

        self.snark_level = int(persona_cfg.get("snark_level", 2))
        self.max_reply_chars = int(persona_cfg.get("max_reply_chars", 60))

        model_cfg = settings.cfg.get("model", {}) or {}
        self.adapter = str(model_cfg.get("adapter", "ollama"))
        self.temperature = float(model_cfg.get("temperature", 0.8))

        timeout = float(settings.env.get("HTTP_TIMEOUT_SECONDS", "20") or "20")
        self.llm = LlmClient(
            base_url=str(settings.env.get("BASE_URL", "")).strip(),
            api_key=str(settings.env.get("API_KEY", "")),
            model_name=str(settings.env.get("MODEL_NAME", "")),
            timeout_seconds=timeout,
        )

        self._timer = QtCore.QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._on_timeout)

        self._inflight = False
        self._stopping = False

    def start(self):
        if not self.cfg.enabled:
            return
        # Schedule a quick first utterance so users can see it works.
        if self.startup_delay_seconds > 0:
            self.debug.emit(f"startup_delay: {self.startup_delay_seconds}s")
            QtCore.QTimer.singleShot(self.startup_delay_seconds * 1000, self.trigger_once)
        self._schedule_next("startup")

    def trigger_once(self):
        """Manual/test trigger (still respects DND by default)."""
        self._do_one(reschedule=False)

    def stop(self):
        """Stop scheduling new calls.

        In-flight HTTP calls cannot be forcibly killed; we run them in daemon threads so app exit won't hang.
        """
        self._stopping = True
        try:
            self._timer.stop()
        except Exception:
            pass

    def _schedule_next(self, reason: str):
        lo = max(1, self.cfg.min_minutes)
        hi = max(lo, self.cfg.max_minutes)
        minutes = random.randint(lo, hi)
        ms = minutes * 60 * 1000
        self.debug.emit(f"schedule_next: {minutes}min ({reason})")
        self._timer.start(ms)

    def _on_timeout(self):
        # Always reschedule first to keep it alive even if something fails.
        self._schedule_next("tick")
        self._do_one(reschedule=False)

    def _do_one(self, *, reschedule: bool):
        if self.dnd.is_dnd_now(datetime.now()):
            self.debug.emit("skip proactive: DND")
            return

        # Gather context
        info = None
        try:
            info = self.active_app_getter()
        except Exception:
            info = None

        process_name = getattr(info, "process_name", "") if info else ""
        classified = self.classifier.classify(process_name)

        ctx = PromptContext(
            process_name=classified.process_name,
            category=classified.category,
            dnd_now=False,
            snark_level=self.snark_level,
            max_reply_chars=self.max_reply_chars,
        )
        prompt = build_proactive_prompt(self.persona, ctx)

        def _call_llm() -> str:
            if self.adapter != "openai_compat":
                raise RuntimeError(f"Unsupported model.adapter: {self.adapter}")
            # max_tokens is a rough bound; we also hard-trim by chars later.
            res = self.llm.complete_openai_compat(prompt=prompt, temperature=self.temperature, max_tokens=96)
            return (res.text or "").strip()

        self._run_in_thread(_call_llm)

    def _run_in_thread(self, fn):
        # one in-flight request at a time
        if self._stopping:
            return
        if self._inflight:
            self.debug.emit("skip proactive: inflight")
            return

        self._inflight = True

        def _runner():
            try:
                text = fn()

                def _deliver_ok():
                    try:
                        t = (text or "").strip().replace("\n", " ")
                        if len(t) > self.max_reply_chars:
                            t = t[: self.max_reply_chars].rstrip()
                        if t:
                            self.say.emit(t)
                        else:
                            self.debug.emit("llm empty")
                    finally:
                        self._inflight = False

                QtCore.QTimer.singleShot(0, _deliver_ok)
            except Exception as e:

                def _deliver_err():
                    try:
                        self.debug.emit(f"llm failed: {e}")
                    finally:
                        self._inflight = False

                QtCore.QTimer.singleShot(0, _deliver_err)

        th = threading.Thread(target=_runner, daemon=True)
        th.start()
