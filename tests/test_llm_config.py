from policy_impact_sandbox.llm.config import LLMConfig


def test_deepseek_is_default_openai_compatible_provider(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_BASE_URL", raising=False)
    monkeypatch.delenv("DEEPSEEK_MODEL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    config = LLMConfig.from_env()

    assert config.provider == "deepseek"
    assert config.base_url == "https://api.deepseek.com"
    assert config.model == "deepseek-chat"
    assert config.api_key is None


def test_deepseek_config_reads_key_and_overrides_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://example.test")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-test-model")

    config = LLMConfig.from_env()

    assert config.api_key == "test-key"
    assert config.base_url == "https://example.test"
    assert config.model == "deepseek-test-model"


def test_generic_llm_environment_overrides_deepseek_defaults(monkeypatch) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-key")
    monkeypatch.setenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-chat")
    monkeypatch.setenv("LLM_API_KEY", "generic-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://generic.test")
    monkeypatch.setenv("LLM_MODEL", "generic-model")

    config = LLMConfig.from_env()

    assert config.api_key == "generic-key"
    assert config.base_url == "https://generic.test"
    assert config.model == "generic-model"
