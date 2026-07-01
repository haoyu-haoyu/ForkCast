from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from policy_impact_sandbox.phase1.graph import build_networkx_fallback


MISSING_STAKEHOLDERS: list[dict[str, Any]] = [
    {
        "id": "stakeholder_van_drivers_tradespeople",
        "name": "Van drivers, tradespeople and small businesses",
        "archetype_group": "affected_business",
        "stance_prior": "oppose",
        "interests": [
            "operating_cost",
            "daily_charge_burden_for_non_compliant_vans",
            "livelihood_impact",
            "vehicle_replacement_cost",
        ],
        "evidence_fact_ids": [
            "D1_six_month_compliance_rate_change",
            "A2_daily_charge",
        ],
        "evidence_note": "Vans have a lower six-month compliance rate than cars in the truth set, indicating heavier transition pressure for van-dependent workers and small businesses.",
    },
    {
        "id": "stakeholder_low_income_households",
        "name": "Low-income households dependent on private vehicles",
        "archetype_group": "affected_public",
        "stance_prior": "oppose",
        "interests": [
            "vehicle_replacement_affordability",
            "policy_fairness",
            "distributional_burden",
            "vehicle_dependence",
        ],
        "evidence_fact_ids": [
            "A2_daily_charge",
            "C1_public_opinion_distribution",
            "D3_air_quality_and_emissions_changes",
        ],
        "evidence_note": "The case graph models distributional pain alongside air-quality benefits: the daily charge and outer-London opposition evidence anchor burden concerns, while air-quality evidence anchors benefits.",
    },
]


def augment_missing_stakeholders(case_graph: dict[str, Any]) -> dict[str, Any]:
    augmented = deepcopy(case_graph)
    existing_ids = {stakeholder["id"] for stakeholder in augmented.get("stakeholders", [])}
    for stakeholder in MISSING_STAKEHOLDERS:
        if stakeholder["id"] not in existing_ids:
            augmented.setdefault("stakeholders", []).append(deepcopy(stakeholder))

    augmented["augmented_at"] = datetime.now(timezone.utc).isoformat()
    augmented["augmentation_notes"] = [
        "Added van drivers/tradespeople/small businesses as a distinct high-impact affected_business group.",
        "Added low-income households as a distinct affected_public group for distributional burden analysis.",
    ]
    augmented["graph"] = build_networkx_fallback(augmented)
    return augmented
