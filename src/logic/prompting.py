from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .persona import Persona


@dataclass
class PromptContext:
    process_name: str
    category: str
    dnd_now: bool
    snark_level: int
    max_reply_chars: int
    # Random hook & time-of-day context to reduce repetition
    seed: int
    time_bucket: str
    topic_hook: str


def build_proactive_prompt(persona: Persona, ctx: PromptContext) -> str:
    """Build a short, robust Chinese prompt for tiny local models.

    Goal: avoid silent outputs and avoid overflowing tiny context windows.
    """
    persona_name = persona.meta.get("name", "赛博摸鱼搭子")
    tone = (
        (((persona.meta.get("style") or {}).get("tone")) if isinstance(persona.meta.get("style"), dict) else None)
        or ""
    )

    # Small local models may have tiny context windows; keep persona body bounded and simple.
    instructions = (persona.body or "").strip()
    if len(instructions) > 260:
        instructions = instructions[:260].rstrip()

    # Make it conversational & *explicitly* require a non-empty output.
    system_bits = [
        f"你叫{persona_name}。{('口吻：' + tone) if tone else ''}",
        "你在跟我聊天。必须回复一句中文，禁止空回复。",
        "只输出一句话，不要解释，不要列点。",
        f"长度≤{ctx.max_reply_chars}字。",
    ]

    situation_bits = [
        f"前台：{ctx.process_name or 'unknown'}（{ctx.category}）",
        f"时间段：{ctx.time_bucket}",
        f"钩子：{ctx.topic_hook}",
    ]

    # Add a fallback: if you don't知道说啥，也要按模板说。
    task = (
        "任务：基于上面信息吐槽/关怀一句。"
        "如果你不知道说什么，就直接输出：‘你吃了吗？’"
    )

    parts = [
        "\n".join(system_bits),
        instructions if instructions else "",
        "\n".join(situation_bits),
        task,
        "输出：",
    ]
    return "\n".join([p for p in parts if p])
