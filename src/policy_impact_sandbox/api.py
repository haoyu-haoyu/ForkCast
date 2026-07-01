from __future__ import annotations

from typing import Callable, Protocol

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from policy_impact_sandbox.live_policy.pipeline import run_policy_analysis
from policy_impact_sandbox.llm import LLMConfig, MissingLLMConfig, OpenAICompatibleLLMClient


class JSONLLMClient(Protocol):
    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        ...


class PolicyRunRequest(BaseModel):
    policy_text: str = Field(default="")
    agent_count: int = Field(default=12, ge=1, le=200)
    rounds: int = Field(default=2, ge=1, le=6)


def create_app(llm_client_factory: Callable[[], JSONLLMClient] | None = None) -> FastAPI:
    load_dotenv()
    app = FastAPI(title="Policy Impact Sandbox API")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/policy-runs")
    def create_policy_run(request: PolicyRunRequest) -> dict:
        if not request.policy_text.strip():
            raise HTTPException(status_code=400, detail="policy_text is required")
        try:
            llm_client = llm_client_factory() if llm_client_factory else _default_llm_client()
            return run_policy_analysis(
                policy_text=request.policy_text,
                llm_client=llm_client,
                agent_count=request.agent_count,
                rounds=request.rounds,
            )
        except MissingLLMConfig as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


def _default_llm_client() -> JSONLLMClient:
    return OpenAICompatibleLLMClient(LLMConfig.from_env())


app = create_app()
