FIRST ACTION: save this entire instruction verbatim to docs/HACKATHON_TASKS.md and commit it before doing anything else.



CONTEXT

You are working on Policy Impact Sandbox (branch: productization-live-policy-run), UK AI Agent Hackathon EP5. Submission targets: Conduct track (judging: Technical execution 35% / Impact & speed-up 30% / User stays in control 20% / Demo 20%) and Kaspa bounty (Innovation 30% / Kaspa Integration 30% / Technical Execution 20% / Demo & UX 20%). Feature freeze: evening of 2026-07-03 (BST). Demo Day: 2026-07-04 10:00. Work through the tasks strictly in order; land each as a complete, green-tests commit before starting the next. If time runs out mid-task, stop at the last complete commit and report.



GROUND RULES

- Never silently change scope. If the repo's actual structure differs from this instruction's assumptions (file names, module boundaries), adapt minimally and log every deviation in your report. Do not refactor or "improve" unrelated code.

- The cached ULEZ demo path must keep working offline at all times (no live LLM, no network, no testnet). Never break the semantics of backups/demo-safe-v1. main stays as the demo-safe lock; do NOT merge to main until final validation at freeze.

- No secrets in commits. .env stays gitignored. Never print or commit private keys or API keys.

- Never broadcast a Kaspa transaction yourself. Anything that would broadcast must stop at "ready, awaiting human approval".

- Code, comments, docs, commit messages: English. Reports to me: Chinese (technical terms in English).

- Timebox: if blocked >45 min on any item with no viable path, park it, report, move on.



PHASE 0 — PROTECT WORK + STATE SNAPSHOT (immediately, ~45 min)

0.1 Commit all uncommitted work on productization-live-policy-run as a short series of logical commits (extraction module / API / frontend / tests). If clean separation isn't quick, one honest commit is acceptable — speed over beauty.

0.2 Run the full test suite (Python + frontend + npm run build); record results.

0.3 Write docs/STATE.md (committed) with concrete file paths:

  a. Repo map: tree of src/, scripts/, tests/, docs/, frontend (2 levels), one line per key module.

  b. Live-run data flow: exact function/module sequence from POST /api/policy-runs to report + manifest; which artifacts are written to disk and which are inline-only.

  c. Blind backtest internals: where R1–R6 are defined; ULEZ truth-set file format; where answer isolation is enforced; where scoring happens; exact prompt files used for prediction.

  d. Manifest + hashing: current manifest schema (paste one real example), exactly how the SHA-256 is computed today (which bytes — file? JSON dump? key order? encoding?), and where txid f553f7bf… is referenced.

  e. Kaspa integration: library/SDK, network (testnet-10), how the payload is embedded, how the manual-approval gate works, what credentials/funds another tx would need.

  f. LLM client: providers, where model/temperature are set, how mock mode works, whether any seeds are set.

  g. Config: every env var read, and which are required for (i) demo mode, (ii) live mode, (iii) anchoring.

  h. Known gaps/TODOs not covered by this instruction.

0.4 Send me STATE.md as your first report, then continue immediately with Task 1 — do not wait for my reply.



TASK 1 — MID-PIPELINE APPROVAL GATE + CHAINED AUDIT (highest scoring leverage; target: rest of today)

Goal: change the live pipeline from one-shot "extract→report" into "extract → HUMAN REVIEW/EDIT → approve → simulate+report", with every approval captured in a hash-chained audit trail that the Kaspa anchor commits to.

1.1 Async run model: POST /api/policy-runs creates a run and returns run_id; pipeline executes in background (FastAPI BackgroundTasks or a simple thread — no Celery/Redis); GET /api/policy-runs/{run_id} returns status. Persist every live run under runs/{run_id}/ (input, intermediate artifacts, report, manifest) using the same artifact structure as the cached demo run. States: RECEIVED → EXTRACTING → AWAITING_REVIEW → SIMULATING → REPORTING → AWAITING_ANCHOR_APPROVAL → DONE, plus FAILED{stage, partial artifacts}. Pipeline pauses at AWAITING_REVIEW after case-graph extraction.

1.2 Review/approve API: GET returns the extracted case graph (stakeholders, assumptions, weights); PATCH allows edits validated against the existing JSON Schema; POST /api/policy-runs/{run_id}/approve resumes. Record an ApprovalEvent: {timestamp, stage, editor:"human", diff between AI-proposed and human-approved case graph, approved_hash}.

1.3 Hash chain: introduce ONE canonical hashing function used everywhere (sorted keys, UTF-8, fixed separators — document it). Chain: h0=H(policy_input); h1=H(h0‖case_graph_ai); h2=H(h1‖approval_event); h3=H(h2‖simulation_outputs); h4=H(h3‖report). Manifest stores all links + head hash; the Kaspa anchor commits to the head — one on-chain tx now provably covers the human approval, not just the final report. IMPORTANT: if today's hashing differs, keep a legacy verification path for the already-anchored demo run; do not rewrite its manifest. Do not anchor per step by default (testnet reliability risk); add config flag anchor_per_approval=false as optional stretch.

