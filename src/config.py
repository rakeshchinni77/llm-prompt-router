from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """Application configuration settings."""

    # App settings
    app_name: str
    app_env: str
    app_host: str
    app_port: int
    app_debug: bool

    # LLM provider settings
    llm_provider: str
    groq_api_key: str
    groq_model_classifier: str
    groq_model_generation: str

    # Router settings
    app_confidence_threshold: float

    # Logging
    log_file: Path

    @property
    def has_groq_api_key(self) -> bool:
        return bool(self.groq_api_key.strip())


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"true", "1", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


@lru_cache()
def get_settings() -> Settings:
    """Load and cache application settings."""

    confidence_threshold = _get_float("APP_CONFIDENCE_THRESHOLD", 0.70)

    if not 0 <= confidence_threshold <= 1:
        raise ValueError("APP_CONFIDENCE_THRESHOLD must be between 0 and 1.")

    log_file = Path(os.getenv("LOG_FILE", "route_log.jsonl"))

    if not log_file.is_absolute():
        log_file = BASE_DIR / log_file

    return Settings(
        app_name=os.getenv("APP_NAME", "LLM Prompt Router"),
        app_env=os.getenv("APP_ENV", "development"),
        app_host=os.getenv("APP_HOST", "127.0.0.1"),
        app_port=_get_int("APP_PORT", 8000),
        app_debug=_get_bool("APP_DEBUG", True),
        llm_provider=os.getenv("LLM_PROVIDER", "groq").strip().lower(),
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        groq_model_classifier=os.getenv("GROQ_MODEL_CLASSIFIER", "llama-3.1-8b-instant"),
        groq_model_generation=os.getenv("GROQ_MODEL_GENERATION", "llama-3.3-70b-versatile"),
        app_confidence_threshold=confidence_threshold,
        log_file=log_file,
    )


def validate_runtime_config(settings: Settings | None = None) -> list[str]:
    """Check runtime configuration issues."""

    settings = settings or get_settings()
    issues = []

    if settings.llm_provider != "groq":
        issues.append("LLM_PROVIDER must be set to 'groq'.")

    if not settings.has_groq_api_key:
        issues.append("GROQ_API_KEY is not configured.")

    return issues