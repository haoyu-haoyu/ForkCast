# Fork API

ForkCast forks let a human compare policy variants without re-extracting the source document. A fork always starts from a reviewed parent case graph, applies explicit JSON Patch edits, reruns only the judgment/simulation/report stages, and writes its own audit chain under the parent run.

No endpoint below broadcasts to Kaspa. Anchoring remains a separate human-approved action.

## Create A Fork

`POST /api/policy-runs/{run_id}/forks`

Creates `runs/{run_id}/forks/{fork_id}/`.

The parent must be reviewed:

- live runs must have `case_graph_approved.json` and `approval_event.json`;
- cached/anchored runs must have an `audit_manifest.json` with a `case_graph` entry.

Request:

```json
{
  "name": "charge £15.00",
  "case_graph_patches": [
    {
      "op": "add",
      "path": "/scenario_variant",
      "value": { "charge": "£15.00" }
    }
  ]
}
```

Supported patch operations are `add`, `replace`, and `remove`, using JSON Pointer paths. The patched case graph is validated against `schemas/case_graph.schema.json`.

Response:

```json
{
  "parent_run_id": "ulez_2023_phase2_deepseek",
  "fork_id": "fork_20260703T172200Z_charge_15_00",
  "name": "charge £15.00",
  "status": "AWAITING_ANCHOR_APPROVAL",
  "approval_event": {
    "stage": "fork_variant_review",
    "editor": "human",
    "actor": "human",
    "diff": [
      {
        "path": "/scenario_variant",
        "before": null,
        "after": { "charge": "£15.00" }
      }
    ],
    "patches": [
      {
        "op": "add",
        "path": "/scenario_variant",
        "value": { "charge": "£15.00" }
      }
    ],
    "approved_hash": "..."
  },
  "audit_manifest": {
    "chain_status": "fork_hash_chained",
    "human_approval_required_for_chain_anchor": true,
    "fork_lineage": {
      "parent_run_id": "ulez_2023_phase2_deepseek",
      "parent_head": "...",
      "fork_root_hash": "...",
      "formula": "sha256(parent_head || canonical_json(patch_diff))"
    }
  }
}
```

Fork artifact layout:

```text
runs/{run_id}/forks/{fork_id}/
  fork_input.json
  case_graph_approved.json
  approval_event.json
  agents.json
  simulation_events.json
  simulation_outputs.json
  impact_report.json
  audit_manifest.json
  status.json
```

The fork hash chain begins with `h0'`, where:

```text
h0' = sha256(parent_head || canonical_json(patch_diff))
```

This makes lineage explicit: the variant commitment cannot be separated from the parent commitment and the human-approved patch.

## Compare Forks

`GET /api/policy-runs/{run_id}/forks/compare?a={fork_id_a}&b={fork_id_b}`

Returns UI-ready side-by-side diffs. The frontend does not need to calculate changes.

Response shape:

```json
{
  "parent_run_id": "ulez_2023_phase2_deepseek",
  "a": { "fork_id": "fork_a", "name": "charge £12.50" },
  "b": { "fork_id": "fork_b", "name": "charge £15.00" },
  "dimensions": {
    "risk_timeline": [
      {
        "key": "implementation_period",
        "status": "changed",
        "changed_fields": ["risk_level", "signal"],
        "a": {
          "stage": "implementation_period",
          "signal": "£12.50 daily charge creates baseline affordability risk.",
          "risk_level": "medium"
        },
        "b": {
          "stage": "implementation_period",
          "signal": "£15.00 daily charge raises enforcement and affordability risk.",
          "risk_level": "high"
        }
      }
    ],
    "claims": [],
    "stakeholder_pressure": []
  },
  "summary": {
    "changed": 3,
    "unchanged": 0,
    "new": 0,
    "removed": 0
  }
}
```

Statuses are `changed`, `unchanged`, `new`, or `removed`.

## Verify Anchor API

`GET /api/anchors/{run_id}/verify`

Runs the existing verifier in process against the live Kaspa API, or against an injected fetcher in tests. It never shells out and never broadcasts.

Response:

```json
{
  "overall": "PASS",
  "mode": "hash_chain_head",
  "network": "testnet-10",
  "txid": "8a682481...",
  "checks": {
    "tx_payload_matches_anchor": {
      "status": "PASS",
      "note": "Kaspa transaction payload matches local kaspa_anchor.json payload."
    }
  },
  "links": [
    {
      "id": "h2",
      "stage": "approval_event",
      "status": "PASS",
      "expected": "...",
      "actual": "..."
    }
  ],
  "cache": {
    "hit": false,
    "ttl_seconds": 60
  }
}
```

The result is cached for 60 seconds per `(run_id, txid, network)`.

## Worked Example: ULEZ Charge Sensitivity

Create the baseline fork:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/policy-runs/ulez_2023_phase2_deepseek/forks \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "charge £12.50",
    "case_graph_patches": [
      {"op":"add","path":"/scenario_variant","value":{"charge":"£12.50"}}
    ]
  }'
```

Create the higher-charge fork:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/policy-runs/ulez_2023_phase2_deepseek/forks \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "charge £15.00",
    "case_graph_patches": [
      {"op":"add","path":"/scenario_variant","value":{"charge":"£15.00"}}
    ]
  }'
```

Compare:

```bash
curl -sS "http://127.0.0.1:8000/api/policy-runs/ulez_2023_phase2_deepseek/forks/compare?a={fork_a}&b={fork_b}"
```

The comparison returns `risk_timeline`, `claims`, and `stakeholder_pressure` arrays with both values attached for every changed or unchanged row.
