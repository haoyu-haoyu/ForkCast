# Pitch Notes

## One Sentence

ForkCast is a human-controlled AI workflow that turns a policy memo into archetype agents, a replayable impact simulation, an answer-isolated blind prediction and a Kaspa-anchored audit trail.

## Core Innovation

The credibility move is answer isolation plus explicit grading limits.

ForkCast generates answer-isolated blind predictions: the prediction step provably never reads outcome data, and leakage guards are recorded per run. The system first asks DeepSeek for a qualitative prediction using only sanitized policy context: policy facts, stakeholder groups, interests and safety constraints. The prediction step does not load `truth_set.json` and the prompt explicitly forbids post-implementation outcomes such as polling percentages, election results, compliance rates, camera offence counts and air-quality measurements.

Predictions are graded two ways: (1) an automated keyword rubric, whose limits we exposed ourselves via negative controls; it checks signal coverage, not semantic truth; and (2) human adjudication against a source-backed truth set in `docs/evaluation/ulez_human_adjudication.md`. Mock simulation remains only a visualization layer.

Current automated keyword-rubric signal coverage:

- R1: PARTIAL
- R2: HIT
- R3: HIT
- R4: HIT
- R5: HIT
- R6: BALANCED HIT

## What Is Real

- Real ULEZ 2023 historical truth set with sourced facts and quotes.
- Real DeepSeek-backed blind prediction artifact.
- Real automated keyword-rubric output from `backtest_result.json`, with its limits documented in `docs/evaluation/negative_controls.md`.
- Human adjudication sheet at `docs/evaluation/ulez_human_adjudication.md` for source-backed human grading.
- Real human-in-the-loop control UI with four checkpoints: extraction, agents, run config, report/chain review.
- Real hard limits in the dashboard: no automatic chain action, no automatic weight changes, no real-person PII, archetypes only and decision support only.
- Real Kaspa TN-10 transaction anchoring the audit-manifest payload:
  - Tx id: `f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`
  - Explorer: `https://explorer-tn10.kaspa.org/txs/f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`

## What Is Demo Substitute

- Mock simulation events are used to make an agent interaction feed visible and replayable. They are not used as historical prediction evidence.
- Dashboard impact scores and any monetary framing are illustrative/demo estimates only.
- The "Run live sample" path is secondary; the main demo uses cached replay artifacts for reliability.
- OASIS live execution is an optional, non-integrated stretch experiment, not part of the mainline MVP.

## Honest Limits

- This is not a randomized holdout. It is an answer-isolated blind prediction on one known policy case, followed by automated signal-coverage scoring and human adjudication material.
- The case graph still names stakeholder groups relevant to ULEZ, so the blind test is not free of all framing information.
- The automated R1-R6 rubric is directional signal coverage only. It does not claim verified accuracy, exact polling percentages, vote margins, offence counts, compliance rates or air-quality numbers.
- Kaspa anchoring proves an audit-manifest commitment, not the truth of the AI's conclusions.
- SilverScript/Covenants are not implemented as production chain rules in this MVP.
- Canton/Daml is not implemented.

## Judge Questions And Honest Answers

### Is this a true holdout?

No. It is an answer-isolated blind prediction on a known historical case. The model is prevented from seeing the truth set and outcome tokens before prediction. Afterward, the prediction is reviewed through an automated keyword rubric and a human adjudication sheet against source-backed outcomes.

### How do you prove the model did not see the answers?

Show `blind_prediction.json` and `docs/methodology/backtest_integrity.md`. The prediction function builds a sanitized context and does not load `truth_set.json`. The stored prompt is visible in the dashboard, and the UI shows the outcome-token scan status.

### Did the mock simulation drive the backtest?

No. Mock events are only for the social-feed visualization and demo continuity. The rubric table reads `backtest_result.json`, which characterizes `blind_prediction.json` for expected signal coverage.

### Why is R1 only PARTIAL?

Because the blind prediction identified outer-London opposition but did not cleanly capture the full inner-vs-outer contrast under the keyword rubric. We keep that as PARTIAL because a credible demo should not hide rubric misses.

### Is the automated R1-R6 scorer a semantic judge?

No. The evidence-hardening controls show it is a reproducible prediction-text signal checklist, not a semantic comparator against truth-set content. Inverting truth facts, shuffling fact alignment and temporarily inverting the harness-level RULE_FACTS surrogate did not change verdicts. Use `docs/evaluation/ulez_human_adjudication.md` for human grading.

### Did OASIS run live?

Not in the mainline MVP. OASIS was treated as a single-point risk and remains an optional, non-integrated probe, so the project switched to mock simulation mode for the end-to-end demo. Real LLM calls for extraction, agent profiles, reports and blind prediction use DeepSeek.

### Where do the money/score numbers come from?

They are illustrative/demo estimates for the dashboard. The evidence-backed grading path is the answer-isolated blind prediction plus human adjudication against the source-linked truth set.

### What exactly is on Kaspa?

Only a commitment payload: manifest hash, case id, run id, stage metadata and human-approval policy. AI reasoning, source evidence, prompts and reports stay off-chain.

### Does the Kaspa tx mean the report is correct?

No. It proves what artifact set was approved and anchored at a point in time. It is an audit and governance primitive, not a truth oracle.

### Did the system automatically send the Kaspa transaction?

No. The dashboard and CLI both enforce a human approval gate. The broadcast used a testnet wallet after explicit checkpoint-4 approval logic.

### Are these real people?

No. Personas are archetypes, not real people. The app does not process real-person PII.

### What would you do next?

Run multiple blind historical cases, add richer source review workflows, replace mock replay with stable live OASIS or another simulation backend, and turn the Kaspa anchor into a production operator workflow with custody and policy controls.
