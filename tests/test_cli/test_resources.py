"""Tests for resource CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from ab_cli.cli.resources import resources
from ab_cli.models.agent import Pagination
from ab_cli.models.resources import (
    DeprecationStatus,
    GuardrailList,
    GuardrailModel,
    LLMModel,
    LLMModelList,
)


@pytest.fixture
def mock_client():
    """Create mock AgentBuilderClient."""
    mock = MagicMock()

    # Mock responses for list_models
    mock.list_models.return_value = LLMModelList(
        models=[
            LLMModel(
                id="model1",
                name="Test Model 1",
                description="Test description",
                badge="Test",
                metadata="metadata",
                agent_types=["tool", "rag"],
                capabilities={"multimodal": True, "streaming": True},
                regions=["us-east", "eu-west"],
                deprecation_status=DeprecationStatus(deprecated=False)
            ),
            LLMModel(
                id="model2",
                name="Test Model 2",
                description="Another model",
                badge="Test2",
                metadata="metadata2",
                agent_types=["task"],
                capabilities={"multimodal": False, "streaming": False},
                regions=["us-east"],
                deprecation_status=DeprecationStatus(deprecated=True, deprecation_date="2025-12-31")
            )
        ],
        pagination=Pagination(limit=50, offset=0, total_items=2)
    )

    # Mock responses for list_guardrails
    mock.list_guardrails.return_value = GuardrailList(
        guardrails=[
            GuardrailModel(name="guardrail1", description="Test guardrail 1"),
            GuardrailModel(name="guardrail2", description="Test guardrail 2")
        ],
        pagination=Pagination(limit=50, offset=0, total_items=2)
    )

    return mock


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestListModels:
    """Tests for list_models command."""

    # Helper method for CLI tests - runs commands directly
    def invoke_command(self, runner, args, obj=None, mock_client=None):
        """Invoke a command with proper context."""
        # Create a context object
        if obj is None:
            obj = {"config_path": None}

        # For debugging - print the command being run
        print(f"Running command: resources {' '.join(args)}")

        # Create a context manager that returns our mock client
        class MockContextManager:
            def __init__(self, mock_client):
                self.mock_client = mock_client
            def __enter__(self):
                return self.mock_client
            def __exit__(self, exc_type, exc_value, traceback):
                pass

        # Patch the get_client function to return our mock context manager
        with patch("ab_cli.cli.resources.get_client", return_value=MockContextManager(mock_client)):
            # Run the command directly via Click's testing interface
            # catch_exceptions=False to see actual errors
            return runner.invoke(resources, args, obj=obj, catch_exceptions=False, standalone_mode=False)

    def test_list_models_basic(self, runner, mock_client):
        """Test basic model listing."""
        result = self.invoke_command(runner, ["models"], mock_client=mock_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify client was called correctly
        mock_client.list_models.assert_called_once_with(agent_type=None, limit=50, offset=0)

        # Verify output contains model names
        assert "Test Model 1" in result.output
        assert "Test Model 2" in result.output
        assert "tool, rag" in result.output  # Agent types for model 1 (note the space after comma)

    def test_list_models_with_agent_type(self, runner, mock_client):
        """Test listing models filtered by agent type."""
        result = self.invoke_command(runner, ["models", "--agent-type", "rag"], mock_client=mock_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify client was called correctly with agent_type parameter
        mock_client.list_models.assert_called_once_with(agent_type="rag", limit=50, offset=0)

    def test_list_models_with_pagination(self, runner, mock_client):
        """Test listing models with pagination."""
        result = self.invoke_command(runner, ["models", "--limit", "10", "--offset", "5"], mock_client=mock_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify client was called correctly with pagination parameters
        mock_client.list_models.assert_called_once_with(agent_type=None, limit=10, offset=5)

    def test_list_models_json_output(self, runner, mock_client):
        """Test listing models with JSON output format."""
        result = self.invoke_command(runner, ["models", "--format", "json"], mock_client=mock_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify JSON format in output (looking for specific JSON elements)
        assert '"models":' in result.output
        assert '"id"' in result.output
        assert '"name"' in result.output
        assert '"agentTypes"' in result.output

    def test_list_models_yaml_output(self, runner, mock_client):
        """Test listing models with YAML output format."""
        result = self.invoke_command(runner, ["models", "--format", "yaml"], mock_client=mock_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify YAML format in output (looking for YAML syntax elements)
        assert "models:" in result.output
        assert "id: model" in result.output  # YAML format has 'id: model1'
        assert "name: Test Model" in result.output
        assert "agentTypes:" in result.output  # Uses camelCase in output


class TestListGuardrails:
    """Tests for list_guardrails command."""

    # Helper method for CLI tests - runs commands directly
    def invoke_command(self, runner, args, obj=None, mock_client=None):
        """Invoke a command with proper context."""
        # Create a context object
        if obj is None:
            obj = {"config_path": None}

        # For debugging - print the command being run
        print(f"Running command: resources {' '.join(args)}")

        # Create a context manager that returns our mock client
        class MockContextManager:
            def __init__(self, mock_client):
                self.mock_client = mock_client
            def __enter__(self):
                return self.mock_client
            def __exit__(self, exc_type, exc_value, traceback):
                pass

        # Patch the get_client function to return our mock context manager
        with patch("ab_cli.cli.resources.get_client", return_value=MockContextManager(mock_client)):
            # Run the command directly via Click's testing interface
            # catch_exceptions=False to see actual errors
            return runner.invoke(resources, args, obj=obj, catch_exceptions=False, standalone_mode=False)

    def test_list_guardrails_basic(self, runner, mock_client):
        """Test basic guardrails listing."""
        result = self.invoke_command(runner, ["guardrails"], mock_client=mock_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify client was called correctly
        mock_client.list_guardrails.assert_called_once_with(limit=50, offset=0)

        # Verify output contains guardrail names and descriptions
        assert "guardrail1" in result.output
        assert "Test guardrail 1" in result.output
        assert "guardrail2" in result.output
        assert "Test guardrail 2" in result.output

    def test_list_guardrails_with_pagination(self, runner, mock_client):
        """Test listing guardrails with pagination."""
        result = self.invoke_command(runner, ["guardrails", "--limit", "10", "--offset", "5"], mock_client=mock_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify client was called correctly with pagination parameters
        mock_client.list_guardrails.assert_called_once_with(limit=10, offset=5)

    def test_list_guardrails_json_output(self, runner, mock_client):
        """Test listing guardrails with JSON output format."""
        result = self.invoke_command(runner, ["guardrails", "--format", "json"], mock_client=mock_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify JSON format in output (looking for specific JSON elements)
        assert '"guardrails":' in result.output
        assert '"name"' in result.output
        assert '"description"' in result.output

    def test_list_guardrails_yaml_output(self, runner, mock_client):
        """Test listing guardrails with YAML output format."""
        result = self.invoke_command(runner, ["guardrails", "--format", "yaml"], mock_client=mock_client)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify YAML format in output (looking for YAML syntax elements)
        assert "guardrails:" in result.output
        assert "name: guardrail" in result.output  # YAML format has 'name: guardrail1'
        assert "description: Test guardrail" in result.output
