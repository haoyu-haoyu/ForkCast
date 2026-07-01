# Safe Demo Version: demo-safe-v1

This document describes the backup version that can be used for submission if later product work breaks the app.

## Restore

If the git tag exists:

```bash
git checkout demo-safe-v1
```

If the working tree is unavailable, restore from the backup artifacts under `backups/`:

- `demo-safe-v1.bundle`: git bundle containing the safe commit and tag.
- `demo-safe-v1.tar.gz`: source archive generated from the safe tag.
- `demo-safe-v1-full-local.tar.gz`: local source/build archive excluding secrets, virtualenvs, node modules, logs and git metadata. This includes the built dashboard under `web/dist/`.

Restore from bundle:

```bash
git clone backups/demo-safe-v1.bundle policy-impact-sandbox-demo-safe-v1
cd policy-impact-sandbox-demo-safe-v1
git checkout demo-safe-v1
```

## Run

Install and verify:

```bash
uv sync
uv run pytest -q
cd web
npm install
npm test
npm run build
npm run dev -- --port 5173
```

Open:

```text
http://127.0.0.1:5173/
```

## 90 Second Demo Path

Click through this exact path:

1. `Before`
2. `ULEZ selected`
3. `Approve extraction`, then click `Approve`
4. `Approve agents`, then click `Approve`
5. `Run controls`, then click `Approve run`
6. `Simulation replay`
7. `Impact report`
8. `Blind backtest`
9. `Audit + Kaspa`
10. `Close`

## What Must Be Visible

- Blind backtest table reads the real R1-R6 result set.
- R1 is `PARTIAL`.
- R6 is `BALANCED HIT`.
- Prompt transparency shows the blind prompt and `No outcome tokens in prompt`.
- Audit + Kaspa shows:
  - status `anchored`
  - network `testnet-10`
  - payload size `731/25000`
  - tx id `f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`
  - explorer `https://explorer-tn10.kaspa.org/txs/f553f7bfd73b1ed81bd1fd71dbd43631b49c392e20699e82ba2cbc5b263b5123`

## Boundaries To State In The Demo

- Mock simulation is visualization only.
- Backtest credibility comes from `blind_prediction.json`.
- Any money or score framing is illustrative/demo estimate only.
- The project is decision support, not deterministic forecast.
- OASIS live mode and Canton are not part of this safe demo version.
