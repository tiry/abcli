"""Tests for agent invocation API client methods."""

from unittest.mock import MagicMock, patch

import pytest

from ab_cli.api.client import AgentBuilderClient
from ab_cli.api.exceptions import APIError
from ab_cli.config.settings import ABSettings
from ab_cli.models.invocation import (
    ChatMessage,
    InvokeRequest,
    InvokeResponse,
    InvokeTaskRequest,
)


@pytest.fixture
def settings() -> ABSettings:
    """Create test settings."""
    return ABSettings(
        api_endpoint="https://api.example.com/",
        oauth_token_url="https://auth.example.com/token",
        client_id="test-client",
        client_secret="test-secret",
        environment_id="env-12345678-1234-5678-1234-567812345678",
    )


@pytest.fixture
def mock_auth() -> MagicMock:
    """Create a mock auth client."""
    auth = MagicMock()
    auth.get_token.return_value = "test-token"
    return auth


@pytest.fixture
def client(settings: ABSettings, mock_auth: MagicMock) -> AgentBuilderClient:
    """Create a test client with mock auth."""
    return AgentBuilderClient(settings, auth_client=mock_auth)


class TestInvokeAgent:
    """Tests for invoke_agent method."""

    def test_invoke_agent_success(self, client: AgentBuilderClient) -> None:
        """Invoke agent returns InvokeResponse."""
        # Create request
        messages = [ChatMessage(role="user", content="Hello, agent!")]
        request = InvokeRequest(messages=messages)

        # Mock API response
        mock_response = {
            "response": "Hello! How can I help you today?",
            "finish_reason": "stop",
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 8,
                "total_tokens": 18
            }
        }

        with patch.object(client, "_request", return_value=mock_response) as mock_req:
            result = client.invoke_agent("agent-123", "version-456", request)

            # Verify response parsing
            assert isinstance(result, InvokeResponse)
            assert result.response == "Hello! How can I help you today?"
            assert result.finish_reason == "stop"
            assert result.usage["total_tokens"] == 18

            # Verify request was made correctly
            mock_req.assert_called_once()
            call_args = mock_req.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/agents/agent-123/versions/version-456/invoke"
            assert "json" in call_args[1]

    def test_invoke_agent_with_inference_params(self, client: AgentBuilderClient) -> None:
        """Invoke agent with temperature and max_tokens."""
        # Create request with inference parameters
        messages = [ChatMessage(role="user", content="Generate a creative story")]
        request = InvokeRequest(
            messages=messages,
            temperature=0.8,
            max_tokens=1000
        )

        # Mock API response
        mock_response = {
            "response": "Once upon a time...",
            "finish_reason": "stop",
            "usage": {"total_tokens": 100}
        }

        with patch.object(client, "_request", return_value=mock_response) as mock_req:
            result = client.invoke_agent("agent-123", "version-456", request)

            # Verify response
            assert result.response.startswith("Once upon a time")

            # Verify request payload included inference parameters
            mock_req.assert_called_once()
            call_args = mock_req.call_args
            json_payload = call_args[1]["json"]
            assert "temperature" in json_payload
            assert json_payload["temperature"] == 0.8
            assert "max_tokens" in json_payload
            assert json_payload["max_tokens"] == 1000

    def test_invoke_agent_latest_version(self, client: AgentBuilderClient) -> None:
        """Invoke agent with 'latest' version string."""
        # Create request
        messages = [ChatMessage(role="user", content="Hello")]
        request = InvokeRequest(messages=messages)

        # Mock API response
        mock_response = {"response": "Hi there!"}

        with patch.object(client, "_request", return_value=mock_response) as mock_req:
            client.invoke_agent("agent-123", "latest", request)

            # Verify URL used "latest" string
            mock_req.assert_called_once()
            call_args = mock_req.call_args
            assert call_args[0][1] == "/agents/agent-123/versions/latest/invoke"


class TestInvokeAgentStream:
    """Tests for invoke_agent_stream method."""

    def test_invoke_agent_stream(self, client: AgentBuilderClient) -> None:
        """Test streaming invocation with mocked SSE response."""
        # Create request
        messages = [ChatMessage(role="user", content="Hello")]
        request = InvokeRequest(messages=messages)

        # Mock httpx Client and response
        mock_response = MagicMock()
        mock_response.is_success = True

        # Setup stream lines to simulate SSE
        mock_response.iter_lines.return_value = [
            b'data: {"event": "text", "data": "Hello"}',
            b'data: {"event": "text", "data": " there!"}',
            b'data: {"event": "done"}'
        ]

        # Mock the POST method directly
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_response

        # Track URL used in post call
        captured_url = None

        # Use patching to capture the URL
        def mock_post_with_url_capture(*args, **kwargs):
            nonlocal captured_url
            captured_url = args[0] if args else kwargs.get('url', '')
            return mock_response

        mock_client.__enter__.return_value.post = mock_post_with_url_capture

        # Use the mock client in the patch
        with patch("httpx.Client", return_value=mock_client):
            # Call streaming endpoint
            events = list(client.invoke_agent_stream("agent-123", "version-456", request))

            # Verify URL has streaming endpoint
            assert captured_url is not None
            assert "invoke-stream" in captured_url

            # Verify events received
            assert len(events) == 3
            assert events[0].event == "text"
            assert events[0].data == "Hello"
            assert events[1].event == "text"
            assert events[1].data == " there!"
            assert events[2].event == "done"
            assert events[2].data is None

    def test_invoke_agent_stream_error_response(self, client: AgentBuilderClient) -> None:
        """Test streaming with error response from API."""
        # Create request
        messages = [ChatMessage(role="user", content="Hello")]
        request = InvokeRequest(messages=messages)

        # Mock error response
        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "Bad request"}

        # Create mock client that returns the error response
        mock_client = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client.__enter__.return_value = mock_client

        # Mock _handle_response to raise APIError
        def raise_api_error(response):
            raise APIError("Bad request")

        # Patch both the httpx.Client and _handle_response method
        with patch("httpx.Client", return_value=mock_client):
            with patch.object(client, "_handle_response", side_effect=raise_api_error):
                # This should raise APIError
                with pytest.raises(APIError):
                    list(client.invoke_agent_stream("agent-123", "version-456", request))

    def test_invoke_agent_stream_event_parsing(self, client: AgentBuilderClient) -> None:
        """Test parsing of different SSE event types."""
        # Create request
        messages = [ChatMessage(role="user", content="Hello")]
        request = InvokeRequest(messages=messages)

        # Mock response with various event types
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.iter_lines.return_value = [
            b'data: {"event": "text", "data": "Hello"}',
            b'data: {"event": "error", "data": "Error message"}',
            b'data: {"event": "done"}',
            b'keep-alive: ping',  # Should be ignored
        ]

        # Setup mock client and post method
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        # Use the mock client in the patch
        with patch("httpx.Client", return_value=mock_client):
            # Call streaming endpoint
            events = list(client.invoke_agent_stream("agent-123", "version-456", request))

            # Only SSE data lines should be processed
            assert len(events) == 3
            assert events[0].event == "text"
            assert events[1].event == "error"
            assert events[2].event == "done"


