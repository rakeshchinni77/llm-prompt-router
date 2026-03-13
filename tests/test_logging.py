from __future__ import annotations

import json

from src.logging import log_routing_decision



def test_log_routing_decision_writes_required_keys(tmp_path) -> None:
    log_file = tmp_path / "route_log.jsonl"

    entry = log_routing_decision(
        intent={"intent": "code", "confidence": 0.92},
        user_message="How do I sort a list in Python?",
        final_response="Use sorted(items).",
        log_file=log_file,
    )

    assert log_file.exists()
    assert entry["intent"] == "code"
    assert entry["confidence"] == 0.92

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    payload = json.loads(lines[0])
    assert set(["intent", "confidence", "user_message", "final_response"]).issubset(payload.keys())
    assert payload["intent"] == "code"
    assert payload["confidence"] == 0.92
    assert payload["user_message"] == "How do I sort a list in Python?"
    assert payload["final_response"] == "Use sorted(items)."



def test_log_routing_decision_appends_entries(tmp_path) -> None:
    log_file = tmp_path / "route_log.jsonl"

    log_routing_decision(
        intent={"intent": "writing", "confidence": 0.85},
        user_message="My paragraph sounds awkward.",
        final_response="Focus on shorter sentences.",
        log_file=log_file,
    )
    log_routing_decision(
        intent={"intent": "career", "confidence": 0.80},
        user_message="How do I improve my resume?",
        final_response="Quantify achievements and tailor each bullet.",
        log_file=log_file,
    )

    lines = log_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    first = json.loads(lines[0])
    second = json.loads(lines[1])

    assert first["intent"] == "writing"
    assert second["intent"] == "career"



def test_log_routing_decision_handles_missing_intent_safely(tmp_path) -> None:
    log_file = tmp_path / "route_log.jsonl"

    log_routing_decision(
        intent=None,
        user_message="help",
        final_response="Can you clarify if you need coding, data, writing, or career help?",
        log_file=log_file,
    )

    payload = json.loads(log_file.read_text(encoding="utf-8").splitlines()[0])
    assert payload["intent"] == "unclear"
    assert payload["confidence"] == 0.0
