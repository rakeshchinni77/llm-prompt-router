from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from groq import Groq

from src.config import Settings, get_settings

# CUSTOM EXCEPTIONS

class APIClientError(Exception):
    """Raised when an LLM API request fails."""


class APIResponseFormatError(APIClientError):
    """Raised when provider returns an unexpected response format."""


# REQUEST STRUCTURE

@dataclass(frozen=True)
class PromptRequest:
    system_prompt: str
    user_message: str
    model: str
    temperature: float
    max_output_tokens: int


# GROQ CLIENT WRAPPER

class LLMApiClient:
    """
    Centralized Groq API client used by the application.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

        if self.settings.llm_provider != "groq":
            raise APIClientError("LLM_PROVIDER must be set to 'groq'.")

        if not self.settings.has_groq_api_key:
            raise APIClientError("GROQ_API_KEY is not configured.")

        self._client = Groq(api_key=self.settings.groq_api_key)

    # CLASSIFIER CALL

    def classify_intent_call(self, message: str, classifier_prompt: str) -> str:
        request = PromptRequest(
            system_prompt=classifier_prompt,
            user_message=message,
            model=self.settings.groq_model_classifier,
            temperature=0.0,
            max_output_tokens=150,
        )

        return self._request_text(request)

    # RESPONSE GENERATION CALL

    def generate_response_call(self, message: str, expert_prompt: str) -> str:
        request = PromptRequest(
            system_prompt=expert_prompt,
            user_message=message,
            model=self.settings.groq_model_generation,
            temperature=0.3,
            max_output_tokens=900,
        )

        return self._request_text(request)

    # INTERNAL OPENAI REQUEST

    def _request_text(self, request: PromptRequest) -> str:

        if not request.system_prompt.strip():
            raise ValueError("system_prompt cannot be empty.")

        if not request.user_message.strip():
            raise ValueError("user_message cannot be empty.")

        try:
            response = self._client.chat.completions.create(
                model=request.model,
                messages=[
                    {
                        "role": "system",
                        "content": request.system_prompt,
                    },
                    {
                        "role": "user",
                        "content": request.user_message,
                    },
                ],
                temperature=request.temperature,
                max_tokens=request.max_output_tokens,
            )

        except Exception as exc:
            raise APIClientError("Groq request failed.") from exc

        fallback_text = self._extract_text(response)

        if fallback_text:
            return fallback_text

        raise APIResponseFormatError("Groq response did not contain text output.")

    # TEXT EXTRACTION FALLBACK

    @staticmethod
    def _extract_text(response: Any) -> str:
        choices = getattr(response, "choices", None)
        if not choices or not isinstance(choices, list):
            return ""

        first_choice = choices[0]
        message = getattr(first_choice, "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()

        return ""


# GLOBAL CLIENT INSTANCE

@lru_cache(maxsize=1)
def get_api_client() -> LLMApiClient:
    return LLMApiClient()