from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import random
from typing import Any


DECISION_SUPPORT_DISCLAIMER = "simulation is decision support, not deterministic forecast"


def _event_id(run_id: str, round_index: int, agent_id: str, event_type: str) -> str:
    raw = f"{run_id}:{round_index}:{agent_id}:{event_type}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def generate_mock_simulation(agents: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    """Generate deterministic synthetic event logs with the same contract as a live simulation."""
    case_id = str(config.get("case_id", "unknown_case"))
    rounds = int(config.get("rounds", 1))
    random_seed = int(config.get("random_seed", 20260701))
    run_id = str(config.get("run_id", f"{case_id}_mock"))
    rng = random.Random(random_seed)

    events: list[dict[str, Any]] = []
    base_time = datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc).isoformat()

    for round_index in range(1, rounds + 1):
        for agent in agents:
            agent_id = str(agent["id"])
            stance = agent.get("stance", "uncertain")
            concerns = list(agent.get("concerns", ["cost", "fairness", "air_quality"]))
            concern = rng.choice(concerns)

            post_type = "post" if round_index == 1 else "comment"
            events.append(
                {
                    "event_id": _event_id(run_id, round_index, agent_id, post_type),
                    "run_id": run_id,
                    "case_id": case_id,
                    "round": round_index,
                    "agent_id": agent_id,
                    "agent_archetype": agent.get("archetype", "unknown_archetype"),
                    "type": post_type,
                    "stance": stance,
                    "topic": concern,
                    "content": (
                        f"{agent.get('archetype', 'archetype')} raises {concern} "
                        f"concerns about {case_id}."
                    ),
                    "created_at": base_time,
                }
            )

            if round_index == rounds:
                delta = rng.choice([-1, 0, 1])
                events.append(
                    {
                        "event_id": _event_id(run_id, round_index, agent_id, "stance_change"),
                        "run_id": run_id,
                        "case_id": case_id,
                        "round": round_index,
                        "agent_id": agent_id,
                        "agent_archetype": agent.get("archetype", "unknown_archetype"),
                        "type": "stance_change",
                        "from_stance": stance,
                        "to_stance": _shift_stance(stance, delta),
                        "reason": f"mock interaction pressure on {concern}",
                        "created_at": base_time,
                    }
                )

    return {
        "case_id": case_id,
        "run_id": run_id,
        "mode": "mock",
        "events": events,
        "metadata": {
            "agent_count": len(agents),
            "rounds": rounds,
            "random_seed": random_seed,
            "disclaimer": DECISION_SUPPORT_DISCLAIMER,
        },
    }


def _shift_stance(stance: str, delta: int) -> str:
    order = ["strongly_against", "against", "uncertain", "support", "strongly_support"]
    if stance not in order:
        return stance
    index = max(0, min(len(order) - 1, order.index(stance) + delta))
    return order[index]
