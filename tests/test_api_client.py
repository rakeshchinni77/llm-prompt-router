from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from src.api_client import APIClientError, APIResponseFormatError, LLMApiClient
from src.config import Settings


class _FakeCompletionsAPI:
	def __init__(self, response_or_exc):
		self._response_or_exc = response_or_exc
		self.calls = []

	def create(self, **kwargs):
		self.calls.append(kwargs)
		if isinstance(self._response_or_exc, Exception):
			raise self._response_or_exc
		return self._response_or_exc


class _FakeGroq:
	def __init__(self, response_or_exc):
		self.chat = SimpleNamespace(completions=_FakeCompletionsAPI(response_or_exc))


def _make_groq_response(text: str | None):
	message = SimpleNamespace(content=text)
	choice = SimpleNamespace(message=message)
	return SimpleNamespace(choices=[choice])


def _settings() -> Settings:
	return Settings(
		app_name="LLM Prompt Router",
		app_env="test",
		app_host="127.0.0.1",
		app_port=8000,
		app_debug=False,
		llm_provider="groq",
		groq_api_key="fake-key",
		groq_model_classifier="llama3-8b-8192",
		groq_model_generation="llama3-70b-8192",
		app_confidence_threshold=0.7,
		log_file=Path("route_log.jsonl"),
	)


def test_classify_uses_classifier_model(monkeypatch):
	fake_groq = _FakeGroq(_make_groq_response('{"intent":"code","confidence":0.9}'))
	monkeypatch.setattr("src.api_client.Groq", lambda api_key: fake_groq)

	client = LLMApiClient(settings=_settings())
	result = client.classify_intent_call("sort list", "classify")

	assert result == '{"intent":"code","confidence":0.9}'
	assert fake_groq.chat.completions.calls[0]["model"] == "llama3-8b-8192"


def test_generate_uses_generation_model(monkeypatch):
	fake_groq = _FakeGroq(_make_groq_response("Use sorted(data)"))
	monkeypatch.setattr("src.api_client.Groq", lambda api_key: fake_groq)

	client = LLMApiClient(settings=_settings())
	result = client.generate_response_call("sort list", "code expert")

	assert "sorted" in result
	assert fake_groq.chat.completions.calls[0]["model"] == "llama3-70b-8192"


def test_provider_error_wrapped(monkeypatch):
	fake_groq = _FakeGroq(RuntimeError("quota"))
	monkeypatch.setattr("src.api_client.Groq", lambda api_key: fake_groq)

	client = LLMApiClient(settings=_settings())

	with pytest.raises(APIClientError):
		client.classify_intent_call("hello", "classify")


def test_empty_output_uses_fallback_extraction(monkeypatch):
	fake_groq = _FakeGroq(_make_groq_response("fallback text"))
	monkeypatch.setattr("src.api_client.Groq", lambda api_key: fake_groq)

	client = LLMApiClient(settings=_settings())
	result = client.generate_response_call("hello", "prompt")

	assert result == "fallback text"


def test_missing_text_raises_format_error(monkeypatch):
	fake_groq = _FakeGroq(_make_groq_response(None))
	monkeypatch.setattr("src.api_client.Groq", lambda api_key: fake_groq)

	client = LLMApiClient(settings=_settings())

	with pytest.raises(APIResponseFormatError):
		client.generate_response_call("hello", "prompt")
