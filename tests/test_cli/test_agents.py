"""Tests for agent CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from ab_cli.cli.agents import (
    agents,
)
from ab_cli.models.agent import (
    Agent,
    AgentCreate,
    AgentList,
    AgentType,
    AgentTypeList,
    AgentUpdate,
    AgentVersion,
    Pagination,
    VersionConfig,
)


@pytest.fixture
def mock_client():
    """Create mock AgentBuilderClient."""
    mock = MagicMock()

    # Mock responses
    mock.list_agents.return_value = AgentList(
        agents=[
            Agent(id="00000000-0000-4000-a000-000000000001", name="Test Agent", type="tool",
                  description="Test agent", status="CREATED",
                  created_at="2026-02-10T10:00:00Z", created_by="test-user",
                  modified_at="2026-02-10T10:00:00Z"),
            Agent(id="00000000-0000-4000-a000-000000000002", name="Another Agent", type="rag",
                  description="Another test agent", status="CREATED",
                  created_at="2026-02-10T11:00:00Z", created_by="test-user",
                  modified_at="2026-02-10T11:00:00Z")
        ],
        pagination=Pagination(limit=50, offset=0, total_items=2)
    )

    mock.get_agent.return_value = AgentVersion(
        agent=Agent(id="00000000-0000-4000-a000-000000000001", name="Test Agent", type="tool",
                   description="Test agent", status="CREATED",
                   created_at="2026-02-10T10:00:00Z", created_by="test-user",
                   modified_at="2026-02-10T10:00:00Z"),
        version=VersionConfig(id="00000000-0000-4000-a000-000000000101", number=1, version_label="v1.0",
                       notes="Initial version",
                       created_at="2026-02-10T10:00:00Z", created_by="test-user",
                       config={"systemPrompt": "You are an AI assistant."})
    )

    mock.create_agent.return_value = AgentVersion(
        agent=Agent(id="00000000-0000-4000-a000-000000000001", name="New Agent", type="tool",
                   description="New agent", status="CREATED",
                   created_at="2026-02-10T12:00:00Z", created_by="test-user",
                   modified_at="2026-02-10T12:00:00Z"),
        version=VersionConfig(id="00000000-0000-4000-a000-000000000101", number=1, version_label="v1.0",
                       notes="Initial version",
                       created_at="2026-02-10T12:00:00Z", created_by="test-user",
                       config={"systemPrompt": "You are an AI assistant."})
    )

    mock.update_agent.return_value = AgentVersion(
        agent=Agent(id="00000000-0000-4000-a000-000000000001", name="Test Agent", type="tool",
                   description="Test agent", status="CREATED",
                   created_at="2026-02-10T10:00:00Z", created_by="test-user",
                   modified_at="2026-02-10T10:00:00Z"),
        version=VersionConfig(id="00000000-0000-4000-a000-000000000102", number=2, version_label="v2.0",
                       notes="Updated version",
                       created_at="2026-02-10T13:00:00Z", created_by="test-user",
                       config={"systemPrompt": "You are an updated AI assistant."})
    )

    mock.patch_agent.return_value = Agent(
        id="00000000-0000-4000-a000-000000000001", name="Updated Name", type="tool",
        description="Updated description", status="CREATED",
        created_at="2026-02-10T10:00:00Z", created_by="test-user",
        modified_at="2026-02-10T14:00:00Z"
    )

    mock.list_agent_types.return_value = AgentTypeList(
        agent_types=[
            AgentType(type="tool", description="Tool agent description"),
            AgentType(type="rag", description="RAG agent description"),
            AgentType(type="task", description="Task agent description")
        ],
        pagination=Pagination(limit=50, offset=0, total_items=3)
    )

    return mock


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestListAgents:
    """Tests for list_agents command."""

    def test_list_agents_basic(self, runner, mock_client):
        """Test basic agent listing."""
        # Create context object with empty config
        ctx_obj = {"config_path": None}

        # Mock get_client to return our mock
        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, ["list"], obj=ctx_obj)

        # Verify command succeeded
        assert result.exit_code == 0

        # Verify client was called correctly
        mock_client.list_agents.assert_called_once_with(limit=50, offset=0)

        # Verify output contains agent information
        assert "Test" in result.output
        assert "Agent" in result.output
        assert "Another" in result.output
        assert "tool" in result.output
        assert "rag" in result.output

    def test_list_agents_with_pagination(self, runner, mock_client):
        """Test listing agents with pagination."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, ["list", "--limit", "10", "--offset", "5"], obj=ctx_obj)

        assert result.exit_code == 0
        mock_client.list_agents.assert_called_once_with(limit=10, offset=5)

    def test_list_agents_json_format(self, runner, mock_client):
        """Test listing agents with JSON output format."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, ["list", "--format", "json"], obj=ctx_obj)

        assert result.exit_code == 0
        assert "agents" in result.output
        assert "00000000-0000-4000-a000-000000000001" in result.output
        assert "00000000-0000-4000-a000-000000000002" in result.output

    def test_list_agents_yaml_format(self, runner, mock_client):
        """Test listing agents with YAML output format."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, ["list", "--format", "yaml"], obj=ctx_obj)

        assert result.exit_code == 0
        assert "agents:" in result.output
        assert "name: Test Agent" in result.output
        assert "name: Another Agent" in result.output


