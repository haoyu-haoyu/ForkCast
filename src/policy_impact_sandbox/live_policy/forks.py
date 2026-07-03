from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable, Protocol

from jsonschema import Draft202012Validator

from policy_impact_sandbox.live_policy.runs import diff_json
from policy_impact_sandbox.live_policy.report import generate_llm_impact_report
from policy_impact_sandbox.phase2.agents import generate_agent_profiles
from policy_impact_sandbox.phase2.audit import canonical_json, canonical_sha256, chained_sha256
from policy_impact_sandbox.phase2.simulation import run_policy_mock_simulation


class JSONLLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


class ForkNotFound(KeyError):
    pass


class ParentRunNotReviewed(RuntimeError):
    pass


class JsonPatchError(ValueError):
    pass


class PolicyForkManager:
    def __init__(
        self,
        *,
        run_root: str | Path,
        llm_client_factory: Callable[[], JSONLLMClient],
    ) -> None:
        self.run_root = Path(run_root)
        self.llm_client_factory = llm_client_factory
        self._case_graph_validator = Draft202012Validator(
            json.loads(Path("schemas/case_graph.schema.json").read_text(encoding="utf-8"))
        )

    def create_fork(self, parent_run_id: str, name: str, case_graph_patches: list[dict[str, Any]]) -> dict[str, Any]:
        if not name.strip():
            raise ValueError("fork name is required")
        if not case_graph_patches:
            raise ValueError("case_graph_patches is required")

        parent = self._load_reviewed_parent(parent_run_id)
        parent_case_graph = parent["case_graph"]
        variant_case_graph = apply_json_patch(parent_case_graph, case_graph_patches)
        self._case_graph_validator.validate(variant_case_graph)

        patch_diff = {
            "patches": case_graph_patches,
            "changes": diff_json(parent_case_graph, variant_case_graph),
        }
        fork_id = self._new_fork_id(parent_run_id, name)
        fork_dir = self._fork_dir(parent_run_id, fork_id)
        fork_dir.mkdir(parents=True, exist_ok=False)

        fork_input = {
            "parent_run_id": parent_run_id,
            "fork_id": fork_id,
            "name": name,
            "created_at": _now(),
            "parent_head": parent["parent_head"],
            "case_graph_patches": case_graph_patches,
            "patch_diff": patch_diff,
        }
        approval_event = {
            "timestamp": _now(),
            "stage": "fork_variant_review",
            "editor": "human",
            "actor": "human",
            "diff": patch_diff["changes"],
            "patches": case_graph_patches,
            "approved_hash": canonical_sha256(variant_case_graph),
        }

        target_count = max(parent["agent_count"], len(variant_case_graph.get("stakeholders", [])))
        rounds = parent["rounds"]
        llm_client = self.llm_client_factory()
        agents_payload = generate_agent_profiles(
            case_graph=variant_case_graph,
            llm_client=llm_client,
            target_count=target_count,
        )
        simulation_result = run_policy_mock_simulation(
            agents_payload=agents_payload,
            run_id=f"{parent_run_id}:{fork_id}",
            rounds=rounds,
        )
        simulation_outputs = {
            "agents": agents_payload,
            "simulation_events": simulation_result,
        }
        impact_report = generate_llm_impact_report(
            case_graph=variant_case_graph,
            agents_payload=agents_payload,
            simulation_result=simulation_result,
            llm_client=llm_client,
        )
        artifacts = {
            "fork_input": (str(fork_dir / "fork_input.json"), fork_input),
            "case_graph_approved": (str(fork_dir / "case_graph_approved.json"), variant_case_graph),
            "approval_event": (str(fork_dir / "approval_event.json"), approval_event),
            "simulation_outputs": (str(fork_dir / "simulation_outputs.json"), simulation_outputs),
            "report": (str(fork_dir / "impact_report.json"), impact_report),
        }
        audit_manifest = build_fork_audit_manifest(
            parent_run_id=parent_run_id,
            fork_id=fork_id,
            case_id=variant_case_graph["case_id"],
            parent_head=parent["parent_head"],
            patch_diff=patch_diff,
            approval_event=approval_event,
            artifacts=artifacts,
        )
        status = {
            "parent_run_id": parent_run_id,
            "fork_id": fork_id,
            "name": name,
            "status": "AWAITING_ANCHOR_APPROVAL",
            "updated_at": _now(),
            "anchor_status": "not_prepared",
        }

        _write_json(fork_dir / "fork_input.json", fork_input)
        _write_json(fork_dir / "case_graph_approved.json", variant_case_graph)
        _write_json(fork_dir / "approval_event.json", approval_event)
        _write_json(fork_dir / "agents.json", agents_payload)
        _write_json(fork_dir / "simulation_events.json", simulation_result)
        _write_json(fork_dir / "simulation_outputs.json", simulation_outputs)
        _write_json(fork_dir / "impact_report.json", impact_report)
        _write_json(fork_dir / "audit_manifest.json", audit_manifest)
        _write_json(fork_dir / "status.json", status)

        return {
            **status,
            "case_graph": variant_case_graph,
            "approval_event": approval_event,
            "audit_manifest": audit_manifest,
        }

    def compare_forks(self, parent_run_id: str, a: str, b: str) -> dict[str, Any]:
        fork_a = self._load_fork(parent_run_id, a)
        fork_b = self._load_fork(parent_run_id, b)
        report_a = fork_a["impact_report"]
        report_b = fork_b["impact_report"]
        dimensions = {
            "risk_timeline": compare_records(
                report_a.get("risk_timeline", []),
                report_b.get("risk_timeline", []),
                key_fields=("stage",),
            ),
            "claims": compare_records(
                report_a.get("claims_audit_table", []),
                report_b.get("claims_audit_table", []),
                key_fields=("id", "claim"),
            ),
            "stakeholder_pressure": compare_records(
                report_a.get("stakeholder_impact_matrix", []),
                report_b.get("stakeholder_impact_matrix", []),
                key_fields=("stakeholder_id", "name"),
            ),
        }
        summary = {"changed": 0, "unchanged": 0, "new": 0, "removed": 0}
        for rows in dimensions.values():
            for row in rows:
                summary[row["status"]] += 1
        return {
            "parent_run_id": parent_run_id,
            "a": {"fork_id": a, "name": fork_a["status"].get("name", a)},
            "b": {"fork_id": b, "name": fork_b["status"].get("name", b)},
            "dimensions": dimensions,
            "summary": summary,
        }

    def _load_reviewed_parent(self, parent_run_id: str) -> dict[str, Any]:
        parent_dir = self.run_root / parent_run_id
        if not parent_dir.exists():
            raise FileNotFoundError(f"parent run not found: {parent_run_id}")

        status_path = parent_dir / "status.json"
        if status_path.exists():
            approved_path = parent_dir / "case_graph_approved.json"
            approval_path = parent_dir / "approval_event.json"
            if not approved_path.exists() or not approval_path.exists():
                raise ParentRunNotReviewed("parent run must have a human-approved case graph before forking")
            case_graph = _read_json(approved_path)
            policy_input = _maybe_read_json(parent_dir / "input.json") or {}
            audit_manifest = _maybe_read_json(parent_dir / "audit_manifest.json")
            return {
                "case_graph": case_graph,
                "parent_head": _parent_head(audit_manifest, _read_json(approval_path)),
                "agent_count": int(policy_input.get("agent_count") or len(case_graph.get("stakeholders", [])) or 1),
                "rounds": int(policy_input.get("rounds") or 2),
            }

        audit_manifest_path = parent_dir / "audit_manifest.json"
        if not audit_manifest_path.exists():
            raise ParentRunNotReviewed("parent run must be reviewed or have an audit manifest before forking")
        audit_manifest = _read_json(audit_manifest_path)
        case_entry = _entry_for_stage(audit_manifest, "case_graph")
        case_graph = _read_json(_resolve_artifact_path(parent_dir, case_entry["artifact_uri"]))
        simulation_config = _maybe_read_json(parent_dir / "simulation_config.json") or {}
        return {
            "case_graph": case_graph,
            "parent_head": _parent_head(audit_manifest, audit_manifest),
            "agent_count": int(simulation_config.get("agent_count") or len(case_graph.get("stakeholders", [])) or 1),
            "rounds": int(simulation_config.get("rounds") or 2),
        }

    def _load_fork(self, parent_run_id: str, fork_id: str) -> dict[str, Any]:
        fork_dir = self._fork_dir(parent_run_id, fork_id)
        if not fork_dir.exists():
            raise ForkNotFound(fork_id)
        return {
            "status": _read_json(fork_dir / "status.json"),
            "impact_report": _read_json(fork_dir / "impact_report.json"),
            "audit_manifest": _read_json(fork_dir / "audit_manifest.json"),
        }

    def _new_fork_id(self, parent_run_id: str, name: str) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "variant"
        slug = slug[:40]
        candidate = f"fork_{timestamp}_{slug}"
        suffix = 1
        while self._fork_dir(parent_run_id, candidate).exists():
            suffix += 1
            candidate = f"fork_{timestamp}_{slug}_{suffix}"
        return candidate

    def _fork_dir(self, parent_run_id: str, fork_id: str) -> Path:
        return self.run_root / parent_run_id / "forks" / fork_id


