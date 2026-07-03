from __future__ import annotations

from pathlib import Path
import time
from typing import Callable, Protocol

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from policy_impact_sandbox.live_policy.forks import (
    ForkNotFound,
    JsonPatchError,
    ParentRunNotReviewed,
    PolicyForkManager,
)
from policy_impact_sandbox.live_policy.runs import LivePolicyRunManager, PolicyRunConflict, PolicyRunNotFound
from policy_impact_sandbox.llm import LLMConfig, MissingLLMConfig, OpenAICompatibleLLMClient
from policy_impact_sandbox.verify_run import FetchPayloadHex, verify_run


class JSONLLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


class PolicyRunRequest(BaseModel):
    policy_text: str = Field(default="")
    agent_count: int = Field(default=12, ge=1, le=200)
    rounds: int = Field(default=2, ge=1, le=6)


class CaseGraphPatchRequest(BaseModel):
    case_graph: dict


class ForkRequest(BaseModel):
    name: str = Field(default="")
    case_graph_patches: list[dict] = Field(default_factory=list)


def create_app(
    llm_client_factory: Callable[[], JSONLLMClient] | None = None,
    run_root: str | Path = "runs",
    run_background: bool = True,
    verify_payload_fetcher: FetchPayloadHex | None = None,
    verify_cache_ttl_seconds: int = 60,
) -> FastAPI:
    load_dotenv()
    app = FastAPI(title="Policy Impact Sandbox API")
    client_factory = llm_client_factory or _default_llm_client
    run_manager = LivePolicyRunManager(client_factory, run_root=run_root)
    fork_manager = PolicyForkManager(run_root=run_root, llm_client_factory=client_factory)
    verify_cache: dict[tuple[str, str, str], tuple[float, dict]] = {}

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/policy-runs", status_code=202)
    def create_policy_run(request: PolicyRunRequest, background_tasks: BackgroundTasks) -> dict:
        if not request.policy_text.strip():
            raise HTTPException(status_code=400, detail="policy_text is required")
        try:
            run_id = run_manager.create_run(
                policy_text=request.policy_text,
                agent_count=request.agent_count,
                rounds=request.rounds,
            )
            if run_background:
                background_tasks.add_task(run_manager.extract_until_review, run_id)
            else:
                run_manager.extract_until_review(run_id)
            status_payload = run_manager.get_run(run_id) or {"status": "RECEIVED"}
            return {"run_id": run_id, "status": status_payload["status"]}
        except MissingLLMConfig as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/policy-runs/{run_id}")
    def get_policy_run(run_id: str) -> dict:
        payload = run_manager.get_run(run_id)
        if payload is None:
            raise HTTPException(status_code=404, detail="policy run not found")
        return payload

    @app.patch("/api/policy-runs/{run_id}")
    def patch_policy_run(run_id: str, request: CaseGraphPatchRequest) -> dict:
        try:
            return run_manager.patch_case_graph(run_id, request.case_graph)
        except PolicyRunNotFound as exc:
            raise HTTPException(status_code=404, detail="policy run not found") from exc
        except PolicyRunConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/policy-runs/{run_id}/approve", status_code=202)
    def approve_policy_run(run_id: str, background_tasks: BackgroundTasks) -> dict:
        try:
            approval = run_manager.approve(run_id)
            if run_background:
                background_tasks.add_task(run_manager.resume_after_approval, run_id)
            else:
                run_manager.resume_after_approval(run_id)
            payload = run_manager.get_run(run_id) or approval
            return {"run_id": run_id, "status": payload["status"]}
        except PolicyRunNotFound as exc:
            raise HTTPException(status_code=404, detail="policy run not found") from exc
        except PolicyRunConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/policy-runs/{run_id}/forks", status_code=202)
    def create_policy_run_fork(run_id: str, request: ForkRequest) -> dict:
        try:
            result = fork_manager.create_fork(
                parent_run_id=run_id,
                name=request.name,
                case_graph_patches=request.case_graph_patches,
            )
            return {
                "parent_run_id": result["parent_run_id"],
                "fork_id": result["fork_id"],
                "name": result["name"],
                "status": result["status"],
                "approval_event": result["approval_event"],
                "audit_manifest": result["audit_manifest"],
            }
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ParentRunNotReviewed as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except (JsonPatchError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/policy-runs/{run_id}/forks/compare")
    def compare_policy_run_forks(run_id: str, a: str, b: str) -> dict:
        try:
            return fork_manager.compare_forks(run_id, a, b)
        except ForkNotFound as exc:
            raise HTTPException(status_code=404, detail=f"fork not found: {exc}") from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/anchors/{run_id}/verify")
    def verify_anchor(run_id: str) -> dict:
        run_dir = Path(run_root) / run_id
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="run not found")
        anchor_path = run_dir / "kaspa_anchor.json"
        if not anchor_path.exists():
            raise HTTPException(status_code=404, detail="kaspa_anchor.json not found")
        try:
            import json

            anchor = json.loads(anchor_path.read_text(encoding="utf-8"))
            txid = anchor.get("tx_id")
            if not isinstance(txid, str) or not txid:
                raise HTTPException(status_code=409, detail="kaspa_anchor.json does not record a tx_id")
            network = str(anchor.get("network") or "testnet-10")
            cache_key = (run_id, txid, network)
            now = time.monotonic()
            cached = verify_cache.get(cache_key)
            if cached and now - cached[0] <= verify_cache_ttl_seconds:
                return {**cached[1], "cache": {"hit": True, "ttl_seconds": verify_cache_ttl_seconds}}
            result = verify_run(
                run_dir=run_dir,
                txid=txid,
                network=network,
                fetch_payload_hex=verify_payload_fetcher,
            )
            verify_cache[cache_key] = (now, result)
            return {**result, "cache": {"hit": False, "ttl_seconds": verify_cache_ttl_seconds}}
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return app


def _default_llm_client() -> JSONLLMClient:
    return OpenAICompatibleLLMClient(LLMConfig.from_env())


app = create_app()
