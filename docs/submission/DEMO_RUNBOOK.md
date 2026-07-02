# Demo Runbook

## 90 Second Path

Use the local dashboard at `http://127.0.0.1:5173/`.

1. Before: show the legacy workflow as weeks of consultants, hearings, spreadsheets and weak traceability.
2. ULEZ selected: select the real 2023 London-wide ULEZ expansion case and state that replay is cached.
3. Approve extraction: show nine stakeholders, including van drivers/tradespeople/small businesses and low-income households. Approve checkpoint 1.
4. Approve agents: show archetype-only personas, stance priors and group sliders. Approve checkpoint 2.
5. Run controls: show 36 agents, 3 rounds, budget cap, locked seed, cached replay and small live-sample option. Approve checkpoint 3.
6. Simulation replay: show the mock social feed. Say clearly that mock events are for visualization only.
7. Impact report: show risk timeline, claim review, delete/downgrade controls and mitigation options. Point out that any scores or monetary framing are illustrative/demo estimates only.
8. Blind prediction + rubric: make this the high point. Show R1-R6 automated keyword-rubric verdicts from `backtest_result.json`, with R1 as PARTIAL and R6 as BALANCED HIT. Say clearly that these are signal-coverage verdicts, not semantic truth verification, then point to `docs/evaluation/ulez_human_adjudication.md` for human grading against source-backed facts.
9. Audit + Kaspa: show the audit manifest hashes, payload bytes, real TN-10 transaction id and explorer link.
10. Close: "weeks to hours, with the human still in control."

## Known Demo Talking Points

- ForkCast generates answer-isolated blind predictions: the prediction step provably never reads outcome data and leakage guards are recorded per run.
- Predictions are graded two ways: an automated keyword rubric whose limits are documented in `docs/evaluation/negative_controls.md`, and human adjudication against a source-backed truth set in `docs/evaluation/ulez_human_adjudication.md`.
- The blind-prediction prompt does not load `truth_set.json` and forbids outcome metrics, election results, polling percentages, compliance rates and camera offence counts.
- The demo uses one historical case, so describe it as answer-isolated blind prediction with rubric-coverage and human-adjudication evidence, not randomized holdout validation.
- Kaspa anchoring stores a manifest-hash commitment only. AI reasoning and source artifacts stay off-chain.
- The tool is decision support, not a deterministic forecast.

## Offline / Network Fallback

The dashboard can run from cached local artifacts:

- `web/src/data/*.json` contains the replay, backtest, audit manifest and Kaspa anchor data.
- `web/dist/` contains a built static dashboard after `npm run build`.
- The Kaspa explorer link needs network access only if judges want to open the external transaction page.
- If internet access fails, show `runs/ulez_2023_phase2_deepseek/kaspa_anchor.json` and the recorded tx id/payload hash locally.
- A screen recording should follow the 90-second path above and can be used as a fallback if the live browser stalls.

## QA Findings From Local Click-Through

- The full path Before -> ULEZ selected -> extraction approval -> agent approval -> run approval -> replay -> report -> blind rubric -> Audit + Kaspa -> close was clickable on the local Vite dashboard.
- The blind prediction rubric table rendered the real R1-R6 automated keyword-rubric result set. R1 showed PARTIAL; R6 showed BALANCED HIT.
- Persona chat switched to the van drivers/tradespeople/small businesses archetype and returned a cost/livelihood-based opposition answer with the archetype-only/no-PII label.
- The Audit + Kaspa panel rendered status `anchored`, network `testnet-10`, payload `731/25000`, the real tx id and a clickable explorer URL.
- Browser console showed only the standard React DevTools info message during the QA run.
- One issue was found and fixed: Audit + Kaspa still used future-tense Phase 4 placeholder copy. It now states that the testnet anchor was broadcast after checkpoint-4 approval.

## Remaining Demo Risks

- The "Run live sample" button is a demo affordance; the main path should use cached replay.
- OASIS live execution is intentionally out of scope for the MVP path.
- The dashboard state is client-side; refreshing resets checkpoint UI approvals, which is acceptable for a staged demo but worth avoiding mid-run.
- Opening the Kaspa explorer depends on network availability. Keep the local anchor JSON ready as fallback evidence.
