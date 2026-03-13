from __future__ import annotations

from fastapi.testclient import TestClient

from src.app import app


client = TestClient(app)


REQUIRED_EXAMPLE_INPUTS: list[str] = [
    "how do i sort a list of objects in python?",
    "explain this sql query for me",
    "This paragraph sounds awkward, can you help me fix it?",
    "I'm preparing for a job interview, any tips?",
    "what's the average of these numbers: 12, 45, 23, 67, 34",
    "Help me make this better.",
    "I need to write a function that takes a user id and returns their profile, but also i need help with my resume.",
    "hey",
    "Can you write me a poem about clouds?",
    "Rewrite this sentence to be more professional.",
    "I'm not sure what to do with my career.",
    "what is a pivot table",
    "fxi thsi bug pls: for i in range(10) print(i)",
    "How do I structure a cover letter?",
    "My boss says my writing is too verbose.",
]


EXPECTED_LABELS: dict[str, str] = {
    "how do i sort a list of objects in python?": "code",
    "explain this sql query for me": "code",
    "This paragraph sounds awkward, can you help me fix it?": "writing",
    "I'm preparing for a job interview, any tips?": "career",
    "what's the average of these numbers: 12, 45, 23, 67, 34": "data",
    "Help me make this better.": "unclear",
    "I need to write a function that takes a user id and returns their profile, but also i need help with my resume.": "unclear",
    "hey": "unclear",
    "Can you write me a poem about clouds?": "unclear",
    "Rewrite this sentence to be more professional.": "writing",
    "I'm not sure what to do with my career.": "career",
    "what is a pivot table": "data",
    "fxi thsi bug pls: for i in range(10) print(i)": "code",
    "How do I structure a cover letter?": "career",
    "My boss says my writing is too verbose.": "writing",
}


def test_required_example_inputs_present() -> None:
    assert len(REQUIRED_EXAMPLE_INPUTS) == 15
    assert len(set(REQUIRED_EXAMPLE_INPUTS)) == 15



def test_route_endpoint_handles_required_examples_without_live_api(monkeypatch) -> None:
    logged_entries: list[dict[str, object]] = []

    def _fake_classify_intent(message: str):
        label = EXPECTED_LABELS[message]
        confidence = 0.90 if label != "unclear" else 0.0
        return {"intent": label, "confidence": confidence}

    def _fake_route_and_respond(message: str, intent: dict[str, object]):
        if intent["intent"] == "unclear":
            return "Are you asking for help with coding, data analysis, writing, or career advice?"
        return f"[{intent['intent']}] mock response for: {message}"

    def _fake_log_routing_decision(*, intent, user_message, final_response):
        entry = {
            "intent": intent.get("intent", "unclear"),
            "confidence": intent.get("confidence", 0.0),
            "user_message": user_message,
            "final_response": final_response,
        }
        logged_entries.append(entry)
        return entry

    monkeypatch.setattr("src.app.classify_intent", _fake_classify_intent)
    monkeypatch.setattr("src.app.route_and_respond", _fake_route_and_respond)
    monkeypatch.setattr("src.app.log_routing_decision", _fake_log_routing_decision)

    for message in REQUIRED_EXAMPLE_INPUTS:
        response = client.post("/route", json={"message": message})
        assert response.status_code == 200

        payload = response.json()
        expected_label = EXPECTED_LABELS[message]

        assert payload["intent"] == expected_label
        assert isinstance(payload["confidence"], float)
        assert isinstance(payload["final_response"], str)
        assert payload["final_response"]

    assert len(logged_entries) == 15
    for entry in logged_entries:
        assert set(["intent", "confidence", "user_message", "final_response"]).issubset(entry.keys())
