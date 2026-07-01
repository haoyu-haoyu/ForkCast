from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from typing import Any

from policy_impact_sandbox.simulation.mock import DECISION_SUPPORT_DISCLAIMER


def run_policy_mock_simulation(
    agents_payload: dict[str, Any],
    run_id: str,
    rounds: int = 3,
) -> dict[str, Any]:
    agents = agents_payload["agents"]
    events: list[dict[str, Any]] = []
    for round_index in range(1, rounds + 1):
        for agent in agents:
            event_type = "post" if round_index == 1 else "comment"
            stance = _stance_for_round(agent, round_index, rounds)
            events.append(
                {
                    "event_id": _event_id(run_id, round_index, agent["id"], event_type),
                    "run_id": run_id,
                    "case_id": agents_payload["case_id"],
                    "round": round_index,
                    "agent_id": agent["id"],
                    "stakeholder_id": agent["stakeholder_id"],
                    "agent_archetype": agent["archetype"],
                    "type": event_type,
                    "stance": stance,
                    "topic": _topic_for(agent, round_index),
                    "content": _content_for(agent, stance, round_index, rounds),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            if round_index == rounds and agent["stance"] in {"oppose", "strongly_oppose"}:
                to_stance = _adapted_stance(agent)
                events.append(
                    {
                        "event_id": _event_id(run_id, round_index, agent["id"], "stance_change"),
                        "run_id": run_id,
                        "case_id": agents_payload["case_id"],
                        "round": round_index,
                        "agent_id": agent["id"],
                        "stakeholder_id": agent["stakeholder_id"],
                        "agent_archetype": agent["archetype"],
                        "type": "stance_change",
                        "from_stance": agent["stance"],
                        "to_stance": to_stance,
                        "reason": _adaptation_reason(agent, to_stance),
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )

    signals = _derive_signals(agents, events)
    return {
        "case_id": agents_payload["case_id"],
        "run_id": run_id,
        "mode": "mock",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "events": events,
        "signals": signals,
        "metadata": {
            "agent_count": len(agents),
            "rounds": rounds,
            "disclaimer": DECISION_SUPPORT_DISCLAIMER,
            "oasis_live": False,
        },
    }


def _event_id(run_id: str, round_index: int, agent_id: str, event_type: str) -> str:
    return hashlib.sha256(f"{run_id}:{round_index}:{agent_id}:{event_type}".encode("utf-8")).hexdigest()[:16]


def _topic_for(agent: dict[str, Any], round_index: int) -> str:
    concerns = agent.get("concerns") or ["policy_impact"]
    return concerns[(round_index - 1) % len(concerns)]


def _stance_for_round(agent: dict[str, Any], round_index: int, rounds: int) -> str:
    if round_index < rounds:
        return agent["stance"]
    if agent["stance"] in {"oppose", "strongly_oppose"} and agent.get("adaptation_capacity") in {"medium", "high"}:
        return "mixed_adapting"
    return agent["stance"]


def _content_for(agent: dict[str, Any], stance: str, round_index: int, rounds: int) -> str:
    stakeholder_id = agent["stakeholder_id"]
    topic = _topic_for(agent, round_index)
    if stakeholder_id == "stakeholder_van_drivers_tradespeople":
        return f"{agent['archetype']} says {topic} makes the policy one of the hardest shocks for van-dependent work."
    if stakeholder_id == "stakeholder_low_income_households":
        return f"{agent['archetype']} frames {topic} as a fairness and affordability burden."
    if stakeholder_id == "stakeholder_outer_london_residents":
        return f"{agent['archetype']} shows stronger outer-London backlash around {topic}."
    if stakeholder_id == "stakeholder_inner_london_residents":
        return f"{agent['archetype']} supports the air-quality rationale while watching implementation fairness."
    if round_index == rounds and stance == "mixed_adapting":
        return f"{agent['archetype']} remains concerned but starts adapting behaviour over time."
    return f"{agent['archetype']} discusses {topic} with stance {stance}."


def _adapted_stance(agent: dict[str, Any]) -> str:
    capacity = agent.get("adaptation_capacity")
    if capacity in {"medium", "high"}:
        return "mixed_adapting"
    if agent["stance"] == "strongly_oppose":
        return "oppose"
    return agent["stance"]


def _adaptation_reason(agent: dict[str, Any], to_stance: str) -> str:
    if to_stance == "mixed_adapting":
        return "short-term opposition persists while compliance behaviour gradually adjusts"
    return "low adaptation capacity keeps economic pressure high"


def _derive_signals(agents: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, str]:
    stakeholder_ids = {agent["stakeholder_id"] for agent in agents}
    adapting = any(event.get("to_stance") == "mixed_adapting" for event in events)
    return {
        "outer_london_backlash": "strong" if "stakeholder_outer_london_residents" in stakeholder_ids else "absent",
        "inner_london_support": "present" if "stakeholder_inner_london_residents" in stakeholder_ids else "absent",
        "van_tradespeople_pressure": "high" if "stakeholder_van_drivers_tradespeople" in stakeholder_ids else "absent",
        "low_income_distributional_burden": "present" if "stakeholder_low_income_households" in stakeholder_ids else "absent",
        "political_salience": "top_risk" if {"stakeholder_conservative_party", "stakeholder_labour_party"} & stakeholder_ids else "absent",
        "enforcement_backlash": "present" if "stakeholder_ulez_opponents_radical" in stakeholder_ids else "absent",
        "behavioural_adaptation": "present" if adapting else "absent",
        "air_quality_benefit": "present" if {"stakeholder_inner_london_residents", "stakeholder_london_mayor"} & stakeholder_ids else "absent",
        "distributional_burden": "present"
        if {"stakeholder_low_income_households", "stakeholder_van_drivers_tradespeople"} & stakeholder_ids
        else "absent",
    }
