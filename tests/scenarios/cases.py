"""Example scenarios. Copy one of these when you add a case.

TODO(week-2): grow this list to 20–30 cases. Cover happy paths, edge cases
(unknown reference, unknown policy topic, blank message), and wrong tool use.
Keep every case on FakeLLM or ScriptedLLM so `pytest` stays offline.

These assertions pin the offline fake's wording and routing. They will be
too brittle for a real model; that is what the Week 3 judge is for. Until
then, if you change FakeLLM's sentences, update the matching case.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Scenario:
    id: str
    message: str
    tools: list[str]
    tool_args: list[dict]
    answer_contains: list[str]
    answer_excludes: list[str] = field(default_factory=list)
    output_contains: list[str] = field(default_factory=list)


CASES: list[Scenario] = [
    Scenario(
        id="booking-confirmed",
        message="What is the status of booking BK-1001?",
        tools=["lookup_booking"],
        tool_args=[{"reference": "BK-1001"}],
        answer_contains=["BK-1001", "confirmed", "Lisbon"],
        answer_excludes=["couldn't find"],
        output_contains=["Priya Shah"],
    ),
    Scenario(
        id="booking-missing",
        message="Where is booking BK-9999?",
        tools=["lookup_booking"],
        tool_args=[{"reference": "BK-9999"}],
        answer_contains=["BK-9999", "couldn't find"],
        answer_excludes=["Priya", "Lisbon", "confirmed"],
        output_contains=['"found": false'],
    ),
    Scenario(
        id="baggage-not-a-booking-lookup",
        message="What is the baggage allowance?",
        tools=["get_policy"],
        tool_args=[{"topic": "baggage"}],
        answer_contains=["8kg", "£25"],
        answer_excludes=["BK-"],
    ),
    Scenario(
        id="opening-hours",
        message="What are your opening hours?",
        tools=["search_faq"],
        tool_args=[{"query": "What are your opening hours?"}],
        answer_contains=["Monday", "08:00"],
    ),
    Scenario(
        id="out-of-scope",
        message="What is the capital of France?",
        tools=[],
        tool_args=[],
        answer_contains=["booking status"],
        answer_excludes=["Paris", "BK-"],
    ),
    Scenario(
        id="blank-message",
        message="   ",
        tools=[],
        tool_args=[],
        answer_contains=["booking status"],
    ),
]
