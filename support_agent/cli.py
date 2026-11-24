"""Command line entry point. Uses the fake LLM unless .env says otherwise."""

import argparse
import sys

from support_agent.agent import SupportAgent
from support_agent.config import load_dotenv, load_settings
from support_agent.llm import LLMError, build_llm


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m support_agent",
        description="Ask the Harbor Air support agent.",
    )
    parser.add_argument("message", help="Customer message, in quotes.")
    args = parser.parse_args(argv)

    load_dotenv()
    settings = load_settings()
    try:
        agent = SupportAgent(llm=build_llm(settings), max_steps=settings.max_steps)
        result = agent.run(args.message)
    except LLMError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(result.answer)
    if result.tool_trace:
        print("\nTools:")
        for step in result.tool_trace:
            rendered = ", ".join(
                f"{key}={value!r}" for key, value in step.arguments.items()
            )
            print(f"- {step.name}({rendered})")
    return 0
