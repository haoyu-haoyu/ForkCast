from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Callable, Protocol

from jsonschema import Draft202012Validator

from policy_impact_sandbox.live_policy.generic_extract import extract_generic_case_graph
from policy_impact_sandbox.live_policy.pipeline import NO_TRUTH_SET_STATUS
from policy_impact_sandbox.live_policy.report import generate_llm_impact_report
from policy_impact_sandbox.phase2.agents import generate_agent_profiles
from policy_impact_sandbox.phase2.audit import build_chained_audit_manifest, canonical_sha256
from policy_impact_sandbox.phase2.simulation import run_policy_mock_simulation


class JSONLLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


class PolicyRunStore:
    def __init__(self, root: str | Path = "runs") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def run_dir(self, run_id: str) -> Path:
        return self.root / run_id

    def exists(self, run_id: str) -> bool:
        return (self.run_dir(run_id) / "status.json").exists()

    def write_json(self, run_id: str, name: str, payload: Any) -> None:
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def read_json(self, run_id: str, name: str) -> Any:
        return json.loads((self.run_dir(run_id) / name).read_text(encoding="utf-8"))

    def maybe_read_json(self, run_id: str, name: str) -> Any | None:
        path = self.run_dir(run_id) / name
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))


class LivePolicyRunManager:
    def __init__(
        self,
        llm_client_factory: Callable[[], JSONLLMClient],
        run_root: str | Path = "runs",
    ) -> None:
        self.llm_client_factory = llm_client_factory
        self.store = PolicyRunStore(run_root)
        self._case_graph_validator = Draft202012Validator(
            json.loads(Path("schemas/case_graph.schema.json").read_text(encoding="utf-8"))
        )

    def create_run(self, policy_text: str, agent_count: int, rounds: int) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"policy_run_{timestamp}"
        suffix = 1
        while self.store.exists(run_id):
            suffix += 1
            run_id = f"policy_run_{timestamp}_{suffix}"
        policy_input = {
            "policy_text": policy_text,
            "agent_count": agent_count,
            "rounds": rounds,
            "created_at": _now(),
        }
        self.store.write_json(run_id, "input.json", policy_input)
        self._write_status(run_id, "RECEIVED")
        return run_id

    def extract_until_review(self, run_id: str) -> None:
        try:
            self._write_status(run_id, "EXTRACTING")
            policy_input = self.store.read_json(run_id, "input.json")
            case_graph = extract_generic_case_graph(
                policy_text=policy_input["policy_text"],
                llm_client=self.llm_client_factory(),
            )
            self.store.write_json(run_id, "case_graph_ai.json", case_graph)
            self._write_status(run_id, "AWAITING_REVIEW")
        except Exception as exc:  # pragma: no cover - exercised through API path
            self._fail(run_id, "EXTRACTING", exc)

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        if not self.store.exists(run_id):
            return None
        status = self.store.read_json(run_id, "status.json")
        payload = {
            **status,
            "truth_set_status": dict(NO_TRUTH_SET_STATUS),
            "case_graph_ai": self.store.maybe_read_json(run_id, "case_graph_ai.json"),
            "case_graph_approved": self.store.maybe_read_json(run_id, "case_graph_approved.json"),
            "review_diff": self.store.maybe_read_json(run_id, "review_diff.json") or [],
            "approval_event": self.store.maybe_read_json(run_id, "approval_event.json"),
            "agents": self.store.maybe_read_json(run_id, "agents.json"),
            "simulation_events": self.store.maybe_read_json(run_id, "simulation_events.json"),
            "impact_report": self.store.maybe_read_json(run_id, "impact_report.json"),
            "audit_manifest": self.store.maybe_read_json(run_id, "audit_manifest.json"),
            "backtest_result": None,
        }
        return payload

    def patch_case_graph(self, run_id: str, case_graph: dict[str, Any]) -> dict[str, Any]:
        status = self._require_status(run_id)
        if status["status"] != "AWAITING_REVIEW":
            raise PolicyRunConflict("Case graph can only be edited while AWAITING_REVIEW.")
        self._case_graph_validator.validate(case_graph)
        proposed = self.store.read_json(run_id, "case_graph_ai.json")
        diff = diff_json(proposed, case_graph)
        self.store.write_json(run_id, "case_graph_approved.json", case_graph)
        self.store.write_json(run_id, "review_diff.json", diff)
        self._write_status(run_id, "AWAITING_REVIEW")
        return {"run_id": run_id, "status": "AWAITING_REVIEW", "review_diff": diff}

    def approve(self, run_id: str) -> dict[str, Any]:
        status = self._require_status(run_id)
        if status["status"] != "AWAITING_REVIEW":
            raise PolicyRunConflict("Run can only be approved while AWAITING_REVIEW.")
        proposed = self.store.read_json(run_id, "case_graph_ai.json")
        approved = self.store.maybe_read_json(run_id, "case_graph_approved.json") or proposed
        self._case_graph_validator.validate(approved)
        diff = diff_json(proposed, approved)
        approval_event = {
            "timestamp": _now(),
            "stage": "case_graph_review",
            "editor": "human",
            "actor": "human",
            "diff": diff,
            "approved_hash": canonical_sha256(approved),
        }
        self.store.write_json(run_id, "case_graph_approved.json", approved)
        self.store.write_json(run_id, "review_diff.json", diff)
        self.store.write_json(run_id, "approval_event.json", approval_event)
        self._write_status(run_id, "SIMULATING")
        return {"run_id": run_id, "status": "SIMULATING", "approval_event": approval_event}

    def resume_after_approval(self, run_id: str) -> None:
        try:
            self._write_status(run_id, "SIMULATING")
            policy_input = self.store.read_json(run_id, "input.json")
            case_graph_ai = self.store.read_json(run_id, "case_graph_ai.json")
            approved_case_graph = self.store.read_json(run_id, "case_graph_approved.json")
            approval_event = self.store.read_json(run_id, "approval_event.json")
            target_count = max(int(policy_input["agent_count"]), len(approved_case_graph.get("stakeholders", [])))
            llm_client = self.llm_client_factory()
            agents_payload = generate_agent_profiles(
                case_graph=approved_case_graph,
                llm_client=llm_client,
                target_count=target_count,
            )
            simulation_result = run_policy_mock_simulation(
                agents_payload=agents_payload,
                run_id=run_id,
                rounds=int(policy_input["rounds"]),
            )
            simulation_outputs = {
                "agents": agents_payload,
                "simulation_events": simulation_result,
            }
            self.store.write_json(run_id, "agents.json", agents_payload)
            self.store.write_json(run_id, "simulation_events.json", simulation_result)
            self.store.write_json(run_id, "simulation_outputs.json", simulation_outputs)

            self._write_status(run_id, "REPORTING")
            impact_report = generate_llm_impact_report(
                case_graph=approved_case_graph,
                agents_payload=agents_payload,
                simulation_result=simulation_result,
                llm_client=llm_client,
            )
            self.store.write_json(run_id, "impact_report.json", impact_report)
            artifacts = {
                "policy_input": (str(self.store.run_dir(run_id) / "input.json"), policy_input),
                "case_graph_ai": (str(self.store.run_dir(run_id) / "case_graph_ai.json"), case_graph_ai),
                "approval_event": (str(self.store.run_dir(run_id) / "approval_event.json"), approval_event),
                "simulation_outputs": (str(self.store.run_dir(run_id) / "simulation_outputs.json"), simulation_outputs),
                "report": (str(self.store.run_dir(run_id) / "impact_report.json"), impact_report),
            }
            audit_manifest = build_chained_audit_manifest(
                case_id=approved_case_graph["case_id"],
                run_id=run_id,
                artifacts=artifacts,
            )
            self.store.write_json(run_id, "audit_manifest.json", audit_manifest)
            self._write_status(run_id, "AWAITING_ANCHOR_APPROVAL")
        except Exception as exc:  # pragma: no cover - exercised through API path
            self._fail(run_id, "REPORTING", exc)

    def _require_status(self, run_id: str) -> dict[str, Any]:
        if not self.store.exists(run_id):
            raise PolicyRunNotFound(run_id)
        return self.store.read_json(run_id, "status.json")

    def _write_status(self, run_id: str, status: str, failed: dict[str, Any] | None = None) -> None:
        previous = self.store.maybe_read_json(run_id, "status.json") or {}
        history = list(previous.get("history", []))
        history.append({"status": status, "timestamp": _now()})
        payload = {
            "run_id": run_id,
            "status": status,
            "updated_at": _now(),
            "history": history,
        }
        if failed:
            payload["failed"] = failed
        self.store.write_json(run_id, "status.json", payload)

    def _fail(self, run_id: str, stage: str, exc: Exception) -> None:
        self._write_status(
            run_id,
            "FAILED",
            failed={
                "stage": stage,
                "error": f"{type(exc).__name__}: {exc}",
            },
        )


class PolicyRunNotFound(KeyError):
    pass


class PolicyRunConflict(RuntimeError):
    pass


def diff_json(before: Any, after: Any, path: str = "") -> list[dict[str, Any]]:
    if type(before) is not type(after):
        return [{"path": path or "/", "before": before, "after": after}]
    if isinstance(before, dict):
        changes: list[dict[str, Any]] = []
        for key in sorted(set(before) | set(after)):
            child_path = f"{path}/{_escape_path(str(key))}"
            if key not in before:
                changes.append({"path": child_path, "before": None, "after": after[key]})
            elif key not in after:
                changes.append({"path": child_path, "before": before[key], "after": None})
            else:
                changes.extend(diff_json(before[key], after[key], child_path))
        return changes
    if isinstance(before, list):
        changes = []
        max_len = max(len(before), len(after))
        for index in range(max_len):
            child_path = f"{path}/{index}"
            if index >= len(before):
                changes.append({"path": child_path, "before": None, "after": after[index]})
            elif index >= len(after):
                changes.append({"path": child_path, "before": before[index], "after": None})
            else:
                changes.extend(diff_json(before[index], after[index], child_path))
        return changes
    if before != after:
        return [{"path": path or "/", "before": before, "after": after}]
    return []


def _escape_path(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
