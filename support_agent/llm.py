"""LLM access: a tiny protocol, an offline fake, and an OpenAI-compatible client.

The agent talks to `LLM.complete`. Tests and the default CLI use `FakeLLM`,
so nothing here needs an API key. `OpenAICompatibleLLM` posts to
`/chat/completions` on whatever base URL you configure (OpenAI, OpenRouter,
Groq, Ollama, ...). There is no provider SDK.
"""

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Protocol

from support_agent.config import Settings, load_settings


class LLMError(RuntimeError):
    """A model call failed, or the provider settings are unusable."""


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class Message:
    role: str
    content: str = ""
    name: str = ""
    tool_call_id: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLM(Protocol):
    def complete(self, messages: list[Message], tools: list[dict]) -> LLMResponse:
        """Return either a final answer or one or more tool calls."""


class FakeLLM:
    """Deterministic stand-in for a chat model.

    Routing order, first match wins:

    1. The latest message is a tool result → answer from that result.
    2. The user text contains a booking reference (`BK-####`) → `lookup_booking`.
    3. It mentions baggage, cancellation, or changes → `get_policy`.
    4. It looks like an FAQ question → `search_faq`.
    5. Otherwise, a short description of what the assistant can do.

    This is not a model and it does not read the system prompt. A booking
    reference beats a policy word, so "Can I change booking BK-1002?" only
    looks up the booking. Swap in a real client when you want to test a model.
    """

    def complete(self, messages: list[Message], tools: list[dict]) -> LLMResponse:
        del tools  # the fake routes by keywords, not by the schema list
        if messages and messages[-1].role == "tool":
            return LLMResponse(content=_summarise_tool(messages[-1]))

        user_text = _latest_user_text(messages)
        reference = _booking_reference(user_text)
        if reference:
            return _call("lookup_booking", {"reference": reference})

        topic = _policy_topic(user_text)
        if topic:
            return _call("get_policy", {"topic": topic})

        if _looks_like_faq(user_text):
            return _call("search_faq", {"query": user_text})

        return LLMResponse(content=_HELP)


class ScriptedLLM:
    """Replay a list of responses. For offline tests of the agent loop."""

    def __init__(self, responses: list[LLMResponse]) -> None:
        self._responses = list(responses)
        self.calls: list[list[Message]] = []

    def complete(self, messages: list[Message], tools: list[dict]) -> LLMResponse:
        del tools  # a script does not consult the schema
        self.calls.append(list(messages))
        if not self._responses:
            raise LLMError("ScriptedLLM has no responses left")
        return self._responses.pop(0)


class OpenAICompatibleLLM:
    """Chat completions client for any server that supports tool calling.

    The model you pick must accept the `tools` field. A plain completion
    model will not drive the agent.
    """

    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = 60) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def complete(self, messages: list[Message], tools: list[dict]) -> LLMResponse:
        if not self.api_key:
            raise LLMError("LLM_API_KEY is empty. Set it in the environment or .env.")
        payload: dict = {
            "model": self.model,
            "messages": to_openai_messages(messages),
            "temperature": 0,
        }
        if tools:
            payload["tools"] = tools
        url = chat_completions_url(self.base_url)
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:300]
            raise LLMError(f"LLM request failed with HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise LLMError(f"LLM request failed: {exc.reason}") from exc
        try:
            body = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMError("LLM response was not JSON") from exc
        return parse_chat_response(body)


def build_llm(settings: Settings | None = None) -> LLM:
    """Pick a client from settings. The default is the offline fake."""
    chosen = settings or load_settings()
    if chosen.provider == "fake":
        return FakeLLM()
    if chosen.provider == "openai":
        if not chosen.api_key:
            raise LLMError(
                "LLM_PROVIDER=openai requires LLM_API_KEY. "
                "Leave the provider as 'fake' to run offline."
            )
        return OpenAICompatibleLLM(
            base_url=chosen.base_url,
            api_key=chosen.api_key,
            model=chosen.model,
        )
    raise LLMError(
        f"Unknown LLM_PROVIDER {chosen.provider!r}. Use 'fake' or 'openai'."
    )


def chat_completions_url(base_url: str) -> str:
    return base_url.rstrip("/") + "/chat/completions"


def to_openai_messages(messages: list[Message]) -> list[dict]:
    payload: list[dict] = []
    for message in messages:
        if message.role == "tool":
            payload.append(
                {
                    "role": "tool",
                    "tool_call_id": message.tool_call_id,
                    "content": message.content,
                }
            )
            continue
        item: dict = {"role": message.role, "content": message.content}
        if message.tool_calls:
            item["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(call.arguments),
                    },
                }
                for call in message.tool_calls
            ]
        payload.append(item)
    return payload


