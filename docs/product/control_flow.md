# Human-in-the-Loop Control Flow

The Phase 3 dashboard implements four approval checkpoints:

1. Extraction review: stakeholders and assumptions are visible. The user can approve, reject, add stakeholders, or remove stakeholders.
2. Agent review: archetype composition, initial stance and adaptation capacity are visible. The user can disable personas and adjust group sliders.
3. Simulation config: agent count, rounds, budget cap and seed lock are visible. The user can approve run, downscale, replay cached run, or run a small live sample.
4. Report and chain review: report claims, blind backtest evidence and audit manifest are visible. The Kaspa anchor is inspectable and still cannot auto-send.

Every approval creates a checkpoint event. Rollback marks the latest approved checkpoint as `superseded` and preserves the old record in the UI history.

Hard limits enforced in the UI:

- no automatic chain action
- no automatic stakeholder weight changes
- no real-person PII
- archetypes only
- decision support only

The dashboard uses cached Phase 2 artifacts for replay resilience. Backtest credibility is explicitly tied to `blind_prediction.json`, while mock simulation events are presented only as a dashboard visualization aid. The Phase 4 Kaspa panel displays the real TN-10 transaction hash when available, but future chain actions still require checkpoint-4 approval.
