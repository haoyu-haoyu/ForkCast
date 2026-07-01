from __future__ import annotations

from dataclasses import dataclass
import os


class MissingLLMConfig(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str | None
    base_url: str
    model: str
    timeout_seconds: float

    @classmethod
    def from_env(cls) -> "LLMConfig":
        provider = os.getenv("LLM_PROVIDER", "deepseek")
        api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY") or None
        base_url = os.getenv("LLM_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL") or "https://api.deepseek.com"
        model = os.getenv("LLM_MODEL") or os.getenv("DEEPSEEK_MODEL") or "deepseek-chat"
        timeout_seconds = float(os.getenv("LLM_TIMEOUT_SECONDS", "60"))
        return cls(
            provider=provider,
            api_key=api_key,
            base_url=base_url.rstrip("/"),
            model=model,
            timeout_seconds=timeout_seconds,
        )

    def require_api_key(self) -> "LLMConfig":
        if not self.api_key:
            raise MissingLLMConfig("Set DEEPSEEK_API_KEY or LLM_API_KEY before running real LLM extraction.")
        return self
