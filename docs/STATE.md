# Policy Impact Sandbox State Snapshot

Date: 2026-07-02 BST
Branch: `productization-live-policy-run`
Safe baseline: `demo-safe-v1` on `main` at `6d64f164400eeebba68d30aa26bd6c5770d86716`

## Phase 0 Test Results

- Python: `uv run pytest -q` -> `31 passed`; one known `StarletteDeprecationWarning` from `fastapi.testclient`.
- Frontend unit tests: `cd web && npm test` -> `9 passed`.
- Frontend production build: `cd web && npm run build` -> passed; Vite emitted `dist/index.html`, CSS, and JS assets.

## Repository Map

### `src/`

```text
src/policy_impact_sandbox/
  api.py                         FastAPI app for live policy runs.
  llm/
    config.py                    Environment-backed OpenAI-compatible LLM config.
    client.py                    DeepSeek/OpenAI-compatible JSON completion client.
  live_policy/
    generic_extract.py           Generic no-truth-set policy extraction.
    pipeline.py                  One-shot live analysis pipeline.
    report.py                    LLM impact report generator for new policies.
  phase1/
    extract.py                   ULEZ truth_set + seed policy -> case_graph.
    augment.py                   Adds missing ULEZ stakeholder groups.
    graph.py                     NetworkX fallback graph export.
  phase2/
    agents.py                    Archetype agent generation and coverage guard.
    audit.py                     Current canonical JSON and per-artifact manifest hashes.
    backtest.py                  R1-R6 scoring.
    blind_prediction.py          Answer-isolated blind prediction prompt/context.
    chat.py                      Deterministic persona answer helper.
    report.py                    Cached ULEZ impact report renderer.
    simulation.py                Policy mock simulation for Phase 2.
  phase4/
    kaspa_anchor.py              Kaspa manifest commitment payload builder/verifier.
  simulation/
    mock.py                      Phase 0 deterministic mock event generator.
    oasis_probe.py               OASIS dependency probe decision logic.
```

### `scripts/`

```text
scripts/
  run_api.py                     Starts `policy_impact_sandbox.api:app`.
  run_phase1_case_graph.py       Runs ULEZ Phase 1 extraction.
  augment_case_graph.py          Adds stakeholder groups to ULEZ case graph.
  run_phase2.py                  Runs ULEZ agents, blind prediction, mock simulation, report, backtest, audit.
  run_mock_simulation.py         Phase 0 mock fallback smoke path.
  probe_oasis.py                 OASIS import/probe; live only with explicit opt-in.
  kaspa_anchor_manifest.py       Prepares local Kaspa anchor record; records tx id if supplied.
  kaspa_create_testnet_wallet.py Creates TN-10 wallet secrets in `.env`.
  kaspa_broadcast_anchor.py      Broadcast path requiring `--human-approved` and TN-10 wallet env.
```

### `tests/`

```text
tests/
  test_policy_run_api.py         Live policy API tests with mocked LLM.
  test_policy_run_pipeline.py    Generic live run pipeline tests and no-truth-set check.
  test_phase2_*.py               Agents, blind prediction, simulation, report, backtest, chat, audit tests.
  test_phase4_kaspa_anchor.py    Kaspa anchor payload and verification tests.
  test_phase1_*.py               ULEZ case graph extraction/schema/CLI tests.
  test_llm_config.py             DeepSeek and generic LLM env precedence tests.
  test_mock_simulation.py        Mock event generator tests.
  test_oasis_probe.py            OASIS dependency probe tests.
  test_scripts_cli.py            CLI smoke tests.
```

### `docs/`

```text
docs/
  HACKATHON_TASKS.md             Verbatim task plan for the final work sprint.
  STATE.md                       This state snapshot.
  methodology/backtest_integrity.md
                                  Blind backtest isolation methodology.
  product/control_flow.md        Human-in-the-loop control design notes.
  submission/
    DEMO_RUNBOOK.md              90-second demo runbook.
    PITCH_NOTES.md               Pitch notes and judge Q&A.
    SAFE_DEMO_VERSION.md         Locked demo-safe version notes.
    SUBMISSION_CHECKLIST.md      Platform submission checklist.
    kaspa-integration.md         Kaspa integration submission notes.
```

### Frontend: `web/`

