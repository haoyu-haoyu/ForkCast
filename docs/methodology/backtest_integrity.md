# Blind Prediction Integrity And Grading

This project separates prediction generation from historical outcome verification.
Mock events are only used to make the dashboard interaction legible.

ForkCast generates answer-isolated blind predictions: the prediction step provably never reads outcome data, and leakage guards are recorded per run.

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

## Prediction And Grading Flow

1. Generate `blind_prediction.json` from sanitized case context only.
2. After the blind prediction artifact is written, load source-backed truth-set material for review.
3. Produce automated R1-R6 keyword-rubric verdicts in `backtest_result.json`.
4. Render `docs/evaluation/ulez_human_adjudication.md` so a human can grade the prediction against the truth-set facts, URLs and quotes.

This makes the historical truth set unavailable to the prediction step. The automated rubric is a signal-coverage checklist; it is not a semantic truth comparator.

## Grading Mechanisms

Predictions are graded two ways:

1. An automated keyword rubric, whose limits we exposed through negative controls. It checks signal coverage, not semantic truth.
2. Human adjudication against a source-backed truth set in `docs/evaluation/ulez_human_adjudication.md`.

The negative-controls result in `docs/evaluation/negative_controls.md` shows that inverting truth-set content, shuffling fact alignment and temporarily inverting the harness-level RULE_FACTS surrogate did not change automated verdicts. Therefore the automated verdicts should be described as rubric-coverage outputs, not accuracy.

## Why Mock Simulation Is Still Present

The mock simulation creates posts, comments and stance-change events for the dashboard.
It demonstrates how a multi-agent interaction might look and gives the UI a stable replay path.

It is not used as grading evidence. The grading evidence is the blind prediction artifact, the automated keyword-rubric characterization, the negative-controls limitation report and the human adjudication sheet.

## Remaining Limitations

The sanitized context is derived from a case graph that was originally built for a historical ULEZ case.
To reduce leakage, the blind context strips outcome entities and sets visible stakeholder prior stance to `unknown`.
However, stakeholder group selection itself is part of the case framing, so the blind test should be described as an answer-isolated blind prediction review on a known historical case, not as a randomized controlled evaluation.

The current rubric is directional signal coverage only. It does not claim verified accuracy, and it does not claim to predict exact polling percentages, vote margins, offence counts, compliance rates or air-quality numbers.
