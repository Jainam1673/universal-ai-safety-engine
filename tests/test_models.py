"""Tests for model adapters and HTTP mocking."""

import json

import httpx
import pytest

from uaise.models.base import ModelProviderError
from uaise.models.hosted import HostedOpenAIModel
from uaise.models.mock import MockModel


def test_mock_model_canned_and_responder():
    mock = MockModel(model_id="test_mock", responses=['{"action": "custom_act"}'])
    res = mock.generate([{"role": "user", "content": "hi"}])
    assert res.content == '{"action": "custom_act"}'
    assert res.model_id == "test_mock"
    assert len(mock.call_history) == 1

    # Using responder callable
    responder_mock = MockModel(
        responder=lambda msgs: json.dumps({"action": "dynamic", "count": len(msgs)})
    )
    res2 = responder_mock.generate([{"role": "user", "content": "test"}])
    assert "dynamic" in res2.content


def test_mock_model_simulated_error():
    mock = MockModel(simulate_error=True, error_message="Provider offline")
    with pytest.raises(ModelProviderError, match="Provider offline"):
        mock.generate([{"role": "user", "content": "test"}])


def test_hosted_model_missing_credentials():
    hosted = HostedOpenAIModel(api_key=None)
    # Explicitly clear env var if set
    hosted._api_key = None
    with pytest.raises(ValueError, match="UAISE_API_KEY environment variable is not configured"):
        hosted.generate([{"role": "user", "content": "test"}])


def test_hosted_model_with_mocked_http_transport():
    # Use httpx.MockTransport to test without network calls
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://mock.api/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer mock_key_123"
        body = json.loads(request.read())
        assert body["model"] == "gpt-4o-mini"
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": '{"action": "safe_act"}'}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    hosted = HostedOpenAIModel(
        base_url="https://mock.api/v1",
        api_key="mock_key_123",
        model_name="gpt-4o-mini",
        client=client,
    )
    res = hosted.generate([{"role": "user", "content": "hello"}])
    assert res.content == '{"action": "safe_act"}'
    assert res.prompt_tokens == 10
    assert res.completion_tokens == 5
    assert res.model_id == "hosted_gpt-4o-mini"


def test_hosted_model_http_status_error():
    def error_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "Invalid API key"})

    client = httpx.Client(transport=httpx.MockTransport(error_handler))
    hosted = HostedOpenAIModel(
        base_url="https://mock.api/v1",
        api_key="mock_key_123",
        client=client,
    )
    with pytest.raises(ModelProviderError, match="HTTP 401"):
        hosted.generate([{"role": "user", "content": "hello"}])


def test_hosted_model_timeout_error():
    def timeout_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("Connection timed out")

    client = httpx.Client(transport=httpx.MockTransport(timeout_handler))
    hosted = HostedOpenAIModel(
        base_url="https://mock.api/v1",
        api_key="mock_key_123",
        client=client,
    )
    with pytest.raises(ModelProviderError, match="timed out"):
        hosted.generate([{"role": "user", "content": "hello"}])