```text
web/
  package.json                   Vite/React scripts.
  vite.config.ts                 React plugin and `/api` proxy to `127.0.0.1:8000`.
  src/
    App.tsx                      Main dashboard cockpit UI and demo flow.
    livePolicy.ts                Frontend POST client for `/api/policy-runs`.
    control.ts                   Checkpoint state model for cached demo.
    data.ts                      Imports cached ULEZ JSON artifacts.
    rubric.ts                    R1-R6 labels.
    styles.css                   Dashboard styling.
    types.ts                     Shared frontend TypeScript interfaces.
    data/                        Cached ULEZ demo JSON copied into the frontend bundle.
```

## Live-Run Data Flow

Current live policy runs are one-shot and synchronous. They do not yet pause for review and they do not persist live-run artifacts to disk.

1. Client calls `POST /api/policy-runs`.
   - File: `src/policy_impact_sandbox/api.py`
   - Model: `PolicyRunRequest(policy_text, agent_count, rounds)`
2. `create_app().create_policy_run()` validates nonblank text.
3. `_default_llm_client()` creates `OpenAICompatibleLLMClient(LLMConfig.from_env())`.
   - Files: `src/policy_impact_sandbox/llm/config.py`, `src/policy_impact_sandbox/llm/client.py`
4. `run_policy_analysis(...)` orchestrates the live pipeline.
   - File: `src/policy_impact_sandbox/live_policy/pipeline.py`
5. `extract_generic_case_graph(policy_text, llm_client)` builds a no-truth-set extraction prompt.
   - File: `src/policy_impact_sandbox/live_policy/generic_extract.py`
   - Prompt: `prompts/case_graph_extraction.md`
   - Important isolation: the prompt contains `historical_truth_set: UNAVAILABLE` and does not load `truth_set.json`.
6. `generate_agent_profiles(case_graph, llm_client, target_count)` generates archetype agents.
   - File: `src/policy_impact_sandbox/phase2/agents.py`
   - Prompt: `prompts/agent_generation.md`
   - Coverage guard fills missing agents deterministically if the LLM returns too few.
7. `run_policy_mock_simulation(agents_payload, run_id, rounds)` creates mock event logs and qualitative signals.
   - File: `src/policy_impact_sandbox/phase2/simulation.py`
8. `generate_llm_impact_report(...)` generates the new-policy impact report.
   - File: `src/policy_impact_sandbox/live_policy/report.py`
   - Prompt: `prompts/impact_report_generation.md`
   - Report mode: `llm_policy_analysis_no_truth_set`
9. `build_audit_manifest(...)` hashes inline artifacts.
   - File: `src/policy_impact_sandbox/phase2/audit.py`
10. API returns JSON with:
    - `run_id`
    - `mode = live_policy_analysis`
    - `truth_set_status = {"status":"unavailable","message":"无历史回测数据，仅提供影响分析"}`
    - `case_graph`
    - `agents`
    - `simulation_events`
    - `impact_report`
    - `backtest_result = null`
    - `audit_manifest`

### Current Artifact Persistence

- Live API path: artifacts are inline-only in the HTTP response. No files are written under `runs/{run_id}/`.
- ULEZ Phase 2 CLI path: `scripts/run_phase2.py` writes:
  - `runs/{run_id}/simulation_config.json`
  - `runs/{run_id}/agents.json`
  - `runs/{run_id}/blind_prediction.json`
  - `runs/{run_id}/simulation_events.json`
  - `runs/{run_id}/impact_report.json`
  - `runs/{run_id}/impact_report.md`
  - `runs/{run_id}/backtest_result.json`
  - `runs/{run_id}/backtest.md`
  - `runs/{run_id}/persona_chat_sample.json`
  - `runs/{run_id}/audit_manifest.json`
  - `runs/{run_id}/kaspa_anchor.json` when `scripts/kaspa_anchor_manifest.py` is run.

Task 1 must change this to persisted asynchronous live runs under `runs/{run_id}/`.

## Blind Backtest Internals

### R1-R6 Definitions

- Rule-to-truth-set mapping lives in `src/policy_impact_sandbox/phase2/backtest.py` as `RULE_FACTS`.
- Human-readable labels live in `web/src/rubric.ts`.
- The requested rubric file is `backtest_rubric.md` at the repository root.
- Current scoring discipline:
  - Directional only, no exact numeric prediction required.
  - R3 is political salience/electoral risk only, not election-result prediction.
  - R6 uses `BALANCED HIT` when both benefit and burden are present.