1.4 Frontend: at AWAITING_REVIEW show a Review screen — AI-proposed stakeholders/assumptions in editable fields, low-confidence extractions highlighted if confidence exists, visible diff after edits, Approve button gates continuation. Stage progress driven by the status endpoint (polling is fine; SSE optional). After completion, the audit panel renders the chain: each link, the approval diff, anchor status.

1.5 Tests: chain hashing (tamper any link → head changes), approval-diff recording, state-machine transitions, resume-after-approve; API tests with mocked LLM for happy path + one FAILED path. All existing tests stay green.

Acceptance: fully offline with mock LLM — POST a policy text, reach AWAITING_REVIEW, PATCH one stakeholder weight, approve, receive a report whose manifest contains the approval diff and a valid hash chain.



TASK 2 — ABLATION BASELINES (evidence against "prompt wrapper"; target: tonight / tomorrow morning)

Same blind-backtest protocol, three conditions on ULEZ: (A) bare single prompt answering R1–R6 directly from the policy text; (B) single-analyst — full context, no stakeholder agents, one generic analyst prompt; (C) full pipeline.

2.1 Harness script scripts/run_ablation.py that reuses the existing scorer and answer isolation UNTOUCHED — conditions differ only in the prediction-generation path. If you believe the scorer must change, STOP and report instead of changing it.

2.2 Each condition runs k times (default k=5; k=1 in mock mode for tests). Output docs/evaluation/ablation_ulez.md + a JSON artifact: per-condition per-question hit/miss matrix, mean hit rate, per-question consistency.

2.3 If live LLM credentials are present in the environment, run the real k=5 ablation and report actual numbers. Report results verbatim even if C does not beat A — do not soften unfavorable numbers.

Acceptance: one command reproduces the table in mock mode; real-run command documented.



TASK 3 — STABILITY + SENSITIVITY (shares infra with Task 2; target: tomorrow midday)

3.1 Repeat-stability: run the full pipeline's R1–R6 judgment stage k=5 times; per-question consistency; any question whose majority answer flips across runs is marked UNSTABLE. Surface next to each directional claim in the report ("5/5 runs agree" vs "3/5 — unstable").

3.2 Weight sensitivity: perturb stakeholder weights ±20% (default 6 perturbations), rerun the judgment stage only, report which conclusions flip. Add a "Robustness" section to the generated report: robust vs assumption-sensitive conclusions.

3.3 Judgment-stage-only reruns — never re-extract. Artifacts to runs/{id}/robustness.json; mock-mode test covers aggregation logic.



TASK 4 — INDEPENDENT VERIFIER + ANCHORING SPEC (Kaspa Integration 30%; target: tomorrow afternoon)

4.1 scripts/verify_run.py: input = run directory + txid; recompute the canonical hash chain from artifacts, fetch the tx payload from a public Kaspa testnet-10 explorer/API, compare, print PASS/FAIL per link + overall. Must support BOTH the legacy anchored demo run (f553f7bf…, via the legacy path from 1.3) and new chained runs. Isolate the network fetch so tests can mock it.

4.2 docs/ANCHORING_SPEC.md: exactly what the anchor commits to (chain construction, byte-level canonical serialization rules), what stays off-chain and why (privacy model: policy text and AI content never on-chain), verifier usage.

4.3 Tamper demo: a test + documented manual demo — flip one byte in an artifact, verification fails.

Acceptance: verify_run.py passes end-to-end against the real explorer for the demo run; any tampered artifact yields FAIL.



TASK 5 (STRETCH — only after Tasks 1–4 are committed and green) — SECOND BACKTEST CASE: London Congestion Charge 2003

Scaffold exactly like ULEZ: input document from the official 2003 scheme/consultation text (public); truth set DRAFTED from TfL post-implementation monitoring literature with a citation per entry. Mark the entire case "DRAFT — PENDING HUMAN VERIFICATION" and exclude it from all headline numbers until I confirm each ground-truth entry. Run the blind protocol in mock mode only to prove plumbing.



TASK 6 (STRETCH) — CLAIM PROVENANCE LABELS

Tag every claim in the generated report as DOCUMENT-CITED (with pointer into source text) / INFERRED-FROM-DOCUMENT / MODEL-PRIOR. Render labels in the report UI + append a claims audit table (claim → evidence pointer → provenance class). Prompt + schema + renderer change; keep it minimal.



REPORTING

After Phase 0 and after each task: short Chinese report — commits landed, test status, deviations, decisions needed from me. At freeze: full status against this list, then run the complete suite and merge productization-live-policy-run → main only if everything is green; finish with a one-paragraph honest assessment of the weakest remaining point.