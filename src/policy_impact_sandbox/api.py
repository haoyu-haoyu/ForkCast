from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from policy_impact_sandbox.live_policy.runs import LivePolicyRunManager, PolicyRunConflict, PolicyRunNotFound
from policy_impact_sandbox.llm import LLMConfig, MissingLLMConfig, OpenAICompatibleLLMClient


class JSONLLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


class PolicyRunRequest(BaseModel):
    policy_text: str = Field(default="")
    agent_count: int = Field(default=12, ge=1, le=200)
    rounds: int = Field(default=2, ge=1, le=6)


class CaseGraphPatchRequest(BaseModel):
    case_graph: dict


def create_app(
    llm_client_factory: Callable[[], JSONLLMClient] | None = None,
    run_root: str | Path = "runs",
    run_background: bool = True,
) -> FastAPI:
    load_dotenv()
    app = FastAPI(title="Policy Impact Sandbox API")
    client_factory = llm_client_factory or _default_llm_client
    run_manager = LivePolicyRunManager(client_factory, run_root=run_root)

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

    return app


def _default_llm_client() -> JSONLLMClient:
    return OpenAICompatibleLLMClient(LLMConfig.from_env())


app = create_app()
