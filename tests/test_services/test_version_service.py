"""Tests for VersionService."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from ab_cli.models.agent import Agent, AgentVersion, Pagination, Version, VersionConfig, VersionList
from ab_cli.services.version_service import VersionService


@pytest.fixture
def mock_client():
    """Create a mock API client."""
    return Mock()


@pytest.fixture
def version_service(mock_client):
    """Create a VersionService with a mock client."""
    return VersionService(mock_client)


@pytest.fixture
def agent():
    """Create a sample agent."""
    return Agent(
        id=str(uuid4()),
        name="Test Agent",
        type="tool",
        description="A test agent",
        status="CREATED",
        is_global_agent=False,
        current_version_id=str(uuid4()),
        created_at="2024-01-01T00:00:00Z",
        created_by="test-user",
        modified_at="2024-01-01T00:00:00Z",
        modified_by="test-user",
    )


@pytest.fixture
def sample_version():
    """Create a sample version."""
    return Version(
        id=str(uuid4()),
        number=1,
        created_at="2024-01-01T00:00:00Z",
        created_by="test-user",
    )


class TestVersionService:
    """Tests for VersionService class."""

    def test_init(self, mock_client):
        """Test service initialization."""
        service = VersionService(mock_client)
        assert service.client == mock_client

    def test_list_versions(self, version_service, mock_client, agent, sample_version):
        """Test listing versions."""
        # Arrange
        agent_id = str(uuid4())
        version_list = VersionList(
            agent=agent,
            versions=[sample_version],
            pagination=Pagination(limit=10, offset=0, total_items=1),
        )
        mock_client.list_versions.return_value = version_list

        # Act
        result = version_service.list_versions(agent_id, limit=10, offset=0)

        # Assert
        assert result == version_list
        mock_client.list_versions.assert_called_once_with(agent_id, limit=10, offset=0)

    def test_list_versions_default_params(self, version_service, mock_client, agent, sample_version):
        """Test listing versions with default parameters."""
        # Arrange
        agent_id = str(uuid4())
        version_list = VersionList(
            agent=agent,
            versions=[sample_version],
            pagination=Pagination(limit=10, offset=0, total_items=1),
        )
        mock_client.list_versions.return_value = version_list

        # Act
        result = version_service.list_versions(agent_id)

        # Assert
        assert result == version_list
        mock_client.list_versions.assert_called_once_with(agent_id, limit=10, offset=0)

    def test_get_version_success(self, version_service, mock_client, agent):
        """Test getting a version successfully."""
        # Arrange
        version_config = VersionConfig(
            id=str(uuid4()),
            number=1,
            version_label="v1.0",
            notes="Test version",
            created_at="2024-01-01T00:00:00Z",
            created_by="test-user",
            config={"model": "gpt-4"},
        )
        agent_version = AgentVersion(agent=agent, version=version_config)
        agent_id = agent.id
        version_id = version_config.id
        mock_client.get_version.return_value = agent_version

        # Act
        result = version_service.get_version(agent_id, version_id)

        # Assert
        assert result == agent_version
        mock_client.get_version.assert_called_once_with(agent_id, version_id)

    def test_get_version_not_found(self, version_service, mock_client):
        """Test getting a version that doesn't exist."""
        # Arrange
        agent_id = str(uuid4())
        version_id = str(uuid4())
        mock_client.get_version.side_effect = Exception("Not found")

        # Act
        result = version_service.get_version(agent_id, version_id)

        # Assert
        assert result is None
        mock_client.get_version.assert_called_once_with(agent_id, version_id)
