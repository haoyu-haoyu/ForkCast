# Policy Impact Sandbox MVP

Policy Impact Sandbox is a controllable AI workflow for policy/decision impact assessment. The MVP is scoped to one historical backtest case: the 2023 London ULEZ expansion.

In one sentence: it turns a policy memo into archetype agents, a replayable impact simulation, an answer-isolated historical backtest and a Kaspa-anchored audit trail.

Before: impact assessment is weeks of consultants, hearings, spreadsheets and fragmented traceability.

After: the same policy decision is reviewed through visible approval checkpoints, cached replay, blind R1-R6 backtest evidence and a verifiable manifest hash on Kaspa testnet.

Current implementation status:

- Mainline MVP is Conduct control layer + ULEZ blind backtest + Kaspa TN-10 audit anchoring.
- OASIS is treated as a runtime dependency probe, not a hard blocker.
- The demo uses deterministic mock simulation events with the same downstream contract.
- Project LLM calls use a DeepSeek/OpenAI-compatible client.
- Kaspa Phase 4 has a real TN-10 transaction: `f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`.
- Fetch.ai and Canton are intentionally out of scope until the Conduct/Kaspa/Ulez mainline is running.

## Demo-Ready Quick Start

Run the cached dashboard path:

```bash
uv sync
uv run pytest -q
cd web
npm install
npm run dev -- --port 5173
```

Then open `http://127.0.0.1:5173/` and follow `docs/submission/DEMO_RUNBOOK.md`.

Build the static dashboard for offline fallback:

```bash
cd web
npm run build
```

## Development Commands

```bash
uv sync --extra oasis
uv run pytest
uv run python scripts/probe_oasis.py
```

If `scripts/probe_oasis.py` fails because of missing API keys, dependency conflicts, or runtime cost concerns, continue with mock mode:

```bash
uv run python scripts/run_mock_simulation.py
```

Run Phase 1 case graph extraction with the configured project LLM:

```bash
export DEEPSEEK_API_KEY=<your local key>
uv run python scripts/run_phase1_case_graph.py
```

For local smoke tests without an external LLM:

```bash
uv run python scripts/run_phase1_case_graph.py --mock-llm
```

Run Phase 2 with DeepSeek-backed archetype generation and mock simulation:

```bash
export DEEPSEEK_API_KEY=<your local key>
uv run python scripts/augment_case_graph.py
uv run python scripts/run_phase2.py --run-id ulez_2023_phase2_deepseek --agent-count 36 --rounds 3
```

Run Phase 2 without an external LLM for local smoke tests:

```bash
uv run python scripts/run_phase2.py --mock-llm --run-id ulez_2023_phase2_mock --agent-count 36 --rounds 3
```

Run the Phase 3 dashboard:

```bash
cd web
npm install
npm run dev -- --port 5173
```

Then open `http://127.0.0.1:5173/`.

Run the live policy-analysis API for arbitrary new policy documents:

```bash
cp .env.example .env
# fill DEEPSEEK_API_KEY in .env; do not commit .env
uv run python scripts/run_api.py --port 8000
```

In a second terminal, run the dashboard. Vite proxies `/api` to `http://127.0.0.1:8000`:

```bash
cd web
npm run dev -- --port 5173
```

Use the `ULEZ selected` screen to paste or upload a new policy document and click `Run real analysis`.
That path calls DeepSeek-backed extraction, archetype generation, mock event generation for visualization context,
and LLM report generation. For non-ULEZ policies without a `truth_set`, the dashboard shows:
`无历史回测数据，仅提供影响分析` and does not display a historical backtest.

Prepare the Phase 4 Kaspa audit anchor package:

```bash
uv run python scripts/kaspa_anchor_manifest.py \
  --manifest runs/ulez_2023_phase2_deepseek/audit_manifest.json \
  --network testnet-10
```

This writes `runs/ulez_2023_phase2_deepseek/kaspa_anchor.json` and copies it into the dashboard data folder. Legacy ULEZ demo artifacts commit to the canonical audit manifest hash. New live policy runs use the hash-chain head described in `docs/HASH_CHAIN.md`.

The current demo artifact has already been broadcast to Kaspa `testnet-10` after explicit human approval:

- Tx id: `f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`
- Explorer: `https://explorer-tn10.kaspa.org/txs/f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`

Future broadcasts must use a local testnet wallet from environment variables and an explicit approval flag:

```bash
uv run --with kaspa python scripts/kaspa_broadcast_anchor.py --human-approved --amount-kas 1
```

To explicitly run the paid/live OASIS Reddit-like probe, set `OPENAI_API_KEY` and opt in:

```bash
OASIS_RUN_LIVE=1 uv run --extra oasis python scripts/probe_oasis.py
```

## Environment

Copy `.env.example` to `.env` locally when you need real integrations. Do not commit secrets.

```bash
cp .env.example .env
```

Project LLM calls read `LLM_API_KEY`/`LLM_BASE_URL`/`LLM_MODEL` first, then fall back to `DEEPSEEK_API_KEY`, `DEEPSEEK_BASE_URL=https://api.deepseek.com`, and `DEEPSEEK_MODEL=deepseek-chat`.

## Data Layout

- `data/cases/ulez_2023/truth_set.json`: verified historical facts for backtesting.
- `data/cases/ulez_2023/sources.md`: human-readable evidence list.
- `data/cases/ulez_2023/seed_policy.md`: compact policy brief used as extraction input.
- `data/cases/ulez_2023/case_graph.json`: Phase 1 structured case graph output.
- `data/cases/ulez_2023/case_graph_networkx.json`: JSON export from the NetworkX fallback graph.
- `runs/`: generated run artifacts.
- `runs/<run_id>/agents.json`: Phase 2 archetype agents.
- `runs/<run_id>/blind_prediction.json`: answer-isolated prediction prompt, sanitized context, and raw LLM prediction.
- `runs/<run_id>/simulation_events.json`: mock simulation event log and detected signals.
- `runs/<run_id>/impact_report.json`: stakeholder impact matrix, risk timeline, mitigations and confidence notes.
- `runs/<run_id>/backtest_result.json`: R1-R6 directional verdicts from blind prediction, not mock demo events.
- `runs/<run_id>/audit_manifest.json`: canonical JSON SHA-256 manifest with hash-chain links and head hash.
- `runs/<run_id>/kaspa_anchor.json`: Kaspa payload commitment package for the hash-chain head, with legacy manifest-hash verification still supported.
- `web/`: React + Vite dashboard for the 90-second controlled demo.
- `schemas/`: JSON Schemas for Phase 1+ contracts.
- `prompts/`: extraction/report prompts for Phase 1+.

## Safety Rules

- Agents are archetypes only, not real people.
- Agents must not add sources or alter stakeholder weights without user approval.
- Agents must not send Kaspa/Canton transactions automatically.
- Reports must state: simulation is decision support, not deterministic forecast.
- Backtest credibility comes from `blind_prediction.json`; mock simulation remains a dashboard/demo visualization aid.
- Kaspa anchoring commits only to a manifest hash or hash-chain head; AI reasoning and artifacts stay off-chain.
