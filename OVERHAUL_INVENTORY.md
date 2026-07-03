# UI Overhaul — Content Inventory (Phase 0 safety net)

Programmatically enumerated from the live DOM (all 10 demo steps, persistent chrome)
plus source-derived states for the live-run path (App.tsx `LivePolicyResultPanel`).
Raw DOM dump: `overhaul_inventory_dom.json` (same capture, machine-readable).

**Rule: the finished redesign must check off 100% of this list. Restructure = rearrange, never remove.**

## Persistent chrome (every screen)

- [ ] Topbar: ForkCast wordmark + subtitle "Policy impact sandbox — control beats autonomy"
- [ ] Topbar: "● Demo Mode" pill · "Demo time remaining 01:14 / 01:30" tile · Scenario tile ("London ULEZ Expansion") · Persona tile ("Policy Maker") · PM avatar chip · **Rollback button (functional)**
- [ ] Timeline rail: heading "90-Second Demo Flow", "Step N of 10", 10 clickable steps with time ranges (0-8s … 88-90s) and checkpoint dots on the 4 checkpoint steps
- [ ] Side panel — Persona chat: heading, select with 18 persona options, question textarea (default "Why do you support or oppose this policy?"), answer block, caption "Archetype only · no real-person PII" (PROTECTED)
- [ ] Side panel — Audit Manifest: facts Run ID / Created / Created by / Scenario / Policy Option / Data Sources / Artifacts / Status
- [ ] Side panel — Kaspa Anchoring mini block with f553… explorer link
- [ ] Side panel — Hard limits (PROTECTED, all 5): No automatic chain action · No automatic weight changes · No real-person PII · Archetypes only · Decision support only
- [ ] Side panel — Checkpoint history (event log fed by approve/reject/edit actions)
- [ ] Status dock: Run ID / Scenario / Policy Option / Simulation Window 90 Days / Population 8.9M / Data Freshness Cached 2026-07-01 / Model Version v0.3.0 / System Status Operational

## Step 1 — Before (0-8s)

- [ ] Heading "Legacy impact assessment" + large copy (weeks of consultants…)
- [ ] Metrics: Typical cycle 3-8 weeks · Traceability Fragmented · Human control Late review
- [ ] Process strip: Policy memo → Consultants → Hearings → Spreadsheet → Board pack

## Step 2 — ULEZ selected / Checkpoint Control Panel (8-16s)

- [ ] Title "Checkpoint Control Panel" + "Human-in-the-loop at every critical step" + Overall status "In progress"
- [ ] 4 checkpoint summary cards (Extraction Review approved; Agent Review, Simulation Replay, Impact Report pending), each with 4 metrics and an **Open checkpoint** button (navigates)
  - Card 1: Data sources 18/18 · Stakeholders 9 · Coverage Blind-safe · Issues 0
  - Card 2: Agent recommendation Proceed · Archetypes 36 · Policy alignment High · Risks flagged 2
  - Card 3: Simulation window 90 days · Events cached 128 · Key signals 6 · Mode Replay
  - Card 4: Claims reviewed 6 · Rubric mode Blind · Kaspa anchor Live tx · Disclaimers On
- [ ] Social Feed Simulation Preview (5 mini events, channel badges, stance chips) + **View full stream** button
- [ ] Blind Rubric Coverage (R1-R6 compact rows with verdict pills) + hit strip (Rubric covered 5/6 · Partial R1 · Mechanism Keyword rubric) + **View detailed rubric report** button
- [ ] Impact Summary list: Prediction isolation No outcome data · Prompt scan No outcome tokens · Kaspa anchoring Testnet tx live · Report mode Decision support · **Human grading: Pending - see docs/evaluation/ulez_human_adjudication.md (PROTECTED)**
- [ ] Truth Status box: "ULEZ historical case verified" + "New policies show impact analysis only until a truth_set exists."
- [ ] Live-run entry: "Run a new policy document" + explainer, **Upload text / markdown file picker**, policy textarea, **Run real analysis** button, run-status pill, error note area, result panel (see Live-run path)

## Step 3 — Approve extraction / Checkpoint 1 (16-28s)

- [ ] Title + "Agent proposes stakeholders and assumptions. It cannot proceed until a human approves or edits."
- [ ] **ActionCluster: Approve / Adjust / Reject (functional: drives checkpoint state + history)**
- [ ] Stakeholders list (10 rows: name, archetype group, prior stance) each with **remove (X) button (functional)**
- [ ] **Add missing stakeholder input + Add button (functional, logs edit event)**
- [ ] Assumptions sheet (5 rows: status label "Pending verification" + statement with outcome numbers stripped)

## Step 4 — Approve agents / Checkpoint 2 (28-40s)

- [ ] Title + archetype disclaimer copy; **Approve (gated/blocked until CP1) / Adjust / Reject**
- [ ] Composition grid: 9 stakeholder groups, count + **range slider each**
- [ ] Persona controls: 10 persona rows, **click toggles disabled state (functional, logs edit)**

## Step 5 — Run controls / Checkpoint 3 (40-46s)

- [ ] Title + "Approve scale, rounds, budget and seed. OASIS live is disabled; mock replay is the MVP path."
- [ ] **Approve run (gated) / Adjust / Reject**
- [ ] Number controls: Agent count (10-200) · Rounds (1-5) · LLM budget cap (10-200); **Lock seed checkbox**
- [ ] Buttons: **Replay cached run** · **Run live sample** (toggles live sample feed) · **Downscale** (clamps agent count ≤18)

