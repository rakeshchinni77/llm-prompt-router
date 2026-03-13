from __future__ import annotations

import json
import re
from typing import Any

from src.api_client import APIClientError, LLMApiClient, get_api_client
from src.prompts import SUPPORTED_INTENTS, get_classifier_prompt


FALLBACK_INTENT: dict[str, float | str] = {"intent": "unclear", "confidence": 0.0}


def classify_intent(message: str, api_client: LLMApiClient | None = None) -> dict[str, float | str]:
	if not message or not message.strip():
		return FALLBACK_INTENT.copy()

	client = api_client or get_api_client()
	classifier_prompt = get_classifier_prompt()

	try:
		raw_response = client.classify_intent_call(message=message, classifier_prompt=classifier_prompt)
	except APIClientError:
		return FALLBACK_INTENT.copy()

	parsed = _parse_classifier_json(raw_response)
	if parsed is None:
		return FALLBACK_INTENT.copy()

	intent = parsed.get("intent")
	confidence = parsed.get("confidence")

	if not isinstance(intent, str) or intent not in SUPPORTED_INTENTS:
		return FALLBACK_INTENT.copy()

	normalized_confidence = _normalize_confidence(confidence)
	if normalized_confidence is None:
		return FALLBACK_INTENT.copy()

	return {"intent": intent, "confidence": normalized_confidence}


def _parse_classifier_json(raw_response: str) -> dict[str, Any] | None:
	if not isinstance(raw_response, str) or not raw_response.strip():
		return None

	cleaned = _strip_markdown_code_fence(raw_response.strip())

	for candidate in (cleaned, _extract_first_json_object(cleaned)):
		if not candidate:
			continue
		try:
			obj = json.loads(candidate)
		except json.JSONDecodeError:
			continue
		if isinstance(obj, dict):
			return obj

	return None


def _strip_markdown_code_fence(text: str) -> str:
	if text.startswith("```") and text.endswith("```"):
		lines = text.splitlines()
		if len(lines) >= 3:
			return "\n".join(lines[1:-1]).strip()
	return text


def _extract_first_json_object(text: str) -> str:
	match = re.search(r"\{.*\}", text, flags=re.DOTALL)
	if match:
		return match.group(0)
	return ""


def _normalize_confidence(value: Any) -> float | None:
	if isinstance(value, bool):
		return None

	try:
		confidence = float(value)
	except (TypeError, ValueError):
		return None

	if not 0.0 <= confidence <= 1.0:
		return None

	return confidence
