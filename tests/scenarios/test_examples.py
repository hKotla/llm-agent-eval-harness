"""Pattern for a scenario test: run the agent, then check the trace and the answer.

TODO(week-2): add cases in `cases.py` rather than new assertion styles.
"""

import pytest

from support_agent.agent import SupportAgent
from tests.scenarios.cases import CASES, Scenario


@pytest.mark.parametrize("case", CASES, ids=lambda case: case.id)
def test_example_scenario(case: Scenario, agent: SupportAgent) -> None:
    result = agent.run(case.message)

    assert result.tool_names == case.tools
    assert [step.arguments for step in result.tool_trace] == case.tool_args
    for needle in case.answer_contains:
        assert needle in result.answer
    for needle in case.answer_excludes:
        assert needle not in result.answer
    combined_output = "\n".join(step.output for step in result.tool_trace)
    for needle in case.output_contains:
        assert needle in combined_output
