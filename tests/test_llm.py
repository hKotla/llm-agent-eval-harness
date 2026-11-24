"""Wire format for the OpenAI-compatible client. No socket is opened."""

import pytest

from support_agent.config import Settings
from support_agent.llm import (
    LLMError,
    Message,
    OpenAICompatibleLLM,
    ToolCall,
    build_llm,
    chat_completions_url,
    parse_chat_response,
    to_openai_messages,
)


def test_messages_round_trip_into_chat_completions_shape() -> None:
    messages = [
        Message(role="system", content="be brief"),
        Message(role="user", content="status of BK-1001"),
        Message(
            role="assistant",
            content="",
            tool_calls=[ToolCall("call-1", "lookup_booking", {"reference": "BK-1001"})],
        ),
        Message(
            role="tool",
            name="lookup_booking",
            tool_call_id="call-1",
            content='{"found": true}',
        ),
    ]
    payload = to_openai_messages(messages)

    assert payload[0] == {"role": "system", "content": "be brief"}
    assert payload[2]["tool_calls"][0]["function"]["arguments"] == '{"reference": "BK-1001"}'
    assert payload[3] == {
        "role": "tool",
        "tool_call_id": "call-1",
        "content": '{"found": true}',
    }


def test_parse_tool_call_response() -> None:
    parsed = parse_chat_response(
        {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "abc",
                                "type": "function",
                                "function": {
                                    "name": "get_policy",
                                    "arguments": '{"topic": "baggage"}',
                                },
                            }
                        ],
                    }
                }
            ]
        }
    )
    assert parsed.content == ""
    assert parsed.tool_calls[0].name == "get_policy"
    assert parsed.tool_calls[0].arguments == {"topic": "baggage"}


def test_parse_plain_answer_and_broken_arguments() -> None:
    parsed = parse_chat_response(
        {
            "choices": [
                {
                    "message": {
                        "content": "Hello",
                        "tool_calls": [
                            {"id": "1", "function": {"name": "get_policy", "arguments": "{"}}
                        ],
                    }
                }
            ]
        }
    )
    assert parsed.content == "Hello"
    assert parsed.tool_calls[0].arguments == {"_raw": "{"}


def test_parse_rejects_a_body_with_no_choices() -> None:
    with pytest.raises(LLMError):
        parse_chat_response({"choices": []})


def test_chat_url_strips_a_trailing_slash() -> None:
    assert chat_completions_url("http://localhost:11434/v1/") == (
        "http://localhost:11434/v1/chat/completions"
    )


def test_build_llm_openai_uses_the_configured_server() -> None:
    client = build_llm(
        Settings(
            provider="openai",
            base_url="http://localhost:11434/v1",
            api_key="test-key",
            model="llama3.2",
        )
    )
    assert isinstance(client, OpenAICompatibleLLM)
    assert client.model == "llama3.2"
    assert client.base_url == "http://localhost:11434/v1"


def test_build_llm_openai_without_a_key_fails() -> None:
    with pytest.raises(LLMError):
        build_llm(Settings(provider="openai", api_key=""))


def test_build_llm_rejects_an_unknown_provider() -> None:
    with pytest.raises(LLMError):
        build_llm(Settings(provider="banana"))
