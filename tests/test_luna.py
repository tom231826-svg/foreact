"""Offline checks for Luna defaults, request compatibility and explicit overrides."""

from unittest.mock import Mock

import pytest
import requests

from foreact import llm


@pytest.fixture(autouse=True)
def clean_llm_environment(monkeypatch):
    for name in (
        "FOREACT_LLM_PROVIDER", "FOREACT_LLM_MODEL",
        "HEATLINE_LLM_PROVIDER", "HEATLINE_LLM_MODEL",
        "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.parametrize("override", [None, "", "gpt-6-luna", "gpt-4o-mini"])
def test_luna_default_request_and_model_override(monkeypatch, override):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-openai")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-anthropic")
    if override is not None:
        monkeypatch.setenv("FOREACT_LLM_MODEL", override)
    post = Mock(return_value=Mock(
        status_code=200,
        json=lambda: {"choices": [{"message": {"content": " selected "}}]},
    ))
    monkeypatch.setattr(requests, "post", post)

    assert llm.active_provider() == "openai"
    assert llm.generate("reviewed instructions", "input", max_tokens=100) == "selected"
    model = override or "gpt-6-luna"
    expected = {
        "model": model,
        "max_completion_tokens": 100,
        "messages": [
            {"role": "system", "content": "reviewed instructions"},
            {"role": "user", "content": "input"},
        ],
    }
    if model == "gpt-6-luna":
        expected["reasoning_effort"] = "none"
    assert post.call_count == 1
    assert post.call_args.args == (llm.OPENAI_URL,)
    assert post.call_args.kwargs["json"] == expected
    assert post.call_args.kwargs["timeout"] == llm.REQUEST_TIMEOUT_S


@pytest.mark.parametrize("anthropic_key", [False, True])
def test_missing_openai_key_does_not_automatically_switch_provider(monkeypatch, anthropic_key):
    if anthropic_key:
        monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic")
    post = Mock()
    monkeypatch.setattr(requests, "post", post)
    assert llm.active_provider() == "none"
    with pytest.raises(llm.LLMError, match="OPENAI_API_KEY"):
        llm.generate("system", "user")
    post.assert_not_called()


def test_explicit_anthropic_remains_an_opt_in(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic")
    monkeypatch.setenv("FOREACT_LLM_PROVIDER", "anthropic")
    post = Mock(return_value=Mock(
        status_code=200,
        json=lambda: {"content": [{"type": "text", "text": "legacy"}]},
    ))
    monkeypatch.setattr(requests, "post", post)
    assert llm.generate("system", "user", max_tokens=100) == "legacy"
    assert post.call_args.args == (llm.ANTHROPIC_URL,)
    assert post.call_args.kwargs["json"]["model"] == llm.DEFAULT_ANTHROPIC_MODEL
    assert post.call_args.kwargs["json"]["max_tokens"] == 100
    assert "reasoning_effort" not in post.call_args.kwargs["json"]


def test_explicit_none_still_disables_ai(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic")
    monkeypatch.setenv("FOREACT_LLM_PROVIDER", "none")
    assert llm.active_provider() == "none"