def build_fork_audit_manifest(
    *,
    parent_run_id: str,
    fork_id: str,
    case_id: str,
    parent_head: str,
    patch_diff: dict[str, Any],
    approval_event: dict[str, Any],
    artifacts: dict[str, tuple[str, Any]],
) -> dict[str, Any]:
    required = ["fork_input", "case_graph_approved", "approval_event", "simulation_outputs", "report"]
    missing = [stage for stage in required if stage not in artifacts]
    if missing:
        raise ValueError(f"Missing fork audit artifacts: {', '.join(missing)}")

    timestamp = _now()
    fork_root_hash = hashlib.sha256((parent_head + canonical_json(patch_diff)).encode("utf-8")).hexdigest()
    links: list[dict[str, Any]] = [
        {
            "id": "h0'",
            "stage": "fork_lineage",
            "payload_hash": canonical_sha256(patch_diff),
            "previous_hash": parent_head,
            "hash": fork_root_hash,
        }
    ]
    previous = fork_root_hash
    for index, stage in enumerate(required, start=1):
        payload = artifacts[stage][1]
        payload_hash = canonical_sha256(payload)
        link_hash = chained_sha256(previous, payload)
        links.append(
            {
                "id": f"h{index}'",
                "stage": stage,
                "payload_hash": payload_hash,
                "previous_hash": previous,
                "hash": link_hash,
            }
        )
        previous = link_hash

    entries = []
    for stage in required:
        artifact_uri, payload = artifacts[stage]
        link = next(item for item in links if item["stage"] == stage)
        entries.append(
            {
                "stage": stage,
                "hash": canonical_sha256(payload),
                "chain_link_hash": link["hash"],
                "actor": "human" if stage == "approval_event" else "conduct_core",
                "approval": "human_approved" if stage == "approval_event" else "not_on_chain",
                "artifact_uri": artifact_uri,
                "timestamp": timestamp,
            }
        )

    return {
        "case_id": case_id,
        "run_id": fork_id,
        "parent_run_id": parent_run_id,
        "generated_at": timestamp,
        "chain_status": "fork_hash_chained",
        "human_approval_required_for_chain_anchor": True,
        "head_hash": previous,
        "fork_lineage": {
            "parent_run_id": parent_run_id,
            "parent_head": parent_head,
            "patch_diff": patch_diff,
            "fork_root_hash": fork_root_hash,
            "formula": "sha256(parent_head || canonical_json(patch_diff))",
        },
        "hash_chain": {
            "canonicalization": "json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')",
            "links": links,
            "head_hash": previous,
        },
        "approval_event": approval_event,
        "entries": entries,
    }


