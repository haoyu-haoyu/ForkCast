# ForkCast Roadmap and Current Limits

Current state as of 2026-07-02: the repository is frozen around the cached ULEZ showcase, answer-isolated blind prediction artifacts, automated rubric-coverage artifacts, human review checkpoints, and a Kaspa testnet-10 anchor. Product build work is gated until after Demo Day unless explicitly overridden.

## What Works Today

- Offline cached ULEZ demo with the 90-second flow: case graph, archetype agents, mock replay, impact report, automated keyword-rubric R1-R6 signal coverage, human adjudication material, and Kaspa anchor card.
- Review-gated live policy run path for a new policy document, using DeepSeek-compatible OpenAI-format configuration when keys are provided.
- Answer-isolated blind prediction for the ULEZ 2023 expansion case, with leakage guards recorded per run.
- Hash-chained audit manifests, local verification, and a real Kaspa testnet-10 anchor for the legacy showcase run.
- Evaluation hardening artifacts:
  - [Negative controls](evaluation/negative_controls.md)
  - [Adversarial input suite](evaluation/adversarial_inputs.md)
  - [CC 2003 verification checklist](evaluation/cc2003_verification_checklist.md)

## Current Limits

- Single fully verified historical case: ULEZ 2023 is the only source-backed case ready for human adjudication today. The London Congestion Charge 2003 case remains draft and excluded from headline claims until every scored fact is manually confirmed.
- Directional-only resolution: current automated rubric output checks qualitative signal coverage, not exact magnitudes, dates, costs, vote shares, calibrated probability forecasts, or semantic truth.
- Mock simulation is a visualization aid: the social feed and event replay help explain how stakeholders interact, but the credibility claim comes from answer-isolated blind prediction, not from mock events.
- In-process background tasks: live runs currently execute through the app process rather than a durable queue. A restart during a live run can interrupt work.
- Scorer mechanism is documented: A1/D1-D2 negative controls show the automated R1-R6 scorer is a prediction-text signal checklist with no semantic comparison target. Inverting truth-set content, shuffling fact alignment, and temporarily inverting the harness-level RULE_FACTS surrogate did not change verdicts. Human grading should therefore use the adjudication sheet, while the scorer remains a reproducible extraction aid.
- Extraction is permissive on bad inputs: A2 showed schema-valid outputs for adversarial, underspecified, off-topic, and technical inputs. That is graceful from a crash-safety perspective, but it does not yet enforce strong "ask for clarification" behavior.
- Anchor coverage boundary: the Kaspa anchor commits to manifest hashes and metadata. AI reasoning, source text, and large artifacts remain off-chain and must be verified through the repository artifacts plus canonical hashing.
- OASIS is optional and non-integrated: the earlier OASIS probe is not part of the default pipeline. ForkCast currently uses mock replay for demonstration unless a future ablation-gated simulation backend proves it improves source-backed human adjudication outcomes across verified cases.
- Canton is not implemented: any Canton-related material is a future integration note, not a completed feature.

## Phase B Plan

Phase B starts no earlier than 2026-07-05 unless the gate is explicitly overridden.

### B1 - Truth-Set Workbench

Make truth-set construction a product loop: LLM drafts facts and citations from post-implementation sources, then a human reviewer marks each item CONFIRM, REJECT, or EDIT in a UI. Only fully confirmed truth sets unlock human adjudication and any future semantic scoring. The backend should provide CRUD, schema validation, per-fact provenance, and audited human decisions using the existing approval-event pattern.

Acceptance: a brand-new case goes from raw sources to a human-adjudicated blind prediction review without hand-editing JSON.

### B2 - Ablation-Gated Feature Entry

Codify a one-command harness and documentation rule: any prediction-affecting component must improve source-backed human adjudication outcomes, and may also improve automated rubric coverage, across all verified cases before becoming part of the default path. This includes any future OASIS or multi-agent simulation backend.

Acceptance: the mock replay remains the honest default until a replacement improves adjudicated outcomes on verified cases.

### B4 - Resolution and Calibration

Upgrade predictions from direction-only to direction plus magnitude band plus time window. Version the schema, prompts, scorer, and truth-set format so ULEZ v1 results remain comparable. Track stated confidence per judgment and compute calibration as cases accumulate.

Acceptance: ULEZ and CC 2003 can be re-run as v2 baselines once both have verified truth sets.

### B3 - Real-Format Ingestion

Add PDF upload, GOV.UK or URL fetch, chunking for long documents, and page or paragraph references that carry through extraction into provenance labels.

Acceptance: a real GOV.UK consultation PDF runs end-to-end with page-referenced claims.

### B6 - What-If Forking

Fork a reviewed case graph into policy variants, rerun judgment stages only, and render a structured diff of conclusions. Record fork lineage in the audit chain.

Acceptance: an ULEZ charge-level variant comparison, such as GBP 12.50 versus GBP 15.00.

### B5 - Ops Hardening

Move background tasks to a persistent queue with retry, add a run-history UI, support multi-provider LLM configuration, implement optional `anchor_per_approval=true`, and write a mainnet cost and feasibility memo for payload anchoring.

Acceptance: a server restart mid-run loses nothing, and two concurrent runs do not interfere.

## Recommended Execution Order

1. B1 - Truth-Set Workbench
2. B2 - Ablation-Gated Feature Entry
3. B4 - Resolution and Calibration
4. B3 - Real-Format Ingestion
5. B6 - What-If Forking
6. B5 - Ops Hardening

## Judge Q&A Phrases

- "The demo is intentionally conservative: one verified case, answer-isolated blind prediction, automated rubric coverage with visible limits, and a human adjudication path."
- "Mock replay is not our evidence. It is only the UI explanation layer."
- "The A1/D1-D2 controls found the automated scorer is a text-signal checklist, not a semantic judge. We are not overselling the score; human grading should come from the adjudication sheet and future scorer redesign."
- "The chain anchor proves artifact commitment, not policy correctness. Correctness comes from source-backed truth sets, blind prompts, and verification scripts."
