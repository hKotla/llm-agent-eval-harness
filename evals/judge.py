"""LLM-as-judge scoring.

TODO(week-3): implement `Judge.score`. Planned metrics, each from 0 to 1:

- accuracy: the answer states the facts the scenario expects
- helpfulness: the answer addresses what the customer asked
- groundedness: claims are supported by the tool trace, not invented

Keep the default test run offline. Score with a fake judge or a recorded
fixture first, the same way `FakeLLM` keeps the agent tests off the network.
A live judge call can be a separate, optional command.
"""

from dataclasses import dataclass


@dataclass
class Score:
    accuracy: float | None = None
    helpfulness: float | None = None
    groundedness: float | None = None


class Judge:
    def score(self, transcript: list, expected: dict) -> Score:
        del transcript, expected
        raise NotImplementedError(
            "TODO(week-3): score accuracy, helpfulness, and groundedness."
        )