def apply_json_patch(document: dict[str, Any], patches: list[dict[str, Any]]) -> dict[str, Any]:
    output = deepcopy(document)
    for patch in patches:
        op = patch.get("op")
        path = patch.get("path")
        if op not in {"add", "replace", "remove"} or not isinstance(path, str):
            raise JsonPatchError(f"Invalid JSON patch operation: {patch!r}")
        if op in {"add", "replace"} and "value" not in patch:
            raise JsonPatchError(f"JSON patch operation requires value: {patch!r}")
        _apply_one(output, op, path, patch.get("value"))
    return output


def compare_records(a_items: list[Any], b_items: list[Any], *, key_fields: tuple[str, ...]) -> list[dict[str, Any]]:
    a_by_key = {_record_key(item, key_fields, index): item for index, item in enumerate(_records(a_items))}
    b_by_key = {_record_key(item, key_fields, index): item for index, item in enumerate(_records(b_items))}
    output = []
    for key in sorted(set(a_by_key) | set(b_by_key)):
        a_value = a_by_key.get(key)
        b_value = b_by_key.get(key)
        if a_value is None:
            status = "new"
            changed_fields = sorted(b_value.keys()) if isinstance(b_value, dict) else []
        elif b_value is None:
            status = "removed"
            changed_fields = sorted(a_value.keys()) if isinstance(a_value, dict) else []
        else:
            changed_fields = _changed_fields(a_value, b_value)
            status = "changed" if changed_fields else "unchanged"
        output.append(
            {
                "key": key,
                "status": status,
                "changed_fields": changed_fields,
                "a": a_value,
                "b": b_value,
            }
        )
    return output


