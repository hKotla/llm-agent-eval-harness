import pytest

from support_agent.agent import SupportAgent
from support_agent.llm import FakeLLM


@pytest.fixture
def agent() -> SupportAgent:
    """The Week 1 agent, wired to the offline fake. No API key involved."""
    return SupportAgent(llm=FakeLLM())
