from __future__ import annotations

import pytest
from skillopt_train.providers import (
    MockProvider,
    ScriptedTurn,
    extract_json,
    make_json_response,
)


def test_mock_provider_default_response() -> None:
    provider = MockProvider()
    response = provider.complete(
        pytest.importorskip("skillopt_train.providers").ModelRequest.new(prompt="hi"),
    )
    assert "edits" in response.text


def test_mock_provider_scripted_match() -> None:
    provider = MockProvider()
    payload = {"addendum": "rule one\n", "reasoning": "tightened"}
    provider.script(ScriptedTurn(match="", response=make_json_response(payload)))
    response = provider.complete(
        pytest.importorskip("skillopt_train.providers").ModelRequest.new(prompt="anything"),
    )
    parsed = extract_json(response.text)
    assert parsed["addendum"] == "rule one\n"


def test_mock_provider_records_call_log() -> None:
    provider = MockProvider()
    request = pytest.importorskip("skillopt_train.providers").ModelRequest.new(prompt="x")
    provider.complete(request)
    assert len(provider.call_log) == 1
    assert provider.call_log[0].prompt == "x"


def test_extract_json_from_fence() -> None:
    text = 'noise\n```json\n{"key": "value"}\n```\nmore noise'
    parsed = extract_json(text)
    assert parsed["key"] == "value"


def test_extract_json_from_bare_braces() -> None:
    text = 'noise {"key": "value"} more noise'
    parsed = extract_json(text)
    assert parsed["key"] == "value"


def test_extract_json_rejects_plain_text() -> None:
    with pytest.raises(Exception):
        extract_json("no json here at all")


def test_estimate_tokens_handles_empty() -> None:
    from skillopt_train.providers import estimate_tokens
    assert estimate_tokens("") == 0
    assert estimate_tokens("hello") >= 1