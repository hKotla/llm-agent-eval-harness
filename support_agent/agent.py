"""The tool loop under test.

One customer message goes to the LLM with the tool schemas. Tool calls are
executed locally and appended to the transcript. The loop stops on a normal
answer, or when `max_steps` is used up.
"""

from dataclasses import dataclass, field

from support_agent.llm import LLM, Message
from support_agent.tools import ToolRegistry, default_registry

SYSTEM_PROMPT = (
    "You are the Harbor Air support assistant. "
    "Help with booking status, baggage, changes, cancellations, and short FAQ answers. "
    "Use a tool for any fact about a booking, a policy, or the FAQ. "
    "Do not invent booking records, fees, or dates. "
    "If a tool says a record is missing, say so and stop. "
    "Keep the answer to a few sentences."
)

_STEP_LIMIT = "I couldn't finish that request within the step limit."


@dataclass
class ToolTrace:
    name: str
    arguments: dict
    output: str


@dataclass
class AgentResult:
    answer: str
    tool_trace: list[ToolTrace] = field(default_factory=list)
    messages: list[Message] = field(default_factory=list)

    @property
    def tool_names(self) -> list[str]:
        return [step.name for step in self.tool_trace]


class SupportAgent:
    def __init__(
        self,
        llm: LLM,
        tools: ToolRegistry | None = None,
        max_steps: int = 4,
    ) -> None:
        self.llm = llm
        self.tools = tools or default_registry()
        self.max_steps = max_steps

    def run(self, user_message: str) -> AgentResult:
        messages = [
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=user_message),
        ]
        trace: list[ToolTrace] = []
        schemas = self.tools.schemas()
        for _step in range(self.max_steps):
            response = self.llm.complete(messages, schemas)
            if not response.tool_calls:
                return AgentResult(
                    answer=response.content.strip(),
                    tool_trace=trace,
                    messages=messages,
                )
            messages.append(
                Message(
                    role="assistant",
                    content=response.content,
                    tool_calls=list(response.tool_calls),
                )
            )
            for call in response.tool_calls:
                output = self.tools.call(call.name, call.arguments)
                trace.append(
                    ToolTrace(
                        name=call.name,
                        arguments=dict(call.arguments),
                        output=output,
                    )
                )
                messages.append(
                    Message(
                        role="tool",
                        name=call.name,
                        tool_call_id=call.id,
                        content=output,
                    )
                )
        return AgentResult(answer=_STEP_LIMIT, tool_trace=trace, messages=messages)
