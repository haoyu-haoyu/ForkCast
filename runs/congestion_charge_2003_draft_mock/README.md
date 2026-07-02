# London Congestion Charge 2003 Draft Mock Run

Status: DRAFT — PENDING HUMAN VERIFICATION

This run is a plumbing test only. It proves that the Phase 2 pipeline can accept a second case graph and produce agents, a blind-prediction artifact, mock simulation events, a report, a backtest-shaped artifact, and an audit manifest.

The ground-truth entries in `data/cases/congestion_charge_2003/truth_set.json` are not yet verified. Because `headline_excluded=true`, `backtest_result.json` intentionally marks every R1-R6 rule as `NOT_SCORED`.

Do not include this case in headline hit-rate, robustness, ablation, or demo credibility numbers until a human verifies the source quotes and writes a case-specific rubric.
