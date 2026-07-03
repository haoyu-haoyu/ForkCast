# Deck Facts: ForkCast

Single source of truth for deck, DoraHacks BUIDL copy, demo narration, and judge Q&A.

Repo pointer: `https://github.com/haoyu-haoyu/ForkCast`.
Current public head before this file: `6c8e693 docs: add broadcast operator card`.

## Canonical Claim Language

Use these sentences verbatim when space allows:

> ForkCast generates answer-isolated blind predictions: the prediction step provably never reads outcome data (leakage guards recorded per run).

> Predictions are graded two ways: (1) an automated keyword rubric — whose limits we exposed ourselves via negative controls; it checks signal coverage, not semantic truth — and (2) human adjudication against a source-backed truth set (docs/evaluation/ulez_human_adjudication.md).

Pointers:

- `README.md`, Safety Rules.
- `docs/submission/PITCH_NOTES.md`, Core Innovation and Judge Q&A.
- `docs/evaluation/negative_controls.md`, Headline Finding and Mechanism.
- `docs/evaluation/ulez_human_adjudication.md`, source-backed human grading sheet.
- Dashboard caption in `web/src/App.tsx`: "Automated keyword-rubric verdicts — signal coverage, not semantic verification. See negative controls & human adjudication."

## Rubric Coverage And Ablation Framing

- `0.8333` may appear only as an automated keyword-rubric coverage number inside the negative-controls narrative. It is not accuracy.
- `0.7333` / `0.73` may appear only as ablation rubric coverage for the full-pipeline condition. It is not accuracy.
- Ablation ordering should be described as: pipeline structure increased coverage of expected outcome dimensions under the automated rubric, not verified accuracy.

Pointers:

- `docs/evaluation/negative_controls.md`, Rubric Coverage Rates and Interpretation.
- `docs/evaluation/negative_controls.json`, machine-readable control results.
- `docs/evaluation/ablation_ulez.md`, table and interpretation.
- `docs/evaluation/ablation_ulez.json`, k=5 raw run matrix.

## Negative-Controls Story

We first built an answer-isolated blind-prediction workflow so the prediction prompt never reads ULEZ outcome data. We then built our own negative controls and found the automated R1-R6 scorer is a keyword checklist: inverting and shuffling truth content did not change the verdicts, so the scorer measures signal coverage rather than semantic truth. We published that limitation, moved accuracy evidence to the human-adjudication sheet, and put a semantic scorer redesign as the first Phase B roadmap item.

Pointers:

- `docs/evaluation/negative_controls.md`, Headline Finding, Mechanism, Control C.
- `src/policy_impact_sandbox/evaluation/negative_controls.py`, harness-only controls.
- `docs/ROADMAP.md`, scorer redesign and future truth-set product loop.

## Audit Chain Facts

Live policy runs use one canonical JSON hashing rule:

```text
json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
```

Hash-chain structure for new live runs:

```text
h0 = H(policy_input)
h1 = H(h0 || canonical_json(case_graph_ai))
h2 = H(h1 || canonical_json(approval_event))
h3 = H(h2 || canonical_json(simulation_outputs))
h4 = H(h3 || canonical_json(report))
```

The manifest stores every link, each artifact hash, each link hash, and final `head_hash`. New live-run Kaspa payloads commit to `head_hash`. The existing ULEZ demo is a legacy anchor path that commits to the canonical `audit_manifest.json` hash because the f553 transaction already exists and is not rewritten.

Legacy ULEZ anchor:

- Tx id: `f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`
- Explorer: `https://explorer-tn10.kaspa.org/txs/f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`
- Payload size: `731 / 25000` bytes.
- Manifest hash: `e9f71f3d18ae1f4a5226bf98f1eb48a14b94fc225e2c3cd38bb97c99fed5bf25`
- Payload hash: `93b99f9ddf63961b9382d0f74416c430d1b560861a0c44fe076d05ff6b536f07`

Exact verify command:

```bash
uv run python scripts/verify_run.py \
  --run-dir runs/ulez_2023_phase2_deepseek \
  --txid f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123 \
  --network testnet-10
```

Showcase APS anchor:

