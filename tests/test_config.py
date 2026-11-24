from pathlib import Path

from support_agent.config import load_dotenv, load_settings
from support_agent.llm import FakeLLM, build_llm


def _clear(monkeypatch) -> None:
    for name in ("LLM_PROVIDER", "LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL", "AGENT_MAX_STEPS"):
        monkeypatch.delenv(name, raising=False)


def test_defaults_are_offline(monkeypatch) -> None:
    _clear(monkeypatch)
    settings = load_settings()
    assert settings.provider == "fake"
    assert settings.model == "gpt-4o-mini"
    assert settings.max_steps == 4
    assert isinstance(build_llm(settings), FakeLLM)


def test_provider_and_steps_are_normalised(monkeypatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "OpenAI")
    monkeypatch.setenv("AGENT_MAX_STEPS", "many")
    settings = load_settings()
    assert settings.provider == "openai"
    assert settings.max_steps == 4


def test_dotenv_does_not_override_the_environment(monkeypatch, tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# comment",
                "LLM_PROVIDER=openai",
                "LLM_MODEL=from-file",
                "LLM_API_KEY='secret'",
                "",
            ]
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    load_dotenv(env_file)

    assert load_settings().provider == "fake"
    assert load_settings().model == "from-file"
    assert load_settings().api_key == "secret"