def parse_chat_response(body: dict) -> LLMResponse:
    try:
        message = body["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError("LLM response had no choices[0].message") from exc
    tool_calls: list[ToolCall] = []
    for call in message.get("tool_calls") or []:
        function = call.get("function") or {}
        tool_calls.append(
            ToolCall(
                id=str(call.get("id") or ""),
                name=str(function.get("name") or ""),
                arguments=_parse_arguments(function.get("arguments", "{}")),
            )
        )
    content = message.get("content") or ""
    return LLMResponse(content=str(content), tool_calls=tool_calls)


def _parse_arguments(raw: object) -> dict:
    if isinstance(raw, dict):
        return raw
    if raw is None:
        return {}
    text = str(raw).strip()
    if not text:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"_raw": text}
    if isinstance(parsed, dict):
        return parsed
    return {"_value": parsed}


_HELP = (
    "I can help with booking status, baggage, cancellations, changes, "
    "and common support questions."
)

_FAQ_CUES = ("opening hours", "hours", "contact", "phone", "email", "how long")


def _call(name: str, arguments: dict) -> LLMResponse:
    return LLMResponse(
        content="",
        tool_calls=[ToolCall(id="call-1", name=name, arguments=arguments)],
    )


def _latest_user_text(messages: list[Message]) -> str:
    for message in reversed(messages):
        if message.role == "user":
            return message.content
    return ""


def _booking_reference(text: str) -> str | None:
    match = re.search(r"\bBK-\d{4}\b", text, flags=re.IGNORECASE)
    if match is None:
        return None
    return match.group(0).upper()


def _policy_topic(text: str) -> str | None:
    lowered = text.lower()
    if "baggage" in lowered or "luggage" in lowered:
        return "baggage"
    if "cancel" in lowered:
        return "cancellation"
    if "reschedule" in lowered or "change" in lowered:
        return "changes"
    return None


def _looks_like_faq(text: str) -> bool:
    lowered = text.lower()
    return any(cue in lowered for cue in _FAQ_CUES)


def _summarise_tool(message: Message) -> str:
    try:
        data = json.loads(message.content)
    except json.JSONDecodeError:
        return "I couldn't read the tool result."
    if not isinstance(data, dict):
        return "I couldn't read the tool result."
    if "error" in data:
        return "I couldn't complete that request with the available tools."

    if message.name == "lookup_booking":
        if not data.get("found"):
            reference = data.get("reference") or "that reference"
            return f"I couldn't find a booking with reference {reference}."
        return (
            f"Booking {data['reference']} ({data['passenger']}) is {data['status']}: "
            f"{data['origin']} to {data['destination']} on {data['departure_date']}."
        )

    if message.name == "get_policy":
        if not data.get("found"):
            return (
                "I don't have a policy on that topic. "
                "I can help with cancellation, baggage, and changes."
            )
        topic = str(data.get("topic") or "policy").capitalize()
        return f"{topic} policy: {data.get('rule', '')}"

    if message.name == "search_faq":
        if not data.get("found"):
            return "I couldn't find an FAQ entry for that."
        return str(data.get("answer") or "")

    return "I looked that up, but I don't have a summary for this tool yet."
