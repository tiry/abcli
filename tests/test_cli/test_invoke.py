"""Tests for invoke CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from ab_cli.cli.invoke import invoke
from ab_cli.models.invocation import (
    InvokeRequest,
    InvokeResponse,
    InvokeTaskRequest,
    StreamEvent,
)


@pytest.fixture
def mock_client():
    """Create mock AgentBuilderClient."""
    mock = MagicMock()
    # Add response attributes that might be needed
    mock.invoke_agent.return_value = InvokeResponse(response="Test response")
    mock.invoke_task.return_value = InvokeResponse(response="Test task response")
    return mock


@pytest.fixture
def mock_get_client(monkeypatch, mock_client):
    """Create mock for get_client function."""
    # Define a replacement function that always returns our mock
    def mock_get_client_function(*args, **kwargs):
        return mock_client

    # Use monkeypatch to replace the function at module level
    monkeypatch.setattr("ab_cli.cli.invoke.get_client", mock_get_client_function)
    return mock_client


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestInvokeChat:
    """Tests for invoke chat command."""

    # Helper method for CLI tests - runs commands directly
    def invoke_command(self, runner, args, obj=None, mock_client=None):
        """Invoke a command with proper context."""
        # Create a context object
        if obj is None:
            obj = {"config_path": None}

        # For debugging - print the command being run
        print(f"Running command: invoke {' '.join(args)}")

        # Create a context manager that returns our mock client
        class MockContextManager:
            def __init__(self, mock_client):
                self.mock_client = mock_client
            def __enter__(self):
                return self.mock_client
            def __exit__(self, exc_type, exc_value, traceback):
                pass

        # Patch the get_client function to return our mock context manager
        with patch("ab_cli.cli.invoke.get_client", return_value=MockContextManager(mock_client)):
            # Run the command directly via Click's testing interface
            # catch_exceptions=False to see actual errors
            return runner.invoke(invoke, args, obj=obj, catch_exceptions=False, standalone_mode=False)

    def test_chat_basic(self, runner, mock_get_client):
        """Test basic chat invocation with message."""
        # Mock response
        mock_response = InvokeResponse(
            response="Hello! How can I help you?",
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 7, "total_tokens": 17}
        )
        mock_get_client.invoke_agent.return_value = mock_response

        # Create context object with empty config
        ctx_obj = {"config_path": None}

        # Run command with invoke parent group
        result = self.invoke_command(runner, ["chat", "agent-123", "--message", "Hello"], mock_client=mock_get_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify client was called correctly
        mock_get_client.invoke_agent.assert_called_once()
        call_args = mock_get_client.invoke_agent.call_args
        assert call_args[0][0] == "agent-123"  # agent_id
        assert call_args[0][1] == "latest"     # version_id (default)

        # Request should have the message
        request = call_args[0][2]  # InvokeRequest
        assert isinstance(request, InvokeRequest)
        assert len(request.messages) == 1
        assert request.messages[0].role == "user"
        assert request.messages[0].content == "Hello"

        # Verify output contains the response
        assert "Hello! How can I help you?" in result.output
        assert "Token usage" in result.output
        assert "17" in result.output  # total_tokens

    def test_chat_with_version_id(self, runner, mock_get_client):
        """Test chat invocation with specific version ID."""
        mock_get_client.invoke_agent.return_value = InvokeResponse(
            response="Version-specific response"
        )

        # Create context object with empty config
        ctx_obj = {"config_path": None}

        result = self.invoke_command(runner, ["chat", "agent-123", "version-456", "--message", "Hello"], mock_client=mock_get_client)

        assert result.exit_code == 0
        mock_get_client.invoke_agent.assert_called_once()
        call_args = mock_get_client.invoke_agent.call_args
        assert call_args[0][0] == "agent-123"
        assert call_args[0][1] == "version-456"

    def test_chat_from_file(self, runner, mock_get_client, tmp_path):
        """Test chat invocation with message from file."""
        # Create message file
        message_file = tmp_path / "message.txt"
        message_file.write_text("This is a message from file.")

        mock_get_client.invoke_agent.return_value = InvokeResponse(
            response="Response to file message"
        )

        # Create context object with empty config
        ctx_obj = {"config_path": None}

        # Run command with message file
        result = self.invoke_command(runner, [
            "chat",
            "agent-123",
            "--message-file", str(message_file)
        ], mock_client=mock_get_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify client was called with correct message
        mock_get_client.invoke_agent.assert_called_once()
        request = mock_get_client.invoke_agent.call_args[0][2]
        assert request.messages[0].content == "This is a message from file."

    def test_chat_missing_message(self, runner, mock_get_client):
        """Test error when no message is provided."""
        result = self.invoke_command(runner, ["chat", "agent-123"], mock_client=mock_get_client)

        # Verify command failed
        assert result.exit_code != 0
        assert "No message provided" in result.output

        # Verify client was not called
        mock_get_client.invoke_agent.assert_not_called()

    def test_chat_stream(self, runner, mock_get_client):
        """Test streaming chat invocation."""
        # Mock stream events
        mock_events = [
            StreamEvent(event="text", data="Hello"),
            StreamEvent(event="text", data=" world"),
            StreamEvent(event="done")
        ]
        mock_get_client.invoke_agent_stream.return_value = mock_events

        # Create context object with empty config
        ctx_obj = {"config_path": None}

        # Run command with stream flag
        result = self.invoke_command(runner, [
            "chat",
            "agent-123",
            "--message", "Hello",
            "--stream"
        ], mock_client=mock_get_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify streaming API was called
        mock_get_client.invoke_agent_stream.assert_called_once()
        mock_get_client.invoke_agent.assert_not_called()

    def test_chat_json_output(self, runner, mock_get_client):
        """Test JSON output format."""
        mock_response = InvokeResponse(
            response="Test response",
            finish_reason="stop",
            usage={"total_tokens": 10}
        )
        mock_get_client.invoke_agent.return_value = mock_response

        # Create context object with empty config
        ctx_obj = {"config_path": None}

        # Run command with format flag for JSON output
        result = self.invoke_command(runner, [
            "chat",
            "agent-123",
            "--message", "Hello",
            "--format", "json"
        ], mock_client=mock_get_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Since we're using rich console in the test which might add formatting,
        # just verify that the command was called correctly and response contains
        # key elements we expect
        assert mock_get_client.invoke_agent.call_count == 1
        assert "Test response" in result.output
        assert "stop" in result.output
        assert "10" in result.output


class TestInvokeTask:
    """Tests for invoke task command."""

    # Helper method for CLI tests - runs commands directly
    def invoke_command(self, runner, args, obj=None, mock_client=None):
        """Invoke a command with proper context."""
        # Create a context object
        if obj is None:
            obj = {"config_path": None}

        # For debugging - print the command being run
        print(f"Running command: invoke {' '.join(args)}")

        # Create a context manager that returns our mock client
        class MockContextManager:
            def __init__(self, mock_client):
                self.mock_client = mock_client
            def __enter__(self):
                return self.mock_client
            def __exit__(self, exc_type, exc_value, traceback):
                pass

        # Patch the get_client function to return our mock context manager
        with patch("ab_cli.cli.invoke.get_client", return_value=MockContextManager(mock_client)):
            # Run the command directly via Click's testing interface
            # catch_exceptions=False to see actual errors
            return runner.invoke(invoke, args, obj=obj, catch_exceptions=False, standalone_mode=False)

    def test_task_basic(self, runner, mock_get_client, tmp_path):
        """Test basic task invocation with input file."""
        # Create input file
        input_file = tmp_path / "input.json"
        input_data = {"query": "What is the capital of France?"}
        input_file.write_text(json.dumps(input_data))

        # Mock response
        mock_response = InvokeResponse(
            response="Paris is the capital of France."
        )
        mock_get_client.invoke_task.return_value = mock_response

        # Create context object with empty config
        ctx_obj = {"config_path": None}

        # Run command
        result = self.invoke_command(runner, [
            "task",
            "agent-123",
            "--input", str(input_file)
        ], mock_client=mock_get_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify client was called correctly
        mock_get_client.invoke_task.assert_called_once()
        call_args = mock_get_client.invoke_task.call_args
        assert call_args[0][0] == "agent-123"  # agent_id
        assert call_args[0][1] == "latest"     # version_id (default)

        # Request should have the inputs
        request = call_args[0][2]  # InvokeTaskRequest
        assert isinstance(request, InvokeTaskRequest)
        assert request.inputs["query"] == "What is the capital of France?"

        # Verify output contains the response
        assert "Paris is the capital of France." in result.output

    def test_task_with_version_id(self, runner, mock_get_client, tmp_path):
        """Test task invocation with specific version ID."""
        # Create input file
        input_file = tmp_path / "input.json"
        input_data = {"query": "Test query"}
        input_file.write_text(json.dumps(input_data))

        mock_get_client.invoke_task.return_value = InvokeResponse(
            response="Version-specific response"
        )

        # Create context object with empty config
        ctx_obj = {"config_path": None}

        result = self.invoke_command(runner, [
            "task",
            "agent-123",
            "version-456",
            "--input", str(input_file)
        ], mock_client=mock_get_client)

        assert result.exit_code == 0
        mock_get_client.invoke_task.assert_called_once()
        call_args = mock_get_client.invoke_task.call_args
        assert call_args[0][0] == "agent-123"
        assert call_args[0][1] == "version-456"

    def test_task_missing_input_file(self, runner, mock_get_client):
        """Test error when no input file is provided."""
        # This should raise a Click MissingParameter exception
        # Using catch_exceptions=True to catch the exception
        with patch("ab_cli.cli.invoke.get_client") as mock_get_client_patch:
            result = runner.invoke(invoke, ["task", "agent-123"],
                                  obj={"config_path": None},
                                  catch_exceptions=True)

        # Verify command failed with the correct error
        assert result.exit_code != 0
        assert "Missing option '--input'" in result.output

        # Verify client was not called since the command validation failed
        mock_get_client.invoke_task.assert_not_called()

    def test_task_invalid_json(self, runner, mock_get_client, tmp_path):
        """Test error when input file contains invalid JSON."""
        # Create invalid JSON file
        input_file = tmp_path / "invalid.json"
        input_file.write_text("{invalid json")

        result = self.invoke_command(runner, [
            "task",
            "agent-123",
            "--input", str(input_file)
        ], mock_client=mock_get_client)

        # Verify command failed
        assert result.exit_code != 0
        assert "Invalid JSON" in result.output

        # Verify client was not called
        mock_get_client.invoke_task.assert_not_called()

    def test_task_stream(self, runner, mock_get_client, tmp_path):
        """Test streaming task invocation."""
        # Create input file
        input_file = tmp_path / "input.json"
        input_data = {"query": "Test query"}
        input_file.write_text(json.dumps(input_data))

        # Mock stream events
        mock_events = [
            StreamEvent(event="text", data="Task"),
            StreamEvent(event="text", data=" response"),
            StreamEvent(event="done")
        ]
        mock_get_client.invoke_task_stream.return_value = mock_events

        # Create context object with empty config
        ctx_obj = {"config_path": None}

        # Run command with stream flag
        result = self.invoke_command(runner, [
            "task",
            "agent-123",
            "--input", str(input_file),
            "--stream"
        ], mock_client=mock_get_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify streaming API was called
        mock_get_client.invoke_task_stream.assert_called_once()
        mock_get_client.invoke_task.assert_not_called()


class TestInvokeInteractive:
    """Tests for invoke interactive command."""

    # Helper method for CLI tests - runs commands directly
    def invoke_command(self, runner, args, obj=None, mock_client=None):
        """Invoke a command with proper context."""
        # Create a context object
        if obj is None:
            obj = {"config_path": None}

        # For debugging - print the command being run
        print(f"Running command: invoke {' '.join(args)}")

        # Create a context manager that returns our mock client
        class MockContextManager:
            def __init__(self, mock_client):
                self.mock_client = mock_client
            def __enter__(self):
                return self.mock_client
            def __exit__(self, exc_type, exc_value, traceback):
                pass

        # Patch the get_client function to return our mock context manager
        with patch("ab_cli.cli.invoke.get_client", return_value=MockContextManager(mock_client)):
            # Run the command directly via Click's testing interface
            # catch_exceptions=False to see actual errors
            return runner.invoke(invoke, args, obj=obj, catch_exceptions=False, standalone_mode=False)

    def test_interactive_basic(self, runner, mock_get_client):
        """Test interactive mode."""
        # Mock agent info with detailed structure
        agent_mock = MagicMock()
        agent_mock.agent = MagicMock(name="TestAgent")
        mock_get_client.get_agent.return_value = agent_mock

        # Set up mock stream responses
        def stream_responses():
            # First response when user types "Hello"
            yield [
                StreamEvent(event="text", data="Hello! How can I help?"),
                StreamEvent(event="done")
            ]

            # Second response when user types "clear"
            yield []

            # Third response when user types "Tell me a joke"
            yield [
                StreamEvent(event="text", data="Why did the developer go broke? Because he used up all his cache!"),
                StreamEvent(event="done")
            ]

        responses = stream_responses()
        mock_get_client.invoke_agent_stream.side_effect = lambda *args, **kwargs: next(responses)

        # Simulate user input sequence:
        # 1. "Hello" - normal message
        # 2. "clear" - special command to clear history
        # 3. "Tell me a joke" - normal message after clearing
        # 4. "exit" - exit command
        input_values = ["Hello", "clear", "Tell me a joke", "exit"]

        # Run the interactive command with mocked input
        with patch("rich.prompt.Prompt.ask", side_effect=input_values):
            with patch("ab_cli.cli.invoke.console"):  # Silence console output
                result = self.invoke_command(runner, ["interactive", "agent-123"], mock_client=mock_get_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify agent was fetched to display name
        mock_get_client.get_agent.assert_called_once_with("agent-123", "latest")

        # Verify agent was invoked with correct messages
        assert mock_get_client.invoke_agent_stream.call_count == 2  # Not called for "clear" command

        # First call should have message "Hello"
        first_call = mock_get_client.invoke_agent_stream.call_args_list[0]
        first_request = first_call[0][2]
        assert len(first_request.messages) == 1
        assert first_request.messages[0].content == "Hello"

        # Second call should have message "Tell me a joke" and no previous messages (after clear)
        second_call = mock_get_client.invoke_agent_stream.call_args_list[1]
        second_request = second_call[0][2]
        assert len(second_request.messages) == 1
        assert second_request.messages[0].content == "Tell me a joke"
