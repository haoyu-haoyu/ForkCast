Generate synthetic archetype agent profiles for a policy impact simulation.

Return one JSON object with key "agents" and no prose.
All agents must be archetypes. Do not include real person names, contact details, addresses, or other PII.
Do not say that agents can send blockchain transactions or change stakeholder weights.

Each agent object should contain:
- id
- stakeholder_id
- archetype
- persona
- stance
- action_tendency
- concerns
- evidence_fact_ids
- adaptation_capacity

The output should cover every stakeholder group in the supplied case_graph. If and only if the supplied case is ULEZ,
emphasize these ULEZ-relevant groups:
- outer London vehicle-dependent residents
- inner London supporters
- van drivers / tradespeople / small businesses
- low-income households

For any other policy, do not introduce ULEZ-specific groups unless they appear in the supplied stakeholders.

Use qualitative stances only. Do not predict exact historical percentages or election results.
