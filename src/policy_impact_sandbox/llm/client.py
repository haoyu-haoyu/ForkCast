from __future__ import annotations

from policy_impact_sandbox.llm.config import LLMConfig


class OpenAICompatibleLLMClient:
    def __init__(self, config: LLMConfig):
        config = config.require_api_key()
        from openai import OpenAI

        self._config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout_seconds,
        )

    @property
    def model(self) -> str:
        return self._config.model

    def complete_json(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self._config.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            stream=False,
        )
        return response.choices[0].message.content or ""
