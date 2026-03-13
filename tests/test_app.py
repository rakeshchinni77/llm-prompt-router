from __future__ import annotations

from fastapi.testclient import TestClient

from src.app import app


client = TestClient(app)


def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}



def test_route_endpoint_orchestrates_classifier_router_and_logger(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def _fake_classify_intent(message: str):
        calls["classified_message"] = message
        return {"intent": "code", "confidence": 0.91}

    def _fake_route_and_respond(message: str, intent: dict[str, object]):
        calls["routed_message"] = message
        calls["routed_intent"] = intent
        return "Use sorted(items)."

    def _fake_log_routing_decision(*, intent, user_message, final_response):
        calls["logged"] = {
            "intent": intent,
            "user_message": user_message,
            "final_response": final_response,
        }
        return {"ok": True}

    monkeypatch.setattr("src.app.classify_intent", _fake_classify_intent)
    monkeypatch.setattr("src.app.route_and_respond", _fake_route_and_respond)
    monkeypatch.setattr("src.app.log_routing_decision", _fake_log_routing_decision)

    response = client.post("/route", json={"message": "sort my list"})

    assert response.status_code == 200
    payload = response.json()

    assert payload["intent"] == "code"
    assert payload["confidence"] == 0.91
    assert payload["final_response"] == "Use sorted(items)."

    assert calls["classified_message"] == "sort my list"
    assert calls["routed_message"] == "sort my list"
    assert calls["routed_intent"] == {"intent": "code", "confidence": 0.91}
    assert calls["logged"]["user_message"] == "sort my list"



def test_route_endpoint_rejects_empty_message() -> None:
    response = client.post("/route", json={"message": ""})

    assert response.status_code == 422
