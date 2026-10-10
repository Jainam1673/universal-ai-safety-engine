"""Hosted model adapter for OpenAI-compatible chat completion endpoints."""

from __future__ import annotations

import os
import time
from typing import Any

import httpx

from uaise.models.base import ModelProviderError, ModelResponse

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT_SECONDS = 30.0


class HostedOpenAIModel:
    """Communicates with OpenAI-compatible chat completion endpoints.

    All credentials must be supplied via environment variables or explicit parameters.
    Secrets are never included in exceptions, logs, or serialized records.
    """

    def __init__(
        self,
        model_name: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        client: httpx.Client | None = None,
    ) -> None:
        self._model_name = model_name or os.environ.get("UAISE_MODEL", DEFAULT_MODEL)
        self._base_url = (
            base_url or os.environ.get("UAISE_API_BASE_URL", DEFAULT_BASE_URL)
        ).rstrip("/")
        self._api_key = api_key or os.environ.get("UAISE_API_KEY")
        self._timeout_seconds = timeout_seconds
        self._client = client

    @property
    def model_id(self) -> str:
        return f"hosted_{self._model_name}"

    @property
    def has_credentials(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        max_tokens: int = 500,
    ) -> ModelResponse:
        """Call chat completions endpoint and return structured ModelResponse."""
        if not self.has_credentials:
            raise ValueError(
                "UAISE_API_KEY environment variable is not configured. "
                "To evaluate hosted models, set 'UAISE_API_KEY'. "
                "For offline reproducible testing, use ScriptedAgent or MockModel."
            )

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start_time = time.monotonic()
        try:
            if self._client is not None:
                resp = self._client.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self._timeout_seconds,
                )
            else:
                with httpx.Client(timeout=self._timeout_seconds) as client:
                    resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        except httpx.TimeoutException as exc:
            raise ModelProviderError(
                f"Model request to '{self._base_url}' timed out after {self._timeout_seconds}s."
            ) from exc
        except httpx.HTTPStatusError as exc:
            # Avoid leaking headers or sensitive URLs
            status_code = exc.response.status_code
            error_detail = exc.response.text[:200]
            raise ModelProviderError(
                f"Model provider returned HTTP {status_code}: {error_detail}"
            ) from exc
        except Exception as exc:
            raise ModelProviderError(f"Model request failed: {type(exc).__name__}") from exc

        latency = time.monotonic() - start_time

        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
            usage = data.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelProviderError(f"Malformed completion response from provider: {exc}") from exc

        return ModelResponse(
            content=content,
            model_id=self.model_id,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_seconds=latency,
            metadata={"base_url": self._base_url, "model_name": self._model_name},
        )