- Run id: `policy_run_20260702T220219Z`
- Canonical tx id: `8a682481e37f9ca5f006150746e3d3eab003b582621b763f0065885c98c656b8`
- Explorer: `https://explorer-tn10.kaspa.org/txs/8a682481e37f9ca5f006150746e3d3eab003b582621b763f0065885c98c656b8`
- Duplicate note: the same commitment was anchored twice due to a CLI output gap; the earliest tx is canonical, and duplicate anchors are harmless redundancy.
- Chained verify command:

```bash
uv run python scripts/verify_run.py \
  --run-dir runs/policy_run_20260702T220219Z \
  --txid 8a682481e37f9ca5f006150746e3d3eab003b582621b763f0065885c98c656b8 \
  --network testnet-10
```

Pointers:

- `docs/HASH_CHAIN.md`, canonical hashing and h0-h4.
- `src/policy_impact_sandbox/phase2/audit.py`, canonical hashing and chain builder.
- `src/policy_impact_sandbox/verify_run.py`, verifier for legacy and chained modes.
- `scripts/verify_run.py`, CLI wrapper.
- `docs/submission/kaspa-integration.md`, Kaspa payload, network, and verification.
- `runs/ulez_2023_phase2_deepseek/kaspa_anchor.json`, legacy anchor record.
- `web/src/data/kaspa_anchor.json`, dashboard anchor copy.

## Control-Story Facts

- Review gate: live runs pause at `AWAITING_REVIEW` after AI extraction; the user can patch the case graph before approval.
- Approval diff: approval writes `approval_event.json` with `editor: "human"`, JSON diff, and approved case-graph hash.
- Anchor approval: broadcasting is not automatic; anchor preparation and broadcast require checkpoint-4 human approval plus the `--human-approved` CLI flag.
- Agent hard limits: agents cannot broadcast Kaspa/Canton transactions automatically, cannot change stakeholder weights without user approval, cannot process real-person PII, and all personas are archetypes.
- New policies without `truth_set` show impact analysis only and no historical grading material.

Pointers:

- `src/policy_impact_sandbox/live_policy/runs.py`, state machine and approval event.
- `src/policy_impact_sandbox/api.py`, POST/PATCH/approve endpoints.
- `scripts/kaspa_broadcast_anchor.py`, `--human-approved` and `testnet-10` fail-closed checks.
- `docs/OPERATOR_RUNBOOK.md`, human operator anchor sequence.
- `docs/submission/BROADCAST_CARD.md`, copy-paste broadcast card.
- `docs/product/control_flow.md`, checkpoint design.
- `web/src/App.tsx`, dashboard control and review UI.

## Test Counts

Latest supporting runs during standby:

- Python suite: `uv run pytest -q` -> `55 passed`, one `StarletteDeprecationWarning`.
- Web suite: `cd web && npm test` -> `13 passed` across 3 test files.
- Previous build check: `cd web && npm run build` -> Vite build passed.
- Broadcast pre-flight: real API `/api/health` returned `{"status":"ok"}`; mock live run reached `AWAITING_REVIEW -> AWAITING_ANCHOR_APPROVAL`; approval diff path `/stakeholders/0/weight`.

Pointers:

- `tests/test_live_policy_async.py`, review-gated live-run acceptance.
- `tests/test_verify_run.py`, verifier behavior.
- `web/src/dashboardContent.test.ts`, dashboard honesty strings.
- `docs/submission/BROADCAST_CARD.md`, pre-flight command.

## Hackathon Commit Timeline

| Commit | What changed |
|---|---|
| `6d64f16` | Locked demo-safe version: `demo-safe-v1`. |
| `0417eae` | Saved hackathon task instructions. |
| `b0cd9e1` | Added live policy run and cockpit dashboard. |
| `cdd2324` | Captured current project state. |
| `e14d07e` | Added review-gated live runs and hash chain. |
| `7830972` | Added operator anchor runbook. |
| `09d43b7` | Added ULEZ ablation baseline harness. |
| `cfd2211` | Added robustness stability analysis. |
| `f464f42` | Added Kaspa run verifier. |
| `5bf8cd8` | Scaffolded Congestion Charge draft case. |
| `29ce55f` | Added claim provenance labels. |
| `1836d17` | Marked legacy provenance unclassified. |
| `581c0b7` | Preserved prepared anchor payload on tx record. |
| `398dc65` | Clarified evaluation anchor boundaries. |
| `89b9ede` | Prepared ForkCast public release. |
| `4d1a51e` | Fixed ES2020 build compatibility. |
| `ab88274` | Recorded product plan gates. |
| `b47ebfe` | Added scorer negative controls. |
| `c192f03` | Added adversarial extraction suite. |
| `1327d20` | Added CC 2003 verification checklist. |
| `3e7bdea` | Added roadmap and current limits. |
| `116f022` | Documented scorer mechanism controls. |
| `e35589f` | Aligned public claims with scorer mechanism. |
| `7510e0c` | Marked dashboard human grading as pending. |
| `6c8e693` | Added broadcast operator card. |

