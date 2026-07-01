# Submission Checklist

## Conduct / DoraHacks

Core material:

- Working tool: React/Vite dashboard at `web/`, backed by cached ULEZ artifacts in `web/src/data/`.
- Run instructions: `README.md` quick start, dashboard command and Phase 1/2/4 commands.
- GitHub repo: include source, schemas, prompts, scripts, data contracts, docs and generated demo artifacts.
- README: one-line definition, before/after framing, local run commands, safety rules and known limitations.
- 90-second demo: use `docs/submission/DEMO_RUNBOOK.md`.
- ULEZ blind backtest report: `runs/ulez_2023_phase2_deepseek/backtest.md`.
- Backtest integrity explanation: `docs/methodology/backtest_integrity.md`.
- Human-control layer explanation: `docs/product/control_flow.md`.

What to emphasize:

- Control beats autonomy: four approval checkpoints, rollback/superseded history and hard limits.
- Agents are archetypes only; no real-person PII.
- No automatic chain action and no automatic stakeholder-weight changes.
- Blind backtest uses answer-isolated prediction, not mock events.

Still missing before final upload:

- Public GitHub URL.
- 90-second video file or live-demo link.
- Short project description field for DoraHacks.
- Final screenshots/GIFs if the submission form asks for media.

## Kaspa / DoraHacks

Core material:

- GitHub repo with `src/policy_impact_sandbox/phase4/kaspa_anchor.py` and Kaspa scripts.
- Integration note: `docs/submission/kaspa-integration.md`.
- Audit manifest example: `runs/ulez_2023_phase2_deepseek/audit_manifest.json`.
- Anchor package: `runs/ulez_2023_phase2_deepseek/kaspa_anchor.json`.
- True TN-10 tx id: `f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`.
- Explorer: `https://explorer-tn10.kaspa.org/txs/f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`.
- 3-5 minute demo script: use the outline below.

3-5 minute Kaspa demo script:

1. Problem: AI policy tools can produce reports, but governance teams need proof of exactly what was approved.
2. Show checkpoint 4: the human reviews report claims and the manifest before chain action.
3. Show payload: only manifest hash, case id, run id, stage metadata and approval policy go on-chain; AI reasoning stays off-chain.
4. Show tx: status anchored, TN-10 tx id and explorer link.
5. Verify: recompute manifest hash locally and compare it to the chain payload hash.
6. Boundary: no production covenant claimed; SilverScript/Covenants remain stretch/design only.

Still missing before final upload:

- 3-5 minute recorded Kaspa demo video.
- Public repo URL.
- Optional short clip opening the explorer page live.

## Cantor8 / Learner / Canton

Current status:

- Canton/Daml proof was not implemented. This was intentionally deferred because the mainline scope was Conduct + Kaspa + ULEZ blind backtest.
- There is no Canton LocalNet artifact, Daml model, ledger transaction or Canton submission proof in this MVP.

If submitting to a Canton-related track:

- Mark as not submitted or explicitly list as future work.
- Do not imply Canton integration exists.

Still missing:

- All Canton-specific evidence, if you decide to pursue it later.

## Final Upload Sanity Checks

- Confirm `.env` is not tracked and contains no secrets in any committed file.
- Confirm `.kaspa-wallet/` is ignored.
- Run `uv run pytest -q`.
- Run `cd web && npm test`.
- Run `cd web && npm run build`.
- Open the dashboard and click through the runbook once.
- Keep `docs/submission/PITCH_NOTES.md` open for judge Q&A.