### ULEZ Truth Set Format

- File: `data/cases/ulez_2023/truth_set.json`
- Schema: `schemas/truth_set.schema.json`
- Top-level keys:
  - `case_id`
  - `case_name`
  - `created_at`
  - `verification_policy`
  - `facts[]`
- Each `facts[]` item requires:
  - `id`
  - `category`
  - `requested_item`
  - `fact`
  - `confidence_status` in `已确认`, `待核实`, `未找到`
  - `sources[]` with `url` and `quote`
  - optional structured `value`
  - optional `notes`
- Human-readable evidence mirror: `data/cases/ulez_2023/sources.md`.

### Answer Isolation

- Enforcement function: `make_blind_case_context(...)` in `src/policy_impact_sandbox/phase2/blind_prediction.py`.
- It intentionally does not accept `truth_set`.
- It drops:
  - `evidence`
  - `evidence_fact_ids`
  - `evidence_note`
  - `graph`
  - `source_truth_set`
  - outcome entities of type `political_event`, `public_reaction`, `policy_outcome`, `report`, `poll`
- It keeps only allowed policy entity id `entity_ulez_policy`, cleaned stakeholders, constraints, and blind-safe empty assumptions.
- Stored leakage guard is in `blind_prediction.json`:
  - `truth_set_loaded_into_prompt: false`
  - `truth_set_file_read_by_prediction_step: false`
  - `excluded_case_graph_fields: [...]`

### Prediction Prompt Files

- Blind prediction system and user prompts are built in code by `build_blind_prediction_prompts(...)`.
  - File: `src/policy_impact_sandbox/phase2/blind_prediction.py`
  - There is no separate prompt file for blind prediction today.
- Agent generation prompt: `prompts/agent_generation.md`.
- Case graph extraction prompt: `prompts/case_graph_extraction.md`.
- New-policy report prompt: `prompts/impact_report_generation.md`.

### Scoring

- ULEZ Phase 2 calls:
  - `generate_blind_prediction(...)`
  - `evaluate_blind_prediction_backtest(blind_prediction, truth_set)`
  - `render_backtest_markdown(...)`
- File: `src/policy_impact_sandbox/phase2/backtest.py`
- Result files:
  - `runs/ulez_2023_phase2_deepseek/blind_prediction.json`
  - `runs/ulez_2023_phase2_deepseek/backtest_result.json`
  - `runs/ulez_2023_phase2_deepseek/backtest.md`
- Current cached verdicts:
  - R1 `PARTIAL`
  - R2 `HIT`
  - R3 `HIT`
  - R4 `HIT`
  - R5 `HIT`
  - R6 `BALANCED HIT`

## Manifest And Hashing

### Current Schema

- Schema file: `schemas/audit_manifest.schema.json`
- Builder: `build_audit_manifest(...)` in `src/policy_impact_sandbox/phase2/audit.py`
- Required manifest keys:
  - `case_id`
  - `run_id`
  - `entries[]`
- Current extra keys:
  - `generated_at`
  - `chain_status`
  - `human_approval_required_for_chain_anchor`
- Entry fields:
  - `stage`
  - `hash`
  - `actor`
  - `approval`
  - `artifact_uri`
  - `timestamp`

### Current SHA-256 Computation

Functions:

```python
def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
```

Current meaning:

- The hash is computed from the in-memory Python object passed to `build_audit_manifest`, not from raw file bytes.
- Serialization is JSON with:
  - sorted keys
  - UTF-8 encoding
  - separators `(",", ":")`
  - `ensure_ascii=False`
- No chained hash exists yet. Each entry independently hashes its artifact payload.
- The current Kaspa anchor commits to the canonical hash of the whole legacy `audit_manifest` object, not to a step-by-step chain head.

### Real Legacy Audit Manifest Example

Source file: `runs/ulez_2023_phase2_deepseek/audit_manifest.json`

