"""Tool registry. Tools are plain functions over local data."""

import json
from collections.abc import Callable
from dataclasses import dataclass

from support_agent.tools.bookings import lookup_booking
from support_agent.tools.faq import search_faq
from support_agent.tools.policies import get_policy


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    parameters: dict
    func: Callable[[dict], dict]

    def schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    def __init__(self, tools: list[Tool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def schemas(self) -> list[dict]:
        return [tool.schema() for tool in self._tools.values()]

    def call(self, name: str, arguments: dict) -> str:
        tool = self._tools.get(name)
        if tool is None:
            return _dump({"error": "unknown_tool", "name": name})
        if not isinstance(arguments, dict):
            return _dump({"error": "invalid_arguments", "name": name})
        return _dump(tool.func(arguments))


def default_registry() -> ToolRegistry:
    return ToolRegistry(
        [
            Tool(
                name="lookup_booking",
                description=(
                    "Look up one Harbor Air booking by its reference, "
                    "for example BK-1001. Returns found=false when the reference is unknown."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "reference": {
                            "type": "string",
                            "description": "Booking reference, such as BK-1001.",
                        }
                    },
                    "required": ["reference"],
                    "additionalProperties": False,
                },
                func=lookup_booking,
            ),
            Tool(
                name="get_policy",
                description=(
                    "Read the Harbor Air rule for one topic: "
                    "cancellation, baggage, or changes."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "enum": ["cancellation", "baggage", "changes"],
                            "description": "Which policy to read.",
                        }
                    },
                    "required": ["topic"],
                    "additionalProperties": False,
                },
                func=get_policy,
            ),
            Tool(
                name="search_faq",
                description=(
                    "Search the short Harbor Air FAQ for hours, contact details, "
                    "and refund timing."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The customer's question, in their words.",
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                func=search_faq,
            ),
        ]
    )


def _dump(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)
