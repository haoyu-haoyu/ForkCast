# ULEZ Ablation Baselines

All conditions use the same R1-R6 scorer: `evaluate_blind_prediction_backtest`.
The truth set is loaded only after each prediction artifact is written.
After the mechanism audit, this table should be read as automated keyword-rubric coverage: it measures how often each condition expresses the expected outcome dimensions under the rubric. It is not verified accuracy and not semantic truth comparison.

Mode: `real_llm`. Runs per condition: `5`.

Anchor coverage boundary: `robustness.json`, ablation artifacts, and anything generated after 2026-07-01 in `runs/ulez_2023_phase2_deepseek/` are NOT covered by the f553 anchor; only the eight artifacts listed in the anchored manifest are committed to on-chain.

Rubric-coverage rule: `PARTIAL` counts as uncovered for the strict coverage fraction; `HIT` and `BALANCED HIT` count as covered. Mean coverage is computed over `k=5` runs times 6 rubric questions per condition.

Interpretation: the ordering `bare_prompt < single_analyst < full_pipeline` suggests pipeline structure increases coverage of expected outcome dimensions under the automated rubric. It does not prove accuracy. The observed coverage gain concentrates on R4, and `n=5` is too small for statistical significance. Ablation, repeat-stability, and weight-sensitivity all independently flag R4 as the assumption-sensitive judgment; that is the kind of case the human approval gate and human adjudication sheet exist to review.

Reproduce mock smoke table: `uv run python scripts/run_ablation.py --mock-llm --k 1 --output-dir docs/evaluation`.
Run real DeepSeek table: `uv run python scripts/run_ablation.py --k 5 --output-dir docs/evaluation`.

| Condition | Mean rubric coverage | R1 | R2 | R3 | R4 | R5 | R6 |
|---|---:|---|---|---|---|---|---|
| bare_prompt | 0.63 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |
| single_analyst | 0.70 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |
| full_pipeline | 0.73 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |

## Rubric Coverage Matrix

| Condition | Run | R1 | R2 | R3 | R4 | R5 | R6 |
|---|---:|---|---|---|---|---|---|
| bare_prompt | 1 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |
| bare_prompt | 2 | PARTIAL | HIT | HIT | MISS | MISS | BALANCED HIT |
| bare_prompt | 3 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |
| bare_prompt | 4 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |
| bare_prompt | 5 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |
| single_analyst | 1 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |
| single_analyst | 2 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |
| single_analyst | 3 | PARTIAL | HIT | HIT | HIT | HIT | BALANCED HIT |
| single_analyst | 4 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |
| single_analyst | 5 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |
| full_pipeline | 1 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |
| full_pipeline | 2 | PARTIAL | HIT | HIT | HIT | HIT | BALANCED HIT |
| full_pipeline | 3 | PARTIAL | HIT | HIT | HIT | HIT | BALANCED HIT |
| full_pipeline | 4 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |
| full_pipeline | 5 | PARTIAL | HIT | HIT | MISS | HIT | BALANCED HIT |

## Per-Question Consistency

### bare_prompt

| Rule | Majority verdict | Consistency | Counts |
|---|---|---:|---|
| R1 | PARTIAL | 1.00 | {"PARTIAL": 5} |
| R2 | HIT | 1.00 | {"HIT": 5} |
| R3 | HIT | 1.00 | {"HIT": 5} |
| R4 | MISS | 1.00 | {"MISS": 5} |
| R5 | HIT | 0.80 | {"HIT": 4, "MISS": 1} |
| R6 | BALANCED HIT | 1.00 | {"BALANCED HIT": 5} |

### single_analyst

| Rule | Majority verdict | Consistency | Counts |
|---|---|---:|---|
| R1 | PARTIAL | 1.00 | {"PARTIAL": 5} |
| R2 | HIT | 1.00 | {"HIT": 5} |
| R3 | HIT | 1.00 | {"HIT": 5} |
| R4 | MISS | 0.80 | {"HIT": 1, "MISS": 4} |
| R5 | HIT | 1.00 | {"HIT": 5} |
| R6 | BALANCED HIT | 1.00 | {"BALANCED HIT": 5} |

### full_pipeline

| Rule | Majority verdict | Consistency | Counts |
|---|---|---:|---|
| R1 | PARTIAL | 1.00 | {"PARTIAL": 5} |
| R2 | HIT | 1.00 | {"HIT": 5} |
| R3 | HIT | 1.00 | {"HIT": 5} |
| R4 | MISS | 0.60 | {"HIT": 2, "MISS": 3} |
| R5 | HIT | 1.00 | {"HIT": 5} |
| R6 | BALANCED HIT | 1.00 | {"BALANCED HIT": 5} |
