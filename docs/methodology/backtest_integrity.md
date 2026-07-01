# Backtest Integrity: Blind Prediction Design

This project separates prediction generation from historical outcome verification.
The backtest is not scored against mock simulation events. Mock events are only used to make the dashboard interaction legible.

## What The Blind Prediction Step Can See

`blind_prediction.json` is generated from a sanitized case context built by `make_blind_case_context()` in `src/policy_impact_sandbox/phase2/blind_prediction.py`.

Visible fields:
- case id and case name
- policy definition entity only: ULEZ expansion scope, effective date and daily charge
- stakeholder group ids, sanitized group names, archetype groups and interests
- safety constraints, including decision-support-only and no automatic on-chain actions

The model is asked for qualitative predictions only:
- support/opposition by group
- relative intensity and affected-group ranking
- political salience/electoral risk
- time dynamics
- secondary reactions such as enforcement resistance
- benefit/burden balance

## What The Blind Prediction Step Cannot See

The blind prediction prompt does not receive `truth_set.json`.
The prediction function does not load the truth set file.

The sanitizer removes:
- source evidence and source quotes
- evidence fact ids
- graph edges/nodes derived from evidence
- historical outcome entities, including by-election outcome, public reaction, camera damage, compliance changes, and air-quality results
- historical assumptions derived from those outcomes
- evidence notes added for post-hoc case graph enrichment

The prompt is stored verbatim in `blind_prediction.json` so reviewers can inspect what the LLM saw.

## Backtest Flow

1. Generate `blind_prediction.json` from sanitized case context only.
2. After the blind prediction artifact is written, load `truth_set.json`.
3. Evaluate R1-R6 from `backtest_rubric.md` against the blind prediction.
4. Write `backtest_result.json` and `backtest.md` with `backtest_mode: blind_prediction`.

This makes the historical truth set available only to the scoring step, not the prediction step.

## Why Mock Simulation Is Still Present

The mock simulation creates posts, comments and stance-change events for the dashboard.
It demonstrates how a multi-agent interaction might look and gives the UI a stable replay path.

It is not used as the credibility basis for the historical backtest.
The credible comparison is the blind prediction artifact versus the verified truth set.

## Remaining Limitations

The sanitized context is derived from a case graph that was originally built for a historical ULEZ case.
To reduce leakage, the blind context strips outcome entities and sets visible stakeholder prior stance to `unknown`.
However, stakeholder group selection itself is part of the case framing, so the blind test should be described as an answer-isolated historical backtest, not as a randomized controlled evaluation.

The backtest is directional only. It does not claim to predict exact polling percentages, vote margins, offence counts, compliance rates or air-quality numbers.