class TestGetAgent:
    """Tests for get_agent command."""

    def test_get_agent_basic(self, runner, mock_client):
        """Test basic agent retrieval."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, ["get", "00000000-0000-4000-a000-000000000001"], obj=ctx_obj)

        assert result.exit_code == 0
        mock_client.get_agent.assert_called_once_with("00000000-0000-4000-a000-000000000001")

        assert "Test Agent" in result.output
        assert "00000000-0000-4000-a000-000000000001" in result.output
        assert "tool" in result.output
        assert "v1.0" in result.output
        assert "Initial version" in result.output
        assert "systemPrompt" in result.output

    def test_get_agent_json_format(self, runner, mock_client):
        """Test getting agent with JSON output format."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, ["get", "00000000-0000-4000-a000-000000000001", "--format", "json"], obj=ctx_obj)

        assert result.exit_code == 0
        assert "agent" in result.output
        assert "version" in result.output
        # Just check for important fields in the output instead of hardcoded value
        assert "id" in result.output
        assert "00000000-0000-4000-a000-000000000101" in result.output
        assert "00000000-0000-4000-a000-000000000101" in result.output
        assert "v1.0" in result.output

    def test_get_agent_not_found(self, runner, mock_client):
        """Test getting a non-existent agent."""
        ctx_obj = {"config_path": None}

        # Override mock to raise NotFoundError
        from ab_cli.api.exceptions import NotFoundError
        mock_client.get_agent.side_effect = NotFoundError("Agent not found", "nonexistent-agent")

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, ["get", "nonexistent-agent"], obj=ctx_obj)

        assert result.exit_code != 0
        assert "Agent not found" in result.output


class TestCreateAgent:
    """Tests for create_agent command."""

    def test_create_agent_basic(self, runner, mock_client, tmp_path):
        """Test basic agent creation."""
        ctx_obj = {"config_path": None}

        # Create temporary config file
        config_file = tmp_path / "test_config.json"
        config = {"systemPrompt": "You are an AI assistant."}
        config_file.write_text(json.dumps(config))

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, [
                "create",
                "--name", "New Agent",
                "--description", "New agent",
                "--type", "tool",
                "--config", str(config_file),
                "--version-label", "v1.0",
                "--notes", "Initial version"
            ], obj=ctx_obj)

        assert result.exit_code == 0

        # Verify client was called with correct parameters
        mock_client.create_agent.assert_called_once()
        args, _ = mock_client.create_agent.call_args
        agent_create = args[0]
        assert isinstance(agent_create, AgentCreate)
        assert agent_create.name == "New Agent"
        assert agent_create.description == "New agent"
        assert agent_create.agent_type == "tool"
        assert agent_create.config == config
        assert agent_create.version_label == "v1.0"
        assert agent_create.notes == "Initial version"

        # Verify output contains success message
        assert "Agent created successfully" in result.output

    def test_create_agent_invalid_config(self, runner, mock_client, tmp_path):
        """Test agent creation with invalid config file."""
        ctx_obj = {"config_path": None}

        # Create invalid JSON file
        config_file = tmp_path / "invalid_config.json"
        config_file.write_text("{invalid json")

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, [
                "create",
                "--name", "New Agent",
                "--description", "New agent",
                "--type", "tool",
                "--config", str(config_file)
            ], obj=ctx_obj)

        assert result.exit_code != 0
        assert "Invalid JSON" in result.output


