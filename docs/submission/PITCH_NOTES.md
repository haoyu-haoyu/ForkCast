# Pitch Notes

## One Sentence

Policy Impact Sandbox is a human-controlled AI workflow that turns a policy memo into archetype agents, a replayable impact simulation, an answer-isolated historical backtest and a Kaspa-anchored audit trail.

## Core Innovation

The credibility move is the answer-isolated blind backtest.

The system first asks DeepSeek for a qualitative prediction using only sanitized policy context: policy facts, stakeholder groups, interests and safety constraints. The prediction step does not load `truth_set.json` and the prompt explicitly forbids post-implementation outcomes such as polling percentages, election results, compliance rates, camera offence counts and air-quality measurements.

Only after `blind_prediction.json` is written does the backtest code load the verified ULEZ truth set and score R1-R6 directionally. That means the demo comparison is not based on mock events that were written after seeing the answers. Mock simulation remains only a visualization layer.

Current blind-backtest result:

- R1: PARTIAL
- R2: HIT
- R3: HIT
- R4: HIT
- R5: HIT
- R6: BALANCED HIT

## What Is Real

- Real ULEZ 2023 historical truth set with sourced facts and quotes.
- Real DeepSeek-backed blind prediction artifact.
- Real answer-isolated backtest result from `backtest_result.json`.
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

- This is not a randomized holdout. It is an answer-isolated historical backtest on one known policy case.
- The case graph still names stakeholder groups relevant to ULEZ, so the blind test is not free of all framing information.
- The backtest is directional only. It does not claim exact polling percentages, vote margins, offence counts, compliance rates or air-quality numbers.
- Kaspa anchoring proves an audit-manifest commitment, not the truth of the AI's conclusions.
- SilverScript/Covenants are not implemented as production chain rules in this MVP.
- Canton/Daml is not implemented.

## Judge Questions And Honest Answers

### Is this a true holdout?

No. It is an answer-isolated historical backtest. The model is prevented from seeing the truth set and outcome tokens before prediction, then the written prediction is scored against verified outcomes. That is weaker than a randomized holdout but much stronger than a mock simulation tuned to match known results.

### How do you prove the model did not see the answers?

Show `blind_prediction.json` and `docs/methodology/backtest_integrity.md`. The prediction function builds a sanitized context and does not load `truth_set.json`. The stored prompt is visible in the dashboard, and the UI shows the outcome-token scan status.

### Did the mock simulation drive the backtest?

No. Mock events are only for the social-feed visualization and demo continuity. The backtest table reads `backtest_result.json`, which scores `blind_prediction.json` against the truth set.

### Why is R1 only PARTIAL?

Because the blind prediction identified outer-London opposition but did not cleanly capture the full inner-vs-outer contrast. We keep that as PARTIAL because a credible demo should not hide misses.

### Did OASIS run live?

Not in the mainline MVP. OASIS was treated as a single-point risk and remains an optional, non-integrated probe, so the project switched to mock simulation mode for the end-to-end demo. Real LLM calls for extraction, agent profiles, reports and blind prediction use DeepSeek.

### Where do the money/score numbers come from?

They are illustrative/demo estimates for the dashboard. The evidence-backed validation is the R1-R6 blind backtest and its source-linked truth set.

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