class TestInvokeTask:
    """Tests for invoke_task method."""

    def test_invoke_task_success(self, client: AgentBuilderClient) -> None:
        """Invoke task returns InvokeResponse."""
        # Create request
        inputs = {"query": "What is the capital of France?", "context": "geography"}
        request = InvokeTaskRequest(inputs=inputs)

        # Mock API response
        mock_response = {
            "response": "The capital of France is Paris.",
            "metadata": {"confidence": 0.98}
        }

        with patch.object(client, "_request", return_value=mock_response) as mock_req:
            result = client.invoke_task("agent-123", "version-456", request)

            # Verify response parsing
            assert isinstance(result, InvokeResponse)
            assert "Paris" in result.response
            assert result.metadata["confidence"] == 0.98

            # Verify request was made correctly
            mock_req.assert_called_once()
            call_args = mock_req.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/agents/agent-123/versions/version-456/invoke-task"
            assert call_args[1]["json"]["inputs"] == inputs

    def test_invoke_task_complex_input(self, client: AgentBuilderClient) -> None:
        """Invoke task with complex nested input structure."""
        # Create request with nested input structure
        inputs = {
            "document": {
                "title": "Annual Report",
                "sections": [
                    {"heading": "Executive Summary", "content": "..."},
                    {"heading": "Financial Results", "content": "..."}
                ],
                "metadata": {
                    "year": 2025,
                    "company": "Example Corp"
                }
            },
            "instructions": "Extract key financial figures"
        }
        request = InvokeTaskRequest(inputs=inputs)

        # Mock API response
        mock_response = {"response": "Revenue: $10M, Profit: $2M"}

        with patch.object(client, "_request", return_value=mock_response) as mock_req:
            client.invoke_task("agent-123", "version-456", request)

            # Verify complex input structure was sent correctly
            mock_req.assert_called_once()
            call_args = mock_req.call_args
            assert call_args[1]["json"]["inputs"] == inputs
            assert call_args[1]["json"]["inputs"]["document"]["metadata"]["year"] == 2025


class TestInvokeTaskStream:
    """Tests for invoke_task_stream method."""

    def test_invoke_task_stream(self, client: AgentBuilderClient) -> None:
        """Test streaming task invocation."""
        # Create request
        inputs = {"query": "Explain quantum computing"}
        request = InvokeTaskRequest(inputs=inputs)

        # Mock response
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.iter_lines.return_value = [
            b'data: {"event": "text", "data": "Quantum computing is"}',
            b'data: {"event": "text", "data": " a type of computing that"}',
            b'data: {"event": "done"}'
        ]

        # Setup mock client and post method
        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post.return_value = mock_response

        # Use the mock client in the patch
        with patch("httpx.Client", return_value=mock_client):
            events = list(client.invoke_task_stream("agent-123", "version-456", request))

            # Verify events
            assert len(events) == 3
            assert events[0].data == "Quantum computing is"
            assert events[1].data == " a type of computing that"
            assert events[2].event == "done"

    def test_invoke_task_stream_url(self, client: AgentBuilderClient) -> None:
        """Test correct URL is used for task stream endpoint."""
        # Create request
        request = InvokeTaskRequest(inputs={"query": "test"})

        # Mock response
        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.iter_lines.return_value = [b'data: {"event": "done"}']

        # Track URL used in post call
        captured_url = None

        # Create mock client that captures URL
        def mock_post_with_url_capture(*args, **kwargs):
            nonlocal captured_url
            captured_url = args[0] if args else kwargs.get('url', '')
            return mock_response

        mock_client = MagicMock()
        mock_client.__enter__.return_value = mock_client
        mock_client.post = mock_post_with_url_capture

        # Use the mock client in the patch
        with patch("httpx.Client", return_value=mock_client):
            list(client.invoke_task_stream("agent-123", "version-456", request))

            # Verify URL has streaming endpoint
            assert captured_url is not None
            assert "invoke-task-stream" in captured_url
            assert "agent-123" in captured_url
            assert "version-456" in captured_url
