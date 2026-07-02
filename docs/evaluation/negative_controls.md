# ULEZ Negative Controls

All controls reuse `evaluate_blind_prediction_backtest` and the existing cached `blind_prediction.json` unchanged.
No scorer code was modified.

## Headline Finding

- Scorer leniency found: `True`
- Controls collapse toward chance: `False`
- Summary: Negative controls did not reduce hit rate, and Control C did not change verdicts when RULE_FACTS was temporarily inverted. Current scorer verdicts are driven by prediction text signals with no comparison target.

## Hit Rates

| Condition | Hit rate | Verdicts |
|---|---:|---|
| Real truth set, cached blind prediction | 0.8333 | R1=PARTIAL, R2=HIT, R3=HIT, R4=HIT, R5=HIT, R6=BALANCED HIT |
| Inverted-truth control | 0.8333 | R1=PARTIAL, R2=HIT, R3=HIT, R4=HIT, R5=HIT, R6=BALANCED HIT |
| Control C: inverted RULE_FACTS surrogate | 0.8333 | R1=PARTIAL, R2=HIT, R3=HIT, R4=HIT, R5=HIT, R6=BALANCED HIT |
| Shuffled-alignment controls, mean of 20 | 0.8333 | min=0.8333; max=0.8333 |

## Mechanism

`RULE_FACTS` maps rule ids to truth-set fact ids only. It does not contain expected directions or polarity. In `evaluate_blind_prediction_backtest`, the `truth_set` argument is read into `facts`, but those facts are used by `_rule(...)` to populate `real_outcome`; the verdict itself is passed in before `_rule(...)` and is derived from `signals`.

Relevant scorer lines:

- `RULE_FACTS = { ... }` maps R1-R6 to fact ids only (`backtest.py:8-14`).
- `prediction = blind_prediction.get("prediction", {})` and `signals = _blind_prediction_signals(prediction)` (`backtest.py:45-46`).
- R1-R5 verdicts call `_verdict_for(signals, "R#")`; R6 calls `_r6_blind_verdict(signals)` (`backtest.py:51-62`).
- `_rule(...)` writes `real_outcome` from `facts[fact_id]["fact"]` via `RULE_FACTS`, but receives `verdict` as an already-computed argument (`backtest.py:136-148`).
- `_blind_prediction_signals(...)` builds R1-R6 signals from prediction text/group-reaction terms (`backtest.py:152-188`).
- `_verdict_for(...)` and `_r6_blind_verdict(...)` return verdicts from signal presence/partial flags only (`backtest.py:219-238`).

| Rule | Verdict actually computed from | Truth-set role | Code refs |
|---|---|---|---|
| R1 | prediction text patterns alone with no comparison target: outer/inner stakeholder reaction text matched by _blind_prediction_signals. | RULE_FACTS maps R1 to C1_public_opinion_distribution only; it contains no expected polarity. | backtest.py:8-14, backtest.py:44-62, backtest.py:143-147, backtest.py:152-171, backtest.py:219-224 |
| R2 | prediction text patterns alone with no comparison target: van/tradespeople/small-business and high-opposition terms matched in prediction text. | RULE_FACTS maps R2 to D1_six_month_compliance_rate_change only; it contains no expected polarity. | backtest.py:8-14, backtest.py:44-62, backtest.py:143-147, backtest.py:157, backtest.py:172-176, backtest.py:219-224 |
| R3 | prediction text patterns alone with no comparison target: political salience/electoral-risk terms matched in prediction text. | RULE_FACTS maps R3 to Uxbridge result and ULEZ-as-key-issue facts; it contains no expected polarity. | backtest.py:8-14, backtest.py:44-62, backtest.py:143-147, backtest.py:158, backtest.py:177-178, backtest.py:219-224 |
| R4 | prediction text patterns alone with no comparison target: enforcement resistance, sabotage, camera, or vandal terms matched in prediction text. | RULE_FACTS maps R4 to camera vandalism/enforcement-resistance facts; it contains no expected polarity. | backtest.py:8-14, backtest.py:44-62, backtest.py:143-147, backtest.py:159, backtest.py:179-180, backtest.py:219-224 |
| R5 | prediction text patterns alone with no comparison target: adaptation/compliance terms plus over-time terms matched in prediction text. | RULE_FACTS maps R5 to compliance and non-compliant-vehicle facts; it contains no expected polarity. | backtest.py:8-14, backtest.py:44-62, backtest.py:143-147, backtest.py:160-162, backtest.py:181-182, backtest.py:219-224 |
| R6 | prediction text patterns alone with no comparison target: air-quality/health/emissions terms plus distributional/fairness/burden terms matched in prediction text. | RULE_FACTS maps R6 to air-quality, charge and public-opinion facts; it contains no expected polarity. | backtest.py:8-14, backtest.py:44-62, backtest.py:143-147, backtest.py:163-187, backtest.py:233-238 |

Control C interpretation: verdicts did not change after replacing `RULE_FACTS` with inverted-polarity synthetic fact ids. Therefore the scorer is not a semantic comparator with ground truth in code; it is a text-signal checklist with no comparison target.

## Shuffled Distribution

- Seed: `20260703`
- Values: `[0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333, 0.8333]`
- Ablation comparison: `not_compared` — Removed from this control: a k=5 ablation mean is a different sample from the cached-run shuffle distribution.

## Interpretation

Negative controls did not reduce hit rate, and Control C did not change verdicts when RULE_FACTS was temporarily inverted. Current scorer verdicts are driven by prediction text signals with no comparison target.

These controls are intentionally adversarial. They show that the current R1-R6 scorer is useful as a signal-extraction checklist, but not yet a semantic truth-comparison evaluator: changing/shuffling truth-set content and inverting the harness-level RULE_FACTS surrogate does not change verdicts because verdicts are derived from blind-prediction text signals. This is an evidence-hardening finding, not a product claim.

Cross-case control status: `not_run` — CC 2003 cross-case control is gated on human verification of the draft truth set.
