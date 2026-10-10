"""Deterministic mock model adapter for unit and offline integration testing."""

from __future__ import annotations

import json
from collections.abc import Callable

from uaise.models.base import ModelProviderError, ModelResponse


class MockModel:
    """Mock model returning canned responses or executing a responder function."""

    def __init__(
        self,
        model_id: str = "mock_model",
        responses: list[str] | None = None,
        responder: Callable[[list[dict[str, str]]], str] | None = None,
        simulate_error: bool = False,
        error_message: str = "Simulated provider error",
    ) -> None:
        self._model_id = model_id
        self._responses = list(responses) if responses else []
        self._responder = responder
        self._simulate_error = simulate_error
        self._error_message = error_message
        self._call_history: list[list[dict[str, str]]] = []

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def call_history(self) -> list[list[dict[str, str]]]:
        return self._call_history

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> ModelResponse:
        self._call_history.append(messages)

        if self._simulate_error:
            raise ModelProviderError(self._error_message)

        if self._responder is not None:
            content = self._responder(messages)
        elif self._responses:
            content = self._responses.pop(0)
        else:
            # Default structured JSON response
            content = json.dumps(
                {
                    "action": "refactor_code",
                    "rationale": "Mock default action adheres to constraints.",
                    "parameters": {},
                }
            )

        return ModelResponse(
            content=content,
            model_id=self.model_id,
            prompt_tokens=15,
            completion_tokens=25,
            latency_seconds=0.01,
            metadata={"mock": True},
        )
