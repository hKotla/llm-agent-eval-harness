"""The loop itself, driven by a scripted model rather than the keyword fake."""

from support_agent.agent import SupportAgent
from support_agent.llm import LLMResponse, ScriptedLLM, ToolCall


def test_tool_output_is_handed_back_to_the_model() -> None:
    llm = ScriptedLLM(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall("1", "lookup_booking", {"reference": "BK-1001"}),
                ]
            ),
            LLMResponse(content="Your booking is confirmed."),
        ]
    )
    result = SupportAgent(llm=llm).run("Status of BK-1001 please")

    assert result.answer == "Your booking is confirmed."
    assert result.tool_names == ["lookup_booking"]
    second_call = llm.calls[1]
    tool_message = next(message for message in second_call if message.role == "tool")
    assert "Priya Shah" in tool_message.content
    assert tool_message.tool_call_id == "1"


def test_unknown_tool_is_reported_and_the_loop_continues() -> None:
    llm = ScriptedLLM(
        [
            LLMResponse(tool_calls=[ToolCall("1", "delete_booking", {})]),
            LLMResponse(content="I can't delete a booking."),
        ]
    )
    result = SupportAgent(llm=llm).run("Please delete booking BK-1001.")

    assert result.tool_names == ["delete_booking"]
    assert "unknown_tool" in result.tool_trace[0].output
    assert result.answer == "I can't delete a booking."


def test_step_limit_stops_a_model_that_keeps_calling_tools() -> None:
    llm = ScriptedLLM(
        [
            LLMResponse(
                tool_calls=[
                    ToolCall(str(n), "lookup_booking", {"reference": "BK-1001"}),
                ]
            )
            for n in range(5)
        ]
    )
    result = SupportAgent(llm=llm, max_steps=2).run("status")

    assert len(result.tool_trace) == 2
    assert result.answer == "I couldn't finish that request within the step limit."
