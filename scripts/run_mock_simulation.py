from __future__ import annotations

import argparse
import json
from pathlib import Path

from policy_impact_sandbox.simulation.mock import generate_mock_simulation


DEFAULT_AGENTS = [
    {
        "id": "agent_outer_london_driver_001",
        "archetype": "outer_london_low_income_driver",
        "stance": "against",
        "concerns": ["daily_charge", "vehicle_replacement_cost", "fairness"],
    },
    {
        "id": "agent_asthma_parent_001",
        "archetype": "parent_of_child_with_asthma",
        "stance": "support",
        "concerns": ["air_quality", "children_health", "school_routes"],
    },
    {
        "id": "agent_small_business_001",
        "archetype": "small_business_van_operator",
        "stance": "against",
        "concerns": ["operating_cost", "scrappage_access", "customer_coverage"],
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Phase 0 mock simulation fallback.")
    parser.add_argument("--output", default="runs/phase0_mock/simulation_events.json")
    parser.add_argument("--rounds", type=int, default=2)
    args = parser.parse_args()

    result = generate_mock_simulation(
        agents=DEFAULT_AGENTS,
        config={
            "case_id": "ulez_2023_expansion",
            "run_id": "phase0_mock",
            "rounds": args.rounds,
            "random_seed": 20260701,
        },
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote mock simulation output: {output_path}")
    print(f"Events: {len(result['events'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
