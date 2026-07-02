# ULEZ Negative Controls

All controls reuse `evaluate_blind_prediction_backtest` and the existing cached `blind_prediction.json` unchanged.
No scorer code was modified.

## Headline Finding

- Scorer leniency found: `True`
- Controls collapse toward chance: `False`
- Summary: Negative controls did not reduce hit rate; current scorer verdicts are driven by prediction text signals and not by semantic comparison against truth-set content.

## Hit Rates

| Condition | Hit rate | Verdicts |
|---|---:|---|
| Real truth set, cached blind prediction | 0.8333 | R1=PARTIAL, R2=HIT, R3=HIT, R4=HIT, R5=HIT, R6=BALANCED HIT |
| Inverted-truth control | 0.8333 | R1=PARTIAL, R2=HIT, R3=HIT, R4=HIT, R5=HIT, R6=BALANCED HIT |
| Shuffled-alignment controls, mean of 20 | 0.8333 | min=0.8333; max=0.8333 |

## Shuffled Distribution

- Seed: `20260703`
- Values: `[0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333]`
- Real ablation full-pipeline mean hit rate: `0.7333`
- Position of real rate in permutation distribution: `{"count_greater_or_equal": 20, "count_less_or_equal": 0, "percentile_less_or_equal": 0.0, "permutation_count": 20, "real_rate": 0.7333}`

## Interpretation

These controls are intentionally adversarial. They show that the current R1-R6 scorer is useful as a signal-extraction checklist, but not yet a semantic truth-comparison evaluator: changing or shuffling the truth-set content does not change verdicts because verdicts are derived from blind-prediction text signals. This is an evidence-hardening finding, not a product claim.

Cross-case control status: `not_run` — CC 2003 cross-case control is gated on human verification of the draft truth set.
