from __future__ import annotations

from src.prompts import UNCLEAR_INTENT_RESPONSE
from src.router import route_and_respond


class _FakeAPIClient:
    def __init__(self, response: str = "ok", should_raise: bool = False):
        self.response = response
        self.should_raise = should_raise
        self.calls: list[dict[str, str]] = []

    def generate_response_call(self, message: str, expert_prompt: str) -> str:
        self.calls.append({"message": message, "expert_prompt": expert_prompt})
        if self.should_raise:
            from src.api_client import APIClientError

            raise APIClientError("simulated generation error")
        return self.response


def test_route_and_respond_returns_clarifying_question_for_unclear_intent() -> None:
    client = _FakeAPIClient()

    result = route_and_respond(
        message="help me",
        intent={"intent": "unclear", "confidence": 0.2},
        api_client=client,
    )

    assert result == UNCLEAR_INTENT_RESPONSE
    assert len(client.calls) == 0



def test_route_and_respond_maps_valid_intent_and_calls_generation() -> None:
    client = _FakeAPIClient(response="Here is the coding answer")

    result = route_and_respond(
        message="How do I sort a list in python?",
        intent={"intent": "code", "confidence": 0.95},
        api_client=client,
    )

    assert result == "Here is the coding answer"
    assert len(client.calls) == 1
    assert client.calls[0]["message"] == "How do I sort a list in python?"
    assert "software engineer" in client.calls[0]["expert_prompt"].lower()



def test_route_and_respond_returns_clarifying_question_for_unknown_intent() -> None:
    client = _FakeAPIClient()

    result = route_and_respond(
        message="write me a poem",
        intent={"intent": "poetry", "confidence": 0.8},
        api_client=client,
    )

    assert result == UNCLEAR_INTENT_RESPONSE
    assert len(client.calls) == 0



def test_route_and_respond_returns_clarifying_question_for_empty_message() -> None:
    client = _FakeAPIClient()

    result = route_and_respond(
        message="   ",
        intent={"intent": "code", "confidence": 0.9},
        api_client=client,
    )

    assert result == UNCLEAR_INTENT_RESPONSE
    assert len(client.calls) == 0



def test_route_and_respond_handles_generation_error_gracefully() -> None:
    client = _FakeAPIClient(should_raise=True)

    result = route_and_respond(
        message="fix my bug",
        intent={"intent": "code", "confidence": 0.9},
        api_client=client,
    )

    assert "try again" in result.lower()