class TestUpdateAgent:
    """Tests for update_agent command."""

    def test_update_agent_basic(self, runner, mock_client, tmp_path):
        """Test basic agent update."""
        ctx_obj = {"config_path": None}

        # Create temporary config file
        config_file = tmp_path / "update_config.json"
        config = {"systemPrompt": "You are an updated AI assistant."}
        config_file.write_text(json.dumps(config))

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, [
                "update",
                "00000000-0000-4000-a000-000000000001",
                "--config", str(config_file),
                "--version-label", "v2.0",
                "--notes", "Updated version"
            ], obj=ctx_obj)

        assert result.exit_code == 0

        # Verify client was called with correct parameters
        mock_client.update_agent.assert_called_once()
        args, _ = mock_client.update_agent.call_args
        assert args[0] == "00000000-0000-4000-a000-000000000001"
        agent_update = args[1]
        assert isinstance(agent_update, AgentUpdate)
        assert agent_update.config == config
        assert agent_update.version_label == "v2.0"
        assert agent_update.notes == "Updated version"

        # Verify output contains success message
        assert "Agent updated successfully" in result.output
        assert "New Version" in result.output

    def test_update_agent_with_dict_response(self, runner, mock_client, tmp_path):
        """Test agent update handling dict response."""
        ctx_obj = {"config_path": None}

        # Mock client to return a dict instead of an AgentVersion
        mock_client.update_agent.return_value = {
            "id": "version-456",
            "versionNumber": 2,
            "versionLabel": "v2.0"
        }

        # Create temporary config file
        config_file = tmp_path / "update_config.json"
        config = {"systemPrompt": "You are an updated AI assistant."}
        config_file.write_text(json.dumps(config))

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, [
                "update",
                "00000000-0000-4000-a000-000000000001",
                "--config", str(config_file)
            ], obj=ctx_obj)

        assert result.exit_code == 0
        assert "Agent updated successfully" in result.output
        assert "New Version Created" in result.output


class TestPatchAgent:
    """Tests for patch_agent command."""

    def test_patch_agent_basic(self, runner, mock_client):
        """Test basic agent patching."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, [
                "patch",
                "00000000-0000-4000-a000-000000000001",
                "--name", "Updated Name",
                "--description", "Updated description"
            ], obj=ctx_obj)

        assert result.exit_code == 0

        # Verify client was called with correct parameters
        mock_client.patch_agent.assert_called_once()
        args, _ = mock_client.patch_agent.call_args
        assert args[0] == "00000000-0000-4000-a000-000000000001"
        agent_patch = args[1]
        assert agent_patch.name == "Updated Name"
        assert agent_patch.description == "Updated description"

        # Verify output contains success message
        assert "Agent patched successfully" in result.output
        assert "Updated Name" in result.output
        assert "Updated description" in result.output

    def test_patch_agent_no_changes(self, runner, mock_client):
        """Test patch agent with no changes specified."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, [
                "patch",
                "00000000-0000-4000-a000-000000000001"
            ], obj=ctx_obj)

        assert "No changes specified" in result.output
        mock_client.patch_agent.assert_not_called()


class TestDeleteAgent:
    """Tests for delete_agent command."""

    def test_delete_agent_with_confirmation(self, runner, mock_client):
        """Test deleting agent with confirmation."""
        ctx_obj = {"config_path": None}

        # Mock click.confirm to return True
        with patch("click.confirm", return_value=True):
            with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
                result = runner.invoke(agents, [
                "delete",
                "00000000-0000-4000-a000-000000000001"
                ], obj=ctx_obj)

        assert result.exit_code == 0
        mock_client.delete_agent.assert_called_once_with("00000000-0000-4000-a000-000000000001")
        assert "Agent deleted" in result.output

    def test_delete_agent_with_yes_flag(self, runner, mock_client):
        """Test deleting agent with --yes flag."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, [
                "delete",
                "00000000-0000-4000-a000-000000000001",
                "--yes"
            ], obj=ctx_obj)

        assert result.exit_code == 0
        mock_client.delete_agent.assert_called_once_with("00000000-0000-4000-a000-000000000001")
        assert "Agent deleted" in result.output

    def test_delete_agent_cancelled(self, runner, mock_client):
        """Test cancelling agent deletion."""
        ctx_obj = {"config_path": None}

        # Mock click.confirm to return False
        with patch("click.confirm", return_value=False):
            with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
                result = runner.invoke(agents, [
                    "delete",
                    "00000000-0000-4000-a000-000000000001"
                ], obj=ctx_obj)

        assert "Cancelled" in result.output
        mock_client.delete_agent.assert_not_called()


class TestListAgentTypes:
    """Tests for list_agent_types command."""

    def test_list_agent_types_basic(self, runner, mock_client):
        """Test basic agent types listing."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, ["types"], obj=ctx_obj)

        assert result.exit_code == 0
        mock_client.list_agent_types.assert_called_once()

        # Verify output contains agent types
        assert "tool" in result.output
        assert "rag" in result.output
        assert "task" in result.output
        assert "Tool agent description" in result.output

    def test_list_agent_types_json_format(self, runner, mock_client):
        """Test listing agent types with JSON output."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.agents.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(agents, ["types", "--format", "json"], obj=ctx_obj)

        assert result.exit_code == 0
        assert "agentTypes" in result.output
        assert "tool" in result.output
        assert "rag" in result.output
        assert "task" in result.output