```json
{
  "case_id": "ulez_2023_expansion",
  "run_id": "ulez_2023_phase2_deepseek",
  "generated_at": "2026-07-01T12:00:31.474732+00:00",
  "chain_status": "not_on_chain",
  "human_approval_required_for_chain_anchor": true,
  "entries": [
    {
      "stage": "case_graph",
      "hash": "20836c56fd7d15b49272009f086cddc090b82faa9cede84343c481b3ef7b517a",
      "actor": "conduct_core",
      "approval": "not_on_chain",
      "artifact_uri": "data/cases/ulez_2023/case_graph.json",
      "timestamp": "2026-07-01T12:00:31.474732+00:00"
    },
    {
      "stage": "simulation_config",
      "hash": "3a4a87030f58982c9e363842674cdba2c54891091c21a0643a9266ccb595262f",
      "actor": "conduct_core",
      "approval": "not_on_chain",
      "artifact_uri": "runs/ulez_2023_phase2_deepseek/simulation_config.json",
      "timestamp": "2026-07-01T12:00:31.474732+00:00"
    },
    {
      "stage": "agents",
      "hash": "345a655035c886c478083e6f9b8368f5fc325645b47486dc84c5fa25c70ab633",
      "actor": "conduct_core",
      "approval": "not_on_chain",
      "artifact_uri": "runs/ulez_2023_phase2_deepseek/agents.json",
      "timestamp": "2026-07-01T12:00:31.474732+00:00"
    },
    {
      "stage": "blind_prediction",
      "hash": "54548566b0bdb0e056b4607689a68990a2304067794828c0347223eb31d8f796",
      "actor": "conduct_core",
      "approval": "not_on_chain",
      "artifact_uri": "runs/ulez_2023_phase2_deepseek/blind_prediction.json",
      "timestamp": "2026-07-01T12:00:31.474732+00:00"
    },
    {
      "stage": "simulation_events",
      "hash": "0c389c74c2e43e1f53791405bcdf363008bbf079f57128c4bd6291b10a75281c",
      "actor": "conduct_core",
      "approval": "not_on_chain",
      "artifact_uri": "runs/ulez_2023_phase2_deepseek/simulation_events.json",
      "timestamp": "2026-07-01T12:00:31.474732+00:00"
    },
    {
      "stage": "impact_report",
      "hash": "e263a8825f943343cdccc791977393c07d643424b22b5dfda0b050743dcd86c7",
      "actor": "conduct_core",
      "approval": "not_on_chain",
      "artifact_uri": "runs/ulez_2023_phase2_deepseek/impact_report.json",
      "timestamp": "2026-07-01T12:00:31.474732+00:00"
    },
    {
      "stage": "backtest_result",
      "hash": "8e99896261ce4cefb6bdea72ccf5086653ed53f87243757079f8984caa4625fc",
      "actor": "conduct_core",
      "approval": "not_on_chain",
      "artifact_uri": "runs/ulez_2023_phase2_deepseek/backtest_result.json",
      "timestamp": "2026-07-01T12:00:31.474732+00:00"
    },
    {
      "stage": "persona_chat_sample",
      "hash": "53f9008d572504622f9e6c8b017e32c6e8c321271d7d74f885dbe5ee701ef929",
      "actor": "conduct_core",
      "approval": "not_on_chain",
      "artifact_uri": "runs/ulez_2023_phase2_deepseek/persona_chat_sample.json",
      "timestamp": "2026-07-01T12:00:31.474732+00:00"
    }
  ]
}
```

### Existing Tx ID References

Legacy anchored tx id:

`f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`

Referenced in:

- `README.md`
- `runs/ulez_2023_phase2_deepseek/kaspa_anchor.json`
- `web/src/data/kaspa_anchor.json`
- `docs/submission/kaspa-integration.md`
- `docs/submission/PITCH_NOTES.md`
- `docs/submission/SUBMISSION_CHECKLIST.md`
- `docs/submission/SAFE_DEMO_VERSION.md`

The task instruction also references the short form `f553f7bf...` in `docs/HACKATHON_TASKS.md`.

## Kaspa Integration

### SDK And Scripts

- Wallet creation: `scripts/kaspa_create_testnet_wallet.py`
- Broadcast script: `scripts/kaspa_broadcast_anchor.py`
- Anchor package builder: `scripts/kaspa_anchor_manifest.py`
- Core payload builder: `src/policy_impact_sandbox/phase4/kaspa_anchor.py`
- Runtime dependency for broadcast: Python `kaspa` package, installed only when explicitly used via `uv run --with kaspa ...`.

### Network

- Current network: `testnet-10`
- Explorer base: `https://explorer-tn10.kaspa.org`
- API evidence URL stored in anchor record:
  - `https://api-tn10.kaspa.org/transactions/f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`

### Payload Embedding

