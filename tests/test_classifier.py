from __future__ import annotations

from src.classifier import classify_intent


class _FakeAPIClient:
    def __init__(self, response: str | None = None, should_raise: bool = False):
        self.response = response
        self.should_raise = should_raise

    def classify_intent_call(self, message: str, classifier_prompt: str) -> str:
        if self.should_raise:
            from src.api_client import APIClientError

            raise APIClientError("simulated provider failure")
        return self.response or ""


def test_classify_intent_returns_valid_schema_for_good_json() -> None:
    client = _FakeAPIClient('{"intent":"code","confidence":0.91}')

    result = classify_intent("how do i sort list in python", api_client=client)

    assert result["intent"] == "code"
    assert isinstance(result["confidence"], float)
    assert result["confidence"] == 0.91



def test_classify_intent_accepts_json_inside_extra_text() -> None:
    client = _FakeAPIClient('Here you go: {"intent":"data","confidence":0.88}')

    result = classify_intent("what is mean of this dataset", api_client=client)

    assert result == {"intent": "data", "confidence": 0.88}



def test_classify_intent_falls_back_on_invalid_json() -> None:
    client = _FakeAPIClient("intent=code, confidence=high")

    result = classify_intent("help", api_client=client)

    assert result == {"intent": "unclear", "confidence": 0.0}



def test_classify_intent_falls_back_on_invalid_intent_label() -> None:
    client = _FakeAPIClient('{"intent":"poetry","confidence":0.85}')

    result = classify_intent("write a poem", api_client=client)

    assert result == {"intent": "unclear", "confidence": 0.0}



def test_classify_intent_falls_back_on_out_of_range_confidence() -> None:
    client = _FakeAPIClient('{"intent":"code","confidence":1.5}')

    result = classify_intent("debug loop", api_client=client)

    assert result == {"intent": "unclear", "confidence": 0.0}



def test_classify_intent_falls_back_when_api_client_raises() -> None:
    client = _FakeAPIClient(should_raise=True)

    result = classify_intent("hello", api_client=client)

    assert result == {"intent": "unclear", "confidence": 0.0}



def test_classify_intent_falls_back_for_empty_message() -> None:
    client = _FakeAPIClient('{"intent":"code","confidence":0.95}')

    result = classify_intent("   ", api_client=client)

    assert result == {"intent": "unclear", "confidence": 0.0}
