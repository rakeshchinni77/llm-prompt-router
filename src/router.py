from __future__ import annotations

from typing import Mapping

from src.api_client import APIClientError, LLMApiClient, get_api_client
from src.prompts import UNCLEAR_INTENT_RESPONSE, get_expert_prompt


def route_and_respond(
    message: str,
    intent: Mapping[str, object],
    api_client: LLMApiClient | None = None,
) -> str:
    """
    Route a user message to the appropriate expert persona and return the final response.

    Parameters:
        message: The original user message
        intent: Result from classify_intent()
        api_client: Optional injected API client (used for testing)

    Returns:
        Final response string
    """

    # Validate message

    if not message or not message.strip():
        return UNCLEAR_INTENT_RESPONSE

    # Extract intent label

    intent_label = intent.get("intent") if isinstance(intent, Mapping) else None

    if not isinstance(intent_label, str) or intent_label == "unclear":
        return UNCLEAR_INTENT_RESPONSE

    # Retrieve expert prompt

    expert_prompt = get_expert_prompt(intent_label)

    if not expert_prompt:
        return UNCLEAR_INTENT_RESPONSE

    # Generate response using LLM

    client = api_client or get_api_client()

    try:
        return client.generate_response_call(
            message=message,
            expert_prompt=expert_prompt,
        )

    except APIClientError:
        return (
            "I ran into an issue generating a response right now. "
            "Please try again in a moment."
        )