- Payload is `anchor["payload_canonical_json"].encode("utf-8")`.
- Broadcast call in `scripts/kaspa_broadcast_anchor.py`:
  - `wallet.accounts_send(..., destination=[PaymentOutput(recipient, kaspa_to_sompi(amount))], payload=payload)`
- Current payload content commits only to:
  - protocol
  - version
  - case id
  - run id
  - stage
  - manifest hash
  - manifest URI
  - artifact count
  - canonicalization description
  - human approval gate
  - off-chain reasoning policy
  - created timestamp
- Current payload size for anchored demo: 731 bytes.
- Practical payload limit constant: `KASPA_PAYLOAD_PRACTICAL_LIMIT_BYTES = 25000`.

### Manual-Approval Gate

- `scripts/kaspa_anchor_manifest.py --send` refuses without `--human-approved`.
- `scripts/kaspa_broadcast_anchor.py` refuses without `--human-approved`.
- `scripts/kaspa_broadcast_anchor.py` refuses if `KASPA_NETWORK != testnet-10`.
- `src/policy_impact_sandbox/phase4/kaspa_anchor.py` records:
  - `human_approval_required_for_chain_anchor: true`
  - `automatic_chain_actions_allowed: false`
  - `human_approval_gate.required_before_broadcast: true`
  - `human_approval_gate.automatic_broadcast_allowed: false`
- Current frontend displays the anchor but does not broadcast.

### Credentials And Funds Needed For Another Tx

Required local `.env` values:

- `KASPA_NETWORK=testnet-10`
- `KASPA_WALLET_FILENAME`
- `KASPA_WALLET_SECRET`
- `KASPA_RECIPIENT_ADDRESS`

Wallet creation script also writes:

- `KASPA_MNEMONIC`

Funds:

- A funded TN-10 wallet/account is required.
- Current scripts do not automate faucet solving or bypass any verification.

## LLM Client

### Providers

- Default provider label: `deepseek`.
- Client: `OpenAICompatibleLLMClient` in `src/policy_impact_sandbox/llm/client.py`.
- Environment precedence:
  - `LLM_API_KEY` over `DEEPSEEK_API_KEY`
  - `LLM_BASE_URL` over `DEEPSEEK_BASE_URL`
  - `LLM_MODEL` over `DEEPSEEK_MODEL`
- Defaults:
  - `DEEPSEEK_BASE_URL` fallback: `https://api.deepseek.com`
  - `DEEPSEEK_MODEL` fallback: `deepseek-chat`
  - `LLM_TIMEOUT_SECONDS` fallback: `60`

### Model And Temperature

- Model is read from `LLMConfig.model`.
- Temperature is hard-coded at `0.1` in `OpenAICompatibleLLMClient.complete_json(...)`.
- Streaming is disabled.

### Mock Mode

- ULEZ Phase 1 mock: `DeterministicMockLLMClient` in `src/policy_impact_sandbox/phase1/extract.py`.
- ULEZ Phase 2 agent mock: `DeterministicAgentLLMClient` in `src/policy_impact_sandbox/phase2/agents.py`; returns empty agents, then coverage guard fills deterministic profiles.
- ULEZ blind prediction mock: `DeterministicBlindLLMClient` in `src/policy_impact_sandbox/phase2/blind_prediction.py`.
- CLI flag: `scripts/run_phase2.py --mock-llm`.
- Live API tests inject a fake client through `create_app(llm_client_factory=...)`.

### Seeds

- `scripts/run_phase2.py` writes `random_seed: 20260701` into `simulation_config.json`.
- `src/policy_impact_sandbox/simulation/mock.py` uses `random.Random(random_seed)`.
- `src/policy_impact_sandbox/phase2/simulation.py` is deterministic by agent order and round count but uses current timestamps.
- No seed is set for LLM calls.

## Configuration

### Environment Variables Read By Code

- `LLM_PROVIDER`
  - Read in `src/policy_impact_sandbox/llm/config.py`.
  - Default: `deepseek`.
- `LLM_API_KEY`
  - Read in `src/policy_impact_sandbox/llm/config.py`.
  - Overrides `DEEPSEEK_API_KEY`.
- `DEEPSEEK_API_KEY`
  - Read in `src/policy_impact_sandbox/llm/config.py`.
  - Required for real live LLM if `LLM_API_KEY` is unset.
- `LLM_BASE_URL`
  - Read in `src/policy_impact_sandbox/llm/config.py`.
  - Overrides `DEEPSEEK_BASE_URL`.
