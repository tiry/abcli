"""Tests for invoke module utility functions."""

import json
from unittest.mock import MagicMock, patch

import pytest
import yaml

from ab_cli.cli.invoke import format_response, get_client, output_json, output_yaml
from ab_cli.config.settings import ABSettings
from ab_cli.models.invocation import InvokeResponse


@pytest.fixture
def mock_console():
    """Create a mock console for testing output functions."""
    with patch("ab_cli.cli.invoke.console") as mock:
        yield mock


@pytest.fixture
def mock_error_console():
    """Create a mock error console for testing error output."""
    with patch("ab_cli.cli.invoke.error_console") as mock:
        yield mock


class TestOutputFormatting:
    """Tests for output formatting functions."""

    def test_output_json(self, mock_console):
        """Test JSON output formatting."""
        # Test data
        data = {"key": "value", "number": 123}

        # Call the function
        output_json(data)

        # Verify the console was called correctly
        mock_console.print_json.assert_called_once()
        args = mock_console.print_json.call_args[0][0]

        # Deserialize the JSON to verify structure
        parsed = json.loads(args)
        assert parsed["key"] == "value"
        assert parsed["number"] == 123

    def test_output_yaml(self, mock_console):
        """Test YAML output formatting."""
        # Test data
        data = {"key": "value", "number": 123}

        # Call the function
        output_yaml(data)

        # Verify the console was called correctly
        mock_console.print.assert_called_once()
        args = mock_console.print.call_args[0][0]

        # Verify it's valid YAML and contains our data
        parsed = yaml.safe_load(args)
        assert parsed["key"] == "value"
        assert parsed["number"] == 123

    def test_format_response_table_format(self, mock_console):
        """Test formatting response in table (default) format."""
        # Create test response
        response = InvokeResponse(
            response="Test response content",
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )

        # Call the format_response function
        format_response(response, output_format="table")

        # Verify console was called with the right content
        # Should have at least 4 print calls:
        # 1. Empty line
        # 2. Response header
        # 3. Response content
        # 4. Empty line
        # 5. Usage info
        # 6. Finish reason
        assert mock_console.print.call_count >= 4

        # Check the response content was printed
        mock_console.print.assert_any_call("Test response content")

        # Check usage was printed
        usage_call = False
        for call in mock_console.print.call_args_list:
            args = call[0]
            if args and isinstance(args[0], str) and "token" in args[0].lower():
                usage_call = True
                break
        assert usage_call, "Usage information was not printed"

    def test_format_response_json_format(self, mock_console):
        """Test formatting response in JSON format."""
        # Create test response
        response = InvokeResponse(
            response="Test JSON response",
            finish_reason="stop"
        )

        # Call the format_response function with JSON format
        with patch("ab_cli.cli.invoke.output_json") as mock_output_json:
            format_response(response, output_format="json")

            # Verify output_json was called with response data
            mock_output_json.assert_called_once()
            called_with = mock_output_json.call_args[0][0]
            assert called_with["response"] == "Test JSON response"
            assert called_with["finish_reason"] == "stop"

    def test_format_response_yaml_format(self, mock_console):
        """Test formatting response in YAML format."""
        # Create test response
        response = InvokeResponse(
            response="Test YAML response",
            finish_reason="stop"
        )

        # Call the format_response function with YAML format
        with patch("ab_cli.cli.invoke.output_yaml") as mock_output_yaml:
            format_response(response, output_format="yaml")

            # Verify output_yaml was called with response data
            mock_output_yaml.assert_called_once()
            called_with = mock_output_yaml.call_args[0][0]
            assert called_with["response"] == "Test YAML response"
            assert called_with["finish_reason"] == "stop"

    def test_format_response_verbose(self, mock_console):
        """Test verbose output with raw API response."""
        # Create test response
        response = InvokeResponse(
            response="Test verbose response",
            finish_reason="stop"
        )

        # Call the format_response function with verbose flag
        format_response(response, output_format="table", verbose=True)

        # Verify that the raw API response section is printed
        raw_response_header_printed = False
        for call in mock_console.print.call_args_list:
            args = call[0]
            if args and isinstance(args[0], str) and "raw api response" in args[0].lower():
                raw_response_header_printed = True
                break
        assert raw_response_header_printed, "Raw API Response header was not printed in verbose mode"

        # Also verify that json.dumps was called
        assert mock_console.print_json.call_count >= 1


class TestGetClient:
    """Tests for get_client function."""

    def test_get_client_with_config_path(self):
        """Test get_client with specific config path."""
        # Setup mock dependencies
        mock_settings = MagicMock(spec=ABSettings)
        mock_client = MagicMock()

        with patch("ab_cli.cli.invoke.load_config", return_value=mock_settings) as mock_load_config:
            with patch("ab_cli.cli.invoke.AgentBuilderClient", return_value=mock_client) as mock_client_class:
                # Call get_client with a config path
                client = get_client("/path/to/config.yaml")

                # Verify dependencies were called correctly
                mock_load_config.assert_called_once_with("/path/to/config.yaml")
                mock_client_class.assert_called_once_with(mock_settings)
                assert client == mock_client

    def test_get_client_without_config_path(self):
        """Test get_client without config path (using find_config_file)."""
        # Setup mock dependencies
        mock_config_path = "/found/config/path.yaml"
        mock_settings = MagicMock(spec=ABSettings)
        mock_client = MagicMock()

        with patch("ab_cli.cli.invoke.find_config_file", return_value=mock_config_path) as mock_find_config:
            with patch("ab_cli.cli.invoke.load_config", return_value=mock_settings) as mock_load_config:
                with patch("ab_cli.cli.invoke.AgentBuilderClient", return_value=mock_client) as mock_client_class:
                    # Call get_client without a config path
                    client = get_client()

                    # Verify dependencies were called correctly
                    mock_find_config.assert_called_once()
                    mock_load_config.assert_called_once_with(mock_config_path)
                    mock_client_class.assert_called_once_with(mock_settings)
                    assert client == mock_client