Pointer: `git log --since='2026-07-01 00:00' --oneline --reverse`.

## Conduct Criteria Mapping

| Criterion | Asset, screen, or number that answers it |
|---|---|
| Technical execution 35% | Live run API and state machine: `src/policy_impact_sandbox/api.py`, `src/policy_impact_sandbox/live_policy/runs.py`; schemas in `schemas/`; tests `55 passed`; web tests `13 passed`; cached ULEZ artifacts in `runs/ulez_2023_phase2_deepseek/`. |
| Impact and speed-up 30% | 90-second before/after demo in `docs/submission/DEMO_RUNBOOK.md`; dashboard `Before` screen contrasts weeks of consultants with controlled review flow; live policy input supports public documents with no truth-set overclaim. |
| User stays in control 20% | Four checkpoints and review gates in dashboard; `AWAITING_REVIEW` pause, human editable stakeholder weights, approval diff `/stakeholders/0/weight`, rollback UI, `--human-approved` chain gate. |
| Demo 20% | Offline cached ULEZ path, Kaspa anchor card with f553 explorer link, blind rubric caption, impact report provenance badges, and `docs/submission/BROADCAST_CARD.md` for live showcase anchoring. |

Pointers:

- Judging split source: `docs/HACKATHON_TASKS.md:7`.
- 90-second demo plan: `policy-impact-sandbox-project-plan.md`, section 8.
- UI source: `web/src/App.tsx`.

## Kaspa Criteria Mapping

| Criterion | Asset, screen, or number that answers it |
|---|---|
| Innovation 30% | AI governance workflow where human approval, approval diff, and report artifacts become a hash-chain commitment; negative-controls honesty prevents overclaiming AI accuracy. |
| Kaspa integration 30% | Real TN-10 transaction `f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`; `scripts/kaspa_broadcast_anchor.py`; `scripts/verify_run.py`; dashboard anchor card; `docs/submission/kaspa-integration.md`. |
| Technical execution 20% | Canonical JSON hashing, verifier supporting legacy and chained modes, payload size `731 / 25000`, fail-closed testnet-only broadcast helper, and tests for anchoring/verifier behavior. |
| Demo and UX 20% | `Audit + Kaspa` screen, explorer link, manifest/payload details, operator card, and exact verify command for judges to run. |

Pointers:

- Judging split source: `docs/HACKATHON_TASKS.md:7`.
- Official Kaspa docs referenced by integration: `https://docs.kaspa.org/integrate/transaction-payload`, `https://docs.kaspa.org/integrate/wallet`, `https://wiki.kaspa.org/en/testnets`.
- Explorer: `https://explorer-tn10.kaspa.org/txs/f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`.

## DoraHacks BUIDL Vision Paragraph

ForkCast is review-gated AI policy impact analysis for high-stakes public decisions. It turns a policy memo into a visible workflow: extract stakeholders, review and edit assumptions, generate archetype-only agents, run a replayable impact analysis, and anchor the approved audit trail on Kaspa. The core evidence design is answer-isolated blind prediction: the prediction step does not read outcome data, and grading is split between an automated keyword rubric with published negative-control limits and human adjudication against a source-backed truth set. The demo uses London ULEZ 2023 as a historical case, with mock simulation only as a visualization layer and Kaspa TN-10 as the verifiable audit commitment layer. The larger vision is a governance copilot where AI accelerates analysis but humans keep control of every approval, every stakeholder-weight change, and every chain action.
