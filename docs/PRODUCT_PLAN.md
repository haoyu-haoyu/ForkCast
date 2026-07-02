NEW INSTRUCTION SET — EVIDENCE HARDENING NOW, PRODUCT BUILD AFTER DEMO DAY.
First action: save this entire instruction verbatim to docs/PRODUCT_PLAN.md and commit.

Standing context: submission deadline 2026-07-04 23:59 BST, Demo Day 10:00. STAGE 2 (showcase-run commit + chained real-explorer verification) remains armed and outranks everything below — it triggers the moment the human reports the real txid.

HARD GATES
- G1: PHASE A only until 2026-07-04 23:59. Do NOT start PHASE B before 2026-07-05 unless the human explicitly writes "override the gate".
- G2: PHASE A must not modify any code path exercised by the cached offline demo or the review-gated live flow. Evaluation harnesses, fixtures, tests, and docs only. Sole exception: a crash-level mainline bug found during A-work — fix minimally, flag loudly, re-run the offline demo check.
- G3: one commit per task, full suite green, push to origin main, short Chinese report with numbers verbatim after each task.
- G4: demo-path freeze at 2026-07-03 evening stands; after that only docs and evaluation artifacts change until the deadline.

PHASE A — EVIDENCE HARDENING (now → 03 Jul evening)

A1 — NEGATIVE CONTROLS for the scorer (highest value per hour; pure evaluation code)
Purpose: prove the ruler can measure a difference before trusting what it measured. Build scripts/run_negative_controls.py reusing the existing scorer and existing blind-prediction artifacts UNCHANGED:
  a. Inverted-truth control: score the cached ULEZ full-pipeline predictions against a direction-inverted copy of the truth set; expect hit rate to collapse toward the complement.
  b. Shuffled-alignment control: score against truth sets with question↔fact alignment permuted (fixed seed, 20 permutations); report the permutation distribution and where the real 0.73 sits in it.
  c. (Conditional — only after the human verifies CC 2003): cross-case control — ULEZ predictions scored against CC 2003 truth and vice versa; expect ~chance.
Output: docs/evaluation/negative_controls.md + JSON artifacts. Report results verbatim, favorable or not. If controls do NOT collapse toward chance, that is a scorer-leniency finding — report it prominently; do not soften it and do not modify the scorer without explicit sign-off.

A2 — ADVERSARIAL INPUT SUITE (evaluation-only)
Create tests/fixtures/adversarial/ with at least: (1) a very long real public consultation document (>50k chars, public source), (2) a document with internally contradictory clauses, (3) off-topic junk text, (4) near-empty input, (5) a non-policy technical document. Run the extraction stage on each (mock always; real LLM too if a key is present) and RECORD actual behavior: schema-valid output? clean failure? confidence flags? Write docs/evaluation/adversarial_inputs.md — describe observed behavior, never aspirational behavior. Add regression tests asserting the current graceful behaviors (no crash; valid JSON or clean error). Any crash goes through the G2 exception path.

A3 — CC 2003 SECOND-CASE UNLOCK (gated on human verification)
Render every draft truth-set fact into docs/evaluation/cc2003_verification_checklist.md: id / fact / source URL / quote / current status, with a CONFIRM / REJECT / EDIT field per item, executable by the human in under an hour. When his decisions come back: apply exactly as instructed (待核实→已确认 only on explicit confirm), set headline_excluded=false only if ALL scored facts are confirmed, run the real blind backtest (k=5) on CC 2003, add it to the ablation/stability docs as case #2, then run A1c. No verification in time = case stays draft and excluded; no silent promotion, ever.

A4 — ROADMAP + LIMITATIONS DOC (deck source material)
Write docs/ROADMAP.md: the Phase B plan below, plus an honest current-limitations section — single fully-verified case, directional-only resolution, mock simulation as visualization aid, in-process background tasks, plus links to A1/A2 results. This feeds the "What's next" slide and judge Q&A verbatim.

PHASE B — PRODUCT BUILD (starts 2026-07-05; recorded now so the plan is committed; do not execute before the gate)

B1 — TRUTH-SET WORKBENCH (the moat). Make truth-set construction a product loop: LLM drafts facts+citations from post-implementation sources → human reviews per item in a UI (CONFIRM/REJECT/EDIT, status transitions, inline source quotes) → only fully-confirmed sets unlock scoring. Backend CRUD with schema validation and per-fact provenance; audit every human decision by reusing the ApprovalEvent pattern. Acceptance: a brand-new case goes from raw sources to a scored blind backtest without hand-editing JSON.

B2 — ABLATION-GATED FEATURE ENTRY. Codify in docs + a one-command harness: any prediction-affecting component (including any real multi-agent simulation behind the OASIS probe) must beat current mainline on the blind-backtest ablation across ALL verified cases before joining the default path. The mock simulation stays the honest default until something beats it.

B3 — REAL-FORMAT INGESTION. PDF upload + GOV.UK/URL fetch; parsing and chunking for >100-page documents; carry page/paragraph references through extraction so provenance labels point at page-level evidence. Acceptance: a real GOV.UK consultation PDF runs end-to-end with page-referenced claims.

B4 — RESOLUTION + CALIBRATION. Upgrade predictions to direction + magnitude band + time window (schema, prompts, scorer, truth-set format — versioned so ULEZ v1 results stay comparable). Track stated confidence per judgment and compute Brier-style calibration as cases accumulate; expose a calibration view. Re-run ULEZ + CC2003 as v2 baselines.

B5 — OPS HARDENING. Background tasks → persistent queue with retry; run-history UI (list, status, artifacts, verify buttons); multi-provider LLM config; implement the anchor_per_approval=true path; a mainnet cost/feasibility memo (731-byte payloads vs fees). Acceptance: a server restart mid-run loses nothing; two concurrent runs don't interfere.

B6 — WHAT-IF FORKING (the "sandbox" promise). Fork a reviewed case graph into variants, rerun judgment stages only, render a structured diff of conclusions between variants, with fork lineage recorded in the audit chain. Acceptance: an ULEZ £12.5-vs-£15 variant comparison.

Execution order within B: B1 → B2 → B4 → B3 → B6 → B5 unless overridden. Same permanent rules: no secrets, no self-initiated broadcasts, honesty notes maintained.
