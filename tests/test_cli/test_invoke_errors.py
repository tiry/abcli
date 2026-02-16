"""Tests for error handling in invoke module."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from ab_cli.api.exceptions import APIError, NotFoundError
from ab_cli.cli.invoke import invoke
from ab_cli.models.invocation import StreamEvent


@pytest.fixture
def mock_client():
    """Create mock AgentBuilderClient that raises specific errors."""
    mock = MagicMock()
    return mock


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestInvokeErrors:
    """Tests for error handling in invoke commands."""

    # Helper method for CLI tests - runs commands directly
    def invoke_command(self, runner, args, obj=None, mock_client=None, exception=None):
        """Invoke a command with proper context, optionally raising an exception."""
        # Create a context object
        if obj is None:
            obj = {"config_path": None}

        # Create a context manager that returns our mock client
        class MockContextManager:
            def __init__(self, mock_client, exception=None):
                self.mock_client = mock_client
                self.exception = exception
            def __enter__(self):
                if self.exception:
                    raise self.exception
                return self.mock_client
            def __exit__(self, exc_type, exc_value, traceback):
                pass

        # Patch the get_client function to return our mock context manager
        with patch("ab_cli.cli.invoke.get_client",
                  return_value=MockContextManager(mock_client, exception)):
            # Run the command directly via Click's testing interface
            return runner.invoke(invoke, args, obj=obj, catch_exceptions=False, standalone_mode=False)

    def test_chat_agent_not_found(self, runner, mock_client):
        """Test chat command with agent not found error."""
        # Setup exception
        exception = NotFoundError("Agent not found", "agent-123")

        # Run command
        result = self.invoke_command(
            runner,
            ["chat", "agent-123", "--message", "Hello"],
            mock_client=mock_client,
            exception=exception
        )

        # Verify command failed with the correct error message
        assert result.exit_code != 0
        assert "Agent not found" in result.output
        assert "agent-123" in result.output

    def test_chat_api_error(self, runner, mock_client):
        """Test chat command with generic API error."""
        # Set mock to raise APIError
        mock_client.invoke_agent.side_effect = APIError("API request failed: Rate limit exceeded")

        # Run command
        result = self.invoke_command(
            runner,
            ["chat", "agent-123", "--message", "Hello"],
            mock_client=mock_client
        )

        # Verify command failed with the correct error message
        assert result.exit_code != 0
        assert "Error" in result.output
        assert "Rate limit exceeded" in result.output

    def test_task_agent_not_found(self, runner, mock_client, tmp_path):
        """Test task command with agent not found error."""
        # Setup exception
        exception = NotFoundError("Agent not found", "agent-123")

        # Run command with inline task data
        result = self.invoke_command(
            runner,
            ["task", "agent-123", "--task", '{"query": "test"}'],
            mock_client=mock_client,
            exception=exception
        )

        # Verify command failed with the correct error message
        assert result.exit_code != 0
        assert "Agent not found" in result.output
        assert "agent-123" in result.output

    def test_task_api_error(self, runner, mock_client, tmp_path):
        """Test task command with generic API error."""
        # Set mock to raise APIError
        mock_client.invoke_task.side_effect = APIError("API request failed: Invalid input format")

        # Run command with inline task data
        result = self.invoke_command(
            runner,
            ["task", "agent-123", "--task", '{"query": "test"}'],
            mock_client=mock_client
        )

        # Verify command failed with the correct error message
        assert result.exit_code != 0
        assert "Error" in result.output
        assert "Invalid input format" in result.output

    def test_chat_stream_error_event(self, runner, mock_client):
        """Test chat stream with error event."""
        # Mock stream events with an error event
        mock_client.invoke_agent_stream.return_value = [
            StreamEvent(event="text", data="Starting response"),
            StreamEvent(event="error", data="Stream processing error")
        ]

        # Run command with stream option
        with patch("ab_cli.cli.invoke.Live") as mock_live:
            # Mock Live context manager
            mock_live_instance = MagicMock()
            mock_live.return_value.__enter__.return_value = mock_live_instance

            # Run command with stream
            result = self.invoke_command(
                runner,
                ["chat", "agent-123", "--message", "Hello", "--stream"],
                mock_client=mock_client
            )

            # Verify command failed with the correct error message
            assert result.exit_code != 0
            assert "Error" in result.output
            assert "Stream processing error" in result.output

    def test_chat_keyboard_interrupt(self, runner, mock_client):
        """Test handling keyboard interrupt during streaming."""
        # Mock invoke_agent_stream to raise KeyboardInterrupt
        mock_client.invoke_agent_stream.side_effect = KeyboardInterrupt()

        # Run command with stream option
        with patch("ab_cli.cli.invoke.Live") as mock_live:
            # Mock Live context manager
            mock_live_instance = MagicMock()
            mock_live.return_value.__enter__.return_value = mock_live_instance

            # Run command with stream
            result = self.invoke_command(
                runner,
                ["chat", "agent-123", "--message", "Hello", "--stream"],
                mock_client=mock_client
            )

            # Verify message about interruption
            assert "interrupted" in result.output.lower()

    def test_task_stream_error_event(self, runner, mock_client, tmp_path):
        """Test task stream with error event."""
        # Mock stream events with an error event
        mock_client.invoke_task_stream.return_value = [
            StreamEvent(event="text", data="Starting task"),
            StreamEvent(event="error", data="Task processing error")
        ]

        # Run command with stream option
        with patch("ab_cli.cli.invoke.Live") as mock_live:
            # Mock Live context manager
            mock_live_instance = MagicMock()
            mock_live.return_value.__enter__.return_value = mock_live_instance

            # Run command with stream and inline task data
            result = self.invoke_command(
                runner,
                ["task", "agent-123", "--task", '{"query": "test"}', "--stream"],
                mock_client=mock_client
            )

            # Verify command failed with the correct error message
            assert result.exit_code != 0
            assert "Error" in result.output
            assert "Task processing error" in result.output

    def test_chat_message_file_error(self, runner, mock_client, tmp_path):
        """Test error when message file cannot be read."""
        # Create a file path that does exist but with permissions that cause an error
        test_file = tmp_path / "test_file.txt"
        test_file.write_text("Test content")

        # Mock the open function to raise an exception when trying to read this file
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = OSError("Permission denied")

            # Run command with the file that will trigger an error
            result = self.invoke_command(
                runner,
                ["chat", "agent-123", "--message-file", str(test_file)],
                mock_client=mock_client
            )

            # Verify command failed with file error message
            assert result.exit_code != 0
            assert "Error reading file" in result.output

    def test_no_message_provided(self, runner, mock_client):
        """Test error when no message is provided to chat command."""
        # Run command without message or message-file
        result = self.invoke_command(
            runner,
            ["chat", "agent-123"],
            mock_client=mock_client
        )

        # Verify command failed with the correct error message
        assert result.exit_code != 0
        assert "No message provided" in result.output
