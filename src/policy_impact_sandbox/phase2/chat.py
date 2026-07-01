from __future__ import annotations

from typing import Any


def answer_persona_question(agent: dict[str, Any], question: str) -> dict[str, str]:
    concerns = ", ".join(agent.get("concerns", []))
    stance = agent.get("stance", "mixed")
    action = agent.get("action_tendency", "explain policy impact concerns")
    answer = (
        f"As this archetype, I am {stance} because my main concerns are {concerns}. "
        f"My likely action is to {action}. I am responding as a synthetic archetype, not as a real person."
    )
    return {
        "agent_id": agent["id"],
        "question": question,
        "answer": answer,
        "safety_note": "persona chat uses archetype agents only and does not process real-person PII",
    }
