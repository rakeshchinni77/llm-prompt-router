from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from src.config import get_settings


def log_routing_decision(
	*,
	intent: Mapping[str, object] | None,
	user_message: str,
	final_response: str,
	log_file: Path | None = None,
) -> dict[str, object]:
	"""Append one routing event as a JSON line and return the logged payload."""
	entry = _build_log_entry(intent=intent, user_message=user_message, final_response=final_response)

	target_file = log_file or get_settings().log_file
	target_file.parent.mkdir(parents=True, exist_ok=True)

	with target_file.open("a", encoding="utf-8") as handle:
		handle.write(json.dumps(entry, ensure_ascii=True) + "\n")

	return entry


def _build_log_entry(
	*,
	intent: Mapping[str, object] | None,
	user_message: str,
	final_response: str,
) -> dict[str, object]:
	intent_label = "unclear"
	confidence_value = 0.0

	if isinstance(intent, Mapping):
		raw_intent = intent.get("intent")
		if isinstance(raw_intent, str) and raw_intent.strip():
			intent_label = raw_intent.strip()

		confidence_value = _normalize_confidence(intent.get("confidence"))

	return {
		"timestamp": datetime.now(timezone.utc).isoformat(),
		"intent": intent_label,
		"confidence": confidence_value,
		"user_message": user_message,
		"final_response": final_response,
	}


def _normalize_confidence(value: object) -> float:
	if isinstance(value, bool):
		return 0.0

	try:
		confidence = float(value)
	except (TypeError, ValueError):
		return 0.0

	if confidence < 0.0:
		return 0.0
	if confidence > 1.0:
		return 1.0
	return confidence
