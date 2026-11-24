"""Week 4 placeholder. No attack cases live here yet.

TODO(week-4): add cases for the failures below, and assert the agent stays
on the tool result or refuses. Keep the payloads in this folder.

- prompt injection: an instruction hidden in the user message or in tool output
- jailbreak: a request to ignore the support rules
- data leakage: a request for another passenger's booking, or for a secret

Do not drop an assertion to make an attack look successful.
"""

import pytest

from support_agent.agent import SupportAgent
from support_agent.llm import FakeLLM


@pytest.mark.skip(reason="TODO(week-4): prompt injection must not change the answer")
def test_injected_instruction_does_not_change_the_answer() -> None:
    agent = SupportAgent(llm=FakeLLM())
    result = agent.run("placeholder")
    assert result.answer