def _apply_one(document: Any, op: str, pointer: str, value: Any) -> None:
    if pointer == "":
        raise JsonPatchError("Root document replacement is not supported for case graph patches")
    parent, token = _resolve_parent(document, pointer)
    if isinstance(parent, list):
        if token == "-":
            index = len(parent)
        else:
            try:
                index = int(token)
            except ValueError as exc:
                raise JsonPatchError(f"Invalid list index in patch path: {pointer}") from exc
        if op == "add":
            if index < 0 or index > len(parent):
                raise JsonPatchError(f"Patch path index out of range: {pointer}")
            parent.insert(index, value)
        elif op == "replace":
            if index < 0 or index >= len(parent):
                raise JsonPatchError(f"Patch path index out of range: {pointer}")
            parent[index] = value
        elif op == "remove":
            if index < 0 or index >= len(parent):
                raise JsonPatchError(f"Patch path index out of range: {pointer}")
            parent.pop(index)
        return

    if not isinstance(parent, dict):
        raise JsonPatchError(f"Patch parent is not an object or array: {pointer}")
    if op == "add":
        parent[token] = value
    elif op == "replace":
        if token not in parent:
            raise JsonPatchError(f"Patch path does not exist: {pointer}")
        parent[token] = value
    elif op == "remove":
        if token not in parent:
            raise JsonPatchError(f"Patch path does not exist: {pointer}")
        del parent[token]


def _resolve_parent(document: Any, pointer: str) -> tuple[Any, str]:
    if not pointer.startswith("/"):
        raise JsonPatchError(f"Patch path must be a JSON pointer: {pointer}")
    tokens = [_unescape_pointer(item) for item in pointer.split("/")[1:]]
    if not tokens:
        raise JsonPatchError("Patch path is empty")
    current = document
    for token in tokens[:-1]:
        if isinstance(current, list):
            try:
                current = current[int(token)]
            except (ValueError, IndexError) as exc:
                raise JsonPatchError(f"Patch path does not exist: {pointer}") from exc
        elif isinstance(current, dict) and token in current:
            current = current[token]
        else:
            raise JsonPatchError(f"Patch path does not exist: {pointer}")
    return current, tokens[-1]


def _unescape_pointer(value: str) -> str:
    return value.replace("~1", "/").replace("~0", "~")


def _record_key(item: dict[str, Any], key_fields: tuple[str, ...], index: int) -> str:
    for field in key_fields:
        value = item.get(field)
        if value not in {None, ""}:
            return str(value)
    return f"index:{index}"


def _records(items: list[Any]) -> list[dict[str, Any]]:
    return [item for item in items if isinstance(item, dict)]


def _changed_fields(a_value: dict[str, Any], b_value: dict[str, Any]) -> list[str]:
    return [
        key
        for key in sorted(set(a_value) | set(b_value))
        if a_value.get(key) != b_value.get(key)
    ]


def _parent_head(audit_manifest: dict[str, Any] | None, fallback: Any) -> str:
    if audit_manifest:
        head_hash = audit_manifest.get("head_hash")
        if isinstance(head_hash, str) and head_hash:
            return head_hash
        return canonical_sha256(audit_manifest)
    return canonical_sha256(fallback)


def _entry_for_stage(audit_manifest: dict[str, Any], stage: str) -> dict[str, Any]:
    for entry in audit_manifest.get("entries", []):
        if entry.get("stage") == stage:
            return entry
    raise ParentRunNotReviewed(f"parent audit manifest has no {stage} entry")


def _resolve_artifact_path(parent_dir: Path, artifact_uri: str) -> Path:
    path = Path(artifact_uri)
    if path.is_absolute() or path.exists():
        return path
    candidate = parent_dir / path.name
    if candidate.exists():
        return candidate
    return path


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _maybe_read_json(path: Path) -> Any | None:
    if not path.exists():
        return None
    return _read_json(path)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
