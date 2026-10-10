"""Base model adapter interfaces and response representations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class ModelProviderError(RuntimeError):
    """Raised when an external model provider fails, times out, or returns an error."""


@dataclass(frozen=True)
class ModelResponse:
    """Structured response from a model adapter."""

    content: str
    model_id: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelAdapter(Protocol):
    """Protocol for model adapters communicating with local or hosted models."""

    @property
    def model_id(self) -> str:
        """Identifier of the model."""
        ...

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> ModelResponse:
        """Generate a response given a sequence of chat messages."""
        ...