- `DEEPSEEK_BASE_URL`
  - Read in `src/policy_impact_sandbox/llm/config.py`.
  - Default fallback: `https://api.deepseek.com`.
- `LLM_MODEL`
  - Read in `src/policy_impact_sandbox/llm/config.py`.
  - Overrides `DEEPSEEK_MODEL`.
- `DEEPSEEK_MODEL`
  - Read in `src/policy_impact_sandbox/llm/config.py`.
  - Default fallback: `deepseek-chat`.
- `LLM_TIMEOUT_SECONDS`
  - Read in `src/policy_impact_sandbox/llm/config.py`.
  - Default fallback: `60`.
- `OPENAI_API_KEY`
  - Read in `scripts/probe_oasis.py`.
  - Required only for explicit live OASIS probe.
- `OASIS_RUN_LIVE`
  - Read in `scripts/probe_oasis.py`.
  - Must equal `1` for live OASIS probe.
- `KASPA_NETWORK`
  - Read in `scripts/kaspa_broadcast_anchor.py`.
  - Must be `testnet-10`.
- `KASPA_WALLET_FILENAME`
  - Read in `scripts/kaspa_broadcast_anchor.py`.
- `KASPA_WALLET_SECRET`
  - Read in `scripts/kaspa_broadcast_anchor.py`.
- `KASPA_RECIPIENT_ADDRESS`
  - Read in `scripts/kaspa_broadcast_anchor.py`.

### Environment Variables Written By Code

- `scripts/kaspa_create_testnet_wallet.py` writes to local `.env`:
  - `KASPA_NETWORK`
  - `KASPA_WALLET_FILENAME`
  - `KASPA_WALLET_SECRET`
  - `KASPA_MNEMONIC`
  - `KASPA_RECIPIENT_ADDRESS`

### Variables Present In `.env.example` But Not Currently Read

- `SIMULATION_MODE`
- `MAX_AGENTS`
- `MAX_ROUNDS`
- `MAX_LLM_CALLS_PER_RUN`
- `KASPA_RPC_URL`

### Required By Mode

Demo/offline cached ULEZ mode:

- No environment variables required.
- Uses `web/src/data/*.json`.
- No network, LLM, OASIS, or Kaspa runtime dependency.

Live policy analysis mode:

- `DEEPSEEK_API_KEY` or `LLM_API_KEY` is required.
- Optional:
  - `DEEPSEEK_BASE_URL` / `LLM_BASE_URL`
  - `DEEPSEEK_MODEL` / `LLM_MODEL`
  - `LLM_TIMEOUT_SECONDS`

Anchoring / broadcast mode:

- Preparing an anchor record does not require secrets.
- Broadcasting requires:
  - `KASPA_NETWORK=testnet-10`
  - `KASPA_WALLET_FILENAME`
  - `KASPA_WALLET_SECRET`
  - `KASPA_RECIPIENT_ADDRESS`
  - funded TN-10 wallet
  - explicit `--human-approved`

OASIS live probe stretch:

- `OPENAI_API_KEY`
- `OASIS_RUN_LIVE=1`
- optional dependency group `uv sync --extra oasis`

## Known Gaps And TODOs

- Live API is synchronous and one-shot; it does not yet support `RECEIVED -> EXTRACTING -> AWAITING_REVIEW -> ...`.
- Live API does not persist runs under `runs/{run_id}/`.
- Live API has no GET/PATCH/approve endpoints for review.
- Current audit manifest is per-artifact independent hashing, not a chained approval-aware hash chain.
- Existing Kaspa tx anchors the legacy manifest hash, not a new hash-chain head.
- No independent verifier script exists yet.
- Frontend review screen is not yet driven by async run status polling.
- Frontend persona chat is still deterministic/local, not a live LLM chat endpoint.
- Ablation baseline harness does not exist yet.
- Stability/sensitivity harness does not exist yet.
- Congestion Charge 2003 case is not scaffolded.
- Claim provenance labels are not implemented.
- `SIMULATION_MODE`, `MAX_AGENTS`, `MAX_ROUNDS`, and `MAX_LLM_CALLS_PER_RUN` are documented in `.env.example` but are not enforced by code.
- Current Phase 2 mock simulation uses timestamps, so artifact hashes can change across reruns even when qualitative structure is deterministic.
