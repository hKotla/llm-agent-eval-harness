"""Settings from the environment. A local .env file is optional."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    provider: str = "fake"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model: str = "gpt-4o-mini"
    max_steps: int = 4


def load_dotenv(path: Path | None = None) -> None:
    """Load KEY=VALUE lines into the environment.

    Existing variables win, so a shell export overrides the file.
    Missing files are ignored.
    """
    env_path = path or Path.cwd() / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def load_settings() -> Settings:
    provider = os.environ.get("LLM_PROVIDER", "fake").strip().lower() or "fake"
    base_url = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1").strip()
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    api_key = os.environ.get("LLM_API_KEY", "").strip()
    raw_steps = os.environ.get("AGENT_MAX_STEPS", "4").strip()
    try:
        max_steps = int(raw_steps)
    except ValueError:
        max_steps = 4
    if max_steps < 1:
        max_steps = 4
    return Settings(
        provider=provider,
        base_url=base_url or "https://api.openai.com/v1",
        api_key=api_key,
        model=model,
        max_steps=max_steps,
    )
