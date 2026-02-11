"""Tests for version CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from ab_cli.cli.versions import versions
from ab_cli.models.agent import (
    Agent,
    AgentVersion,
    Pagination,
    Version,
    VersionConfig,
    VersionCreate,
    VersionList,
)


@pytest.fixture
def mock_client():
    """Create mock AgentBuilderClient."""
    mock = MagicMock()

    # Mock responses for list_versions
    mock.list_versions.return_value = VersionList(
        agent=Agent(
            id="00000000-0000-4000-a000-000000000001",
            name="Test Agent",
            type="tool",
            description="Test agent",
            status="CREATED",
            created_at="2026-02-10T10:00:00Z",
            created_by="test-user",
            modified_at="2026-02-10T10:00:00Z"
        ),
        versions=[
            Version(
                id="00000000-0000-4000-a000-000000000101",
                number=1,
                version_label="v1.0",
                notes="Initial version",
                created_at="2026-02-10T10:00:00Z",
                created_by="user1",
                config={"systemPrompt": "You are an AI assistant."}
            ),
            Version(
                id="00000000-0000-4000-a000-000000000102",
                number=2,
                version_label="v2.0",
                notes="Updated version",
                created_at="2026-02-10T11:00:00Z",
                created_by="user2",
                config={"systemPrompt": "You are an updated AI assistant."}
            )
        ],
        pagination=Pagination(limit=50, offset=0, total_items=2)
    )

    # Mock response for get_version
    mock.get_version.return_value = AgentVersion(
        agent=Agent(
            id="00000000-0000-4000-a000-000000000001",
            name="Test Agent",
            type="tool",
            description="Test agent",
            status="CREATED",
            created_at="2026-02-10T10:00:00Z",
            created_by="test-user",
            modified_at="2026-02-10T10:00:00Z"
        ),
        version=VersionConfig(
            id="00000000-0000-4000-a000-000000000101",
            number=1,
            version_label="v1.0",
            notes="Initial version",
            created_at="2026-02-10T10:00:00Z",
            created_by="user1",
            config={"systemPrompt": "You are an AI assistant."}
        )
    )

    # Mock response for create_version
    mock.create_version.return_value = AgentVersion(
        agent=Agent(
            id="00000000-0000-4000-a000-000000000001",
            name="Test Agent",
            type="tool",
            description="Test agent",
            status="CREATED",
            created_at="2026-02-10T10:00:00Z",
            created_by="test-user",
            modified_at="2026-02-10T10:00:00Z"
        ),
        version=VersionConfig(
            id="00000000-0000-4000-a000-000000000103",
            number=3,
            version_label="v3.0",
            notes="New version",
            created_at="2026-02-10T12:00:00Z",
            created_by="user3",
            config={"systemPrompt": "You are a new AI assistant."}
        )
    )

    return mock


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestListVersions:
    """Tests for list_versions command."""

    def test_list_versions_basic(self, runner, mock_client):
        """Test basic version listing."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.versions.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(versions, ["list", "00000000-0000-4000-a000-000000000001"], obj=ctx_obj)

        assert result.exit_code == 0
        mock_client.list_versions.assert_called_once_with("00000000-0000-4000-a000-000000000001", limit=50, offset=0)

        # Check output contains version information
        assert "Test Agent" in result.output
        assert "00000000-0000-4000-a000-000000000101" in result.output or "v1.0" in result.output
        assert "00000000-0000-4000-a000-000000000102" in result.output or "v2.0" in result.output
        assert "v1.0" in result.output
        assert "v2.0" in result.output
        # The "Initial version" text may be truncated in the output table, so we don't assert it

    def test_list_versions_with_pagination(self, runner, mock_client):
        """Test version listing with pagination."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.versions.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(versions, [
                "list",
                "00000000-0000-4000-a000-000000000001",
                "--limit", "10",
                "--offset", "5"
            ], obj=ctx_obj)

        assert result.exit_code == 0
        mock_client.list_versions.assert_called_once_with("00000000-0000-4000-a000-000000000001", limit=10, offset=5)

    def test_list_versions_json_format(self, runner, mock_client):
        """Test version listing with JSON output format."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.versions.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(versions, [
                "list",
                "00000000-0000-4000-a000-000000000001",
                "--format", "json"
            ], obj=ctx_obj)

        assert result.exit_code == 0
        assert "agent" in result.output
        assert "versions" in result.output

    def test_list_versions_yaml_format(self, runner, mock_client):
        """Test version listing with YAML output format."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.versions.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(versions, [
                "list",
                "00000000-0000-4000-a000-000000000001",
                "--format", "yaml"
            ], obj=ctx_obj)

        assert result.exit_code == 0
        assert "agent:" in result.output
        assert "versions:" in result.output
        assert "versionLabel: v1.0" in result.output

    def test_list_versions_not_found(self, runner, mock_client):
        """Test listing versions for a non-existent agent."""
        ctx_obj = {"config_path": None}

        # Override mock to raise NotFoundError
        from ab_cli.api.exceptions import NotFoundError
        mock_client.list_versions.side_effect = NotFoundError("Agent not found", "nonexistent-agent")

        with patch("ab_cli.cli.versions.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(versions, ["list", "nonexistent-agent"], obj=ctx_obj)

        assert result.exit_code != 0
        assert "Agent not found" in result.output


class TestGetVersion:
    """Tests for get_version command."""

    def test_get_version_basic(self, runner, mock_client):
        """Test basic version retrieval."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.versions.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(versions, ["get", "00000000-0000-4000-a000-000000000001", "00000000-0000-4000-a000-000000000101"], obj=ctx_obj)

        assert result.exit_code == 0
        mock_client.get_version.assert_called_once_with("00000000-0000-4000-a000-000000000001", "00000000-0000-4000-a000-000000000101")

        # Check output contains version information
        assert "Test Agent" in result.output
        assert "Version 1" in result.output
        assert "v1.0" in result.output
        assert "Initial version" in result.output
        assert "systemPrompt" in result.output

    def test_get_version_json_format(self, runner, mock_client):
        """Test getting version with JSON output format."""
        ctx_obj = {"config_path": None}

        with patch("ab_cli.cli.versions.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(versions, [
                "get",
                "00000000-0000-4000-a000-000000000001",
                "00000000-0000-4000-a000-000000000101",
                "--format", "json"
            ], obj=ctx_obj)

        assert result.exit_code == 0
        assert "agent" in result.output
        assert "version" in result.output

    def test_get_version_not_found(self, runner, mock_client):
        """Test getting a non-existent version."""
        ctx_obj = {"config_path": None}

        # Override mock to raise NotFoundError
        from ab_cli.api.exceptions import NotFoundError
        mock_client.get_version.side_effect = NotFoundError("Resource not found", "nonexistent-version")

        with patch("ab_cli.cli.versions.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(versions, ["get", "00000000-0000-4000-a000-000000000001", "nonexistent-version"], obj=ctx_obj)

        assert result.exit_code != 0
        assert "Resource not found" in result.output


class TestCreateVersion:
    """Tests for create_version command."""

    def test_create_version_basic(self, runner, mock_client, tmp_path):
        """Test basic version creation."""
        ctx_obj = {"config_path": None}

        # Create temporary config file
        config_file = tmp_path / "version_config.json"
        config = {"systemPrompt": "You are a new AI assistant."}
        config_file.write_text(json.dumps(config))

        with patch("ab_cli.cli.versions.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(versions, [
                "create",
                "00000000-0000-4000-a000-000000000001",
                "--config", str(config_file),
                "--version-label", "v3.0",
                "--notes", "New version"
            ], obj=ctx_obj)

        assert result.exit_code == 0

        # Verify client was called with correct parameters
        mock_client.create_version.assert_called_once()
        args, _ = mock_client.create_version.call_args
        assert args[0] == "00000000-0000-4000-a000-000000000001"
        version_create = args[1]
        assert isinstance(version_create, VersionCreate)
        assert version_create.config == config
        assert version_create.version_label == "v3.0"
        assert version_create.notes == "New version"

        # Verify output contains success message
        assert "Version created successfully" in result.output
        assert "Version ID" in result.output

    def test_create_version_invalid_config(self, runner, mock_client, tmp_path):
        """Test version creation with invalid config file."""
        ctx_obj = {"config_path": None}

        # Create invalid JSON file
        config_file = tmp_path / "invalid_config.json"
        config_file.write_text("{invalid json")

        with patch("ab_cli.cli.versions.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(versions, [
                "create",
                "00000000-0000-4000-a000-000000000001",
                "--config", str(config_file)
            ], obj=ctx_obj)

        assert result.exit_code != 0
        assert "Invalid JSON" in result.output
        mock_client.create_version.assert_not_called()

    def test_create_version_agent_not_found(self, runner, mock_client, tmp_path):
        """Test creating version for a non-existent agent."""
        ctx_obj = {"config_path": None}

        # Create temporary config file
        config_file = tmp_path / "version_config.json"
        config = {"systemPrompt": "You are a new AI assistant."}
        config_file.write_text(json.dumps(config))

        # Override mock to raise NotFoundError
        from ab_cli.api.exceptions import NotFoundError
        mock_client.create_version.side_effect = NotFoundError("Agent not found", "nonexistent-agent")

        with patch("ab_cli.cli.versions.get_client", return_value=MagicMock(__enter__=lambda x: mock_client, __exit__=lambda *args: None)):
            result = runner.invoke(versions, [
                "create",
                "nonexistent-agent",
                "--config", str(config_file)
            ], obj=ctx_obj)

        assert result.exit_code != 0
        assert "Agent not found" in result.output
