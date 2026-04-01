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


def build_proactive_prompt(persona: Persona, ctx: PromptContext) -> str:
    # Keep it simple & robust for /v1/completions.
    persona_name = persona.meta.get("name", "赛博摸鱼搭子")
    tone = (((persona.meta.get("style") or {}).get("tone")) if isinstance(persona.meta.get("style"), dict) else None) or ""

    instructions = persona.body.strip()

    system_bits = [
        f"你叫{persona_name}。{('口吻：' + tone) if tone else ''}",
        "只输出一句中文短句，不要解释，不要列点。",
        f"长度≤{ctx.max_reply_chars}字。",
        f"嘴贱等级snark_level={ctx.snark_level}（0温柔~3火力全开，但禁止人身攻击）。",
    ]

    situation_bits = [
        "【上下文】",
        f"前台进程：{ctx.process_name or 'unknown'}",
        f"类别：{ctx.category}",
        f"勿扰中：{'是' if ctx.dnd_now else '否'}",
    ]

    # When DND is on, we shouldn't proactively talk (caller should skip). Still include for safety.
    task = "【任务】根据上下文吐槽/关怀一句，让人舒服点、想笑一下。"

    parts = [
        "\n".join(system_bits),
        ("\n" + instructions + "\n") if instructions else "",
        "\n".join(situation_bits),
        task,
        "输出：",
    ]
    return "\n".join([p for p in parts if p is not None and p != ""])
