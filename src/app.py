from __future__ import annotations

import argparse
import json

from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.classifier import classify_intent
from src.config import get_settings
from src.logging import log_routing_decision
from src.router import route_and_respond


settings = get_settings()
app = FastAPI(title=settings.app_name)


class RouteRequest(BaseModel):
	message: str = Field(..., min_length=1, description="User message to route")


class RouteResponse(BaseModel):
	intent: str
	confidence: float
	final_response: str


def process_message(message: str) -> RouteResponse:
	intent_result = classify_intent(message)
	final_response = route_and_respond(message, intent_result)

	log_routing_decision(
		intent=intent_result,
		user_message=message,
		final_response=final_response,
	)

	return RouteResponse(
		intent=str(intent_result.get("intent", "unclear")),
		confidence=float(intent_result.get("confidence", 0.0)),
		final_response=final_response,
	)


@app.get("/health")
def health() -> dict[str, str]:
	return {"status": "ok"}


@app.post("/route", response_model=RouteResponse)
def route_message(payload: RouteRequest) -> RouteResponse:
	return process_message(payload.message)


def run_cli() -> int:
	parser = argparse.ArgumentParser(description="LLM Prompt Router CLI")
	parser.add_argument("message", help="Message to route")
	args = parser.parse_args()

	result = process_message(args.message)
	print(json.dumps(result.model_dump(), ensure_ascii=True, indent=2))
	return 0


if __name__ == "__main__":
	raise SystemExit(run_cli())