## Step 6 — Simulation replay (46-52s)

- [ ] Title + cached/live-sample caption; disclaimer pill "simulation is decision support, not deterministic forecast" (PROTECTED)
- [ ] Event feed (26 cached / 12 live-sample events): archetype, round, type, content; stance_change rows highlighted

## Step 7 — Impact report (52-66s)

- [ ] Method note + evidence pill "Evidence: blind_prediction.json"
- [ ] PROTECTED note: "Any dashboard score or monetary framing in this view is illustrative / demo estimate only. Automated R1-R6 verdicts are keyword-rubric signal coverage; human adjudication is the grading path."
- [ ] Risk timeline (3 rows: stage, risk level, signal)
- [ ] Claim review (6 rows: rule id, claim, provenance pill, **Delete/Restore toggle (functional)**, **Downgrade wording button**)
- [ ] Mitigation options (3 cards)
- [ ] Claims audit table: head (Claim / Provenance / Evidence pointer), PROTECTED notice "This report predates provenance classification and is anchored; claims are shown unclassified.", 8 rows with "Unclassified (legacy report)" pills (PROTECTED label) + evidence pointers

## Step 8 — Blind rubric (66-80s)

- [ ] Title + "ForkCast generates answer-isolated blind predictions; the prediction step does not read outcome data."
- [ ] PROTECTED caption: "Automated keyword-rubric verdicts — signal coverage, not semantic verification. See negative controls & human adjudication."
- [ ] Source line: "Source: runs/ulez_2023_phase2_deepseek/backtest_result.json · rubric: backtest_rubric.md"
- [ ] Outcome-token scan pill: "No outcome tokens in prompt" (computed from forbidden-token scan)
- [ ] R1-R6 table: Rule / Rubric item / Blind prediction signal / Real outcome (English display translation) / Verdict pills (PARTIAL, HIT ×4, BALANCED HIT)
- [ ] Footnote: "Display translation — canonical data lives in the anchored run artifacts."
- [ ] Prompt transparency: PROTECTED copy "Prediction function does not load truth_set. Stored prompt is inspectable and scanned for outcome tokens." + system-prompt <pre>

## Step 9 — Audit + Kaspa / Checkpoint 4 (80-88s)

- [ ] Title + "Manifest and chain payload are inspectable. This testnet anchor was broadcast only after checkpoint-4 human approval."
- [ ] **Approve report (gated) / Adjust / Reject**
- [ ] Audit meta: Created 2026-07-01 · Run ID ulez_2023_phase2_deepseek · Data freshness Cached 2026-07-01 replay
- [ ] Audit rows (8 artifacts: case_graph, simulation_config, agents, blind_prediction, simulation_events, impact_report, backtest_result, persona_chat_sample) each with hash + approval status
- [ ] Kaspa payload anchoring block: "Status: anchored. User approval remains required before any future transaction broadcast." · Network testnet-10 · Payload bytes 731/25000 · Explorer explorer-tn10.kaspa.org
- [ ] Hash stack: Manifest hash (e9f71f…) · Payload hash (93b99f…) · Kaspa tx id (f553f7…)
- [ ] **Open Kaspa explorer link → explorer-tn10.kaspa.org/txs/f553…** 
- [ ] Payload canonical JSON <pre>
- [ ] **Approve anchored payload review / Refuse on-chain anchor buttons (functional, set chain decision pill pending/payload_approved/refused)**

## Step 10 — Close (88-90s)

- [ ] "Weeks to hours, with the human still in control." + supporting copy
- [ ] Metrics: Demo run 90 sec · Prediction Blind · Autonomy Gated

## Live-run path (source-derived: CaseSelectScreen + LivePolicyResultPanel states)

- [ ] Empty state: "Result will appear here" + cached-replay explainer
- [ ] Status pill sequence: idle → running ("Running DeepSeek analysis...") → awaiting_review → approving → succeeded / failed; error note on failure
- [ ] FAILED state: run_id, "Run failed at <stage>", FAILED pill, error text
- [ ] AWAITING_REVIEW state: run_id + case-name header, "Human review required" pill, Editable stakeholders table (name, stance, **weight number input 0-3 step 0.1, functional**), Assumptions (status: statement, low-confidence highlight driven by `=== "已确认"` logic on raw data), Visible diff block (diff lines `path: before → after` or "No human edits saved yet."), **Save review edits** + **Approve and continue** buttons, `window.confirm("No changes were made — approve anyway?")` (PROTECTED)
- [ ] Succeeded state: run_id + case name, truth-set message pill (displayEnglish), Extracted stakeholders (5), "Generated archetypes: N archetype agents · no real-person PII", Report signals (3), Mitigation options (2), Audit hash chain (Head hash + h-links id/stage/hash), Human approval diff (recorded), report disclaimer note
- [ ] Polling behavior `pollPolicyRun` (1s interval, terminal statuses) — logic, must remain untouched

## Invariant text (never reworded, restyle only)

All PROTECTED items above, plus: all disclaimer/limit lines, provenance badge labels
(Document-cited / Inferred from document / Model prior / Unclassified (legacy report)),
displayEnglish.ts map keys byte-exact, English-only UI.
