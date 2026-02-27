"""Tests for AgentService."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from ab_cli.api.pagination import PaginatedResult
from ab_cli.models.agent import Agent, AgentList, AgentVersion, Pagination, VersionConfig
from ab_cli.services.agent_service import AgentService


@pytest.fixture
def mock_client():
    """Create a mock API client."""
    return Mock()


@pytest.fixture
def agent_service(mock_client):
    """Create an AgentService with a mock client."""
    return AgentService(mock_client)


@pytest.fixture
def sample_agent():
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
def sample_agent_version(sample_agent):
    """Create a sample agent version."""
    return AgentVersion(
        agent=sample_agent,
        version=VersionConfig(
            id=sample_agent.current_version_id,
            number=1,
            version_label="v1.0",
            notes="Test version",
            created_at="2024-01-01T00:00:00Z",
            created_by="test-user",
            config={"model": "gpt-4"},
        ),
    )


class TestAgentService:
    """Tests for AgentService class."""

    def test_init(self, mock_client):
        """Test service initialization."""
        service = AgentService(mock_client)
        assert service.client == mock_client

    def test_list_agents(self, agent_service, mock_client, sample_agent):
        """Test listing agents."""
        # Arrange
        agent_list = AgentList(
            agents=[sample_agent],
            pagination=Pagination(limit=50, offset=0, total_items=1),
        )
        mock_client.list_agents.return_value = agent_list

        # Act
        result = agent_service.list_agents()

        # Assert
        assert result == agent_list
        mock_client.list_agents.assert_called_once_with(limit=50, offset=0)

    def test_list_agents_with_params(self, agent_service, mock_client, sample_agent):
        """Test listing agents with custom parameters."""
        # Arrange
        agent_list = AgentList(
            agents=[sample_agent],
            pagination=Pagination(limit=10, offset=5, total_items=1),
        )
        mock_client.list_agents.return_value = agent_list

        # Act
        result = agent_service.list_agents(limit=10, offset=5, _agent_type="tool")

        # Assert
        assert result == agent_list
        mock_client.list_agents.assert_called_once_with(limit=10, offset=5)

    def test_list_agents_paginated(self, agent_service, mock_client, sample_agent):
        """Test listing agents with pagination."""
        # Arrange
        agent_list = AgentList(
            agents=[sample_agent],
            pagination=Pagination(limit=10, offset=0, total_items=1),
        )
        mock_client.list_agents.return_value = agent_list

        # Act
        result = agent_service.list_agents_paginated(limit=10, offset=0)

        # Assert
        assert isinstance(result, PaginatedResult)
        assert len(result.agents) == 1
        assert result.total_count == 1
        assert result.limit == 10
        assert result.offset == 0
        mock_client.list_agents.assert_called_once_with(limit=10, offset=0)

    def test_get_agent_success(self, agent_service, mock_client, sample_agent_version):
        """Test getting an agent successfully."""
        # Arrange
        mock_client.get_agent.return_value = sample_agent_version
        agent_id = sample_agent_version.agent.id

        # Act
        result = agent_service.get_agent(agent_id)

        # Assert
        assert result == sample_agent_version
        mock_client.get_agent.assert_called_once_with(agent_id, None)

    def test_get_agent_with_version(self, agent_service, mock_client, sample_agent_version):
        """Test getting an agent with specific version."""
        # Arrange
        mock_client.get_agent.return_value = sample_agent_version
        agent_id = sample_agent_version.agent.id
        version_id = sample_agent_version.version.id

        # Act
        result = agent_service.get_agent(agent_id, version_id)

        # Assert
        assert result == sample_agent_version
        mock_client.get_agent.assert_called_once_with(agent_id, version_id)

    def test_get_agent_not_found(self, agent_service, mock_client):
        """Test getting an agent that doesn't exist."""
        # Arrange
        mock_client.get_agent.side_effect = Exception("Not found")
        agent_id = str(uuid4())

        # Act
        result = agent_service.get_agent(agent_id)

        # Assert
        assert result is None
        mock_client.get_agent.assert_called_once_with(agent_id, None)

    def test_create_agent(self, agent_service, mock_client, sample_agent_version):
        """Test creating an agent."""
        # Arrange
        agent_data = {
            "name": "Test Agent",
            "description": "A test agent",
            "agent_type": "tool",
            "version_label": "v1",
            "notes": "Initial version",
            "config": {"model": "gpt-4"},
        }
        agent_id = sample_agent_version.agent.id
        mock_client.create_agent.return_value = {"id": agent_id}
        mock_client.get_agent.return_value = sample_agent_version

        # Act
        result = agent_service.create_agent(agent_data)

        # Assert
        assert result == sample_agent_version
        assert mock_client.create_agent.called
        mock_client.get_agent.assert_called_once_with(agent_id)

    def test_update_agent(self, agent_service, mock_client, sample_agent_version):
        """Test updating an agent."""
        # Arrange
        agent_id = sample_agent_version.agent.id
        update_data = {
            "config": {"model": "gpt-4"},
            "version_label": "v2",
            "notes": "Updated version",
        }
        mock_client.update_agent.return_value = sample_agent_version

        # Act
        result = agent_service.update_agent(agent_id, update_data)

        # Assert
        assert result == sample_agent_version
        assert mock_client.update_agent.called

    def test_patch_agent(self, agent_service, mock_client, sample_agent):
        """Test patching an agent."""
        # Arrange
        agent_id = sample_agent.id
        mock_client.patch_agent.return_value = sample_agent

        # Act
        result = agent_service.patch_agent(agent_id, name="New Name", description="New Description")

        # Assert
        assert result == sample_agent
        assert mock_client.patch_agent.called

    def test_delete_agent_success(self, agent_service, mock_client):
        """Test deleting an agent successfully."""
        # Arrange
        agent_id = str(uuid4())
        mock_client.delete_agent.return_value = None

        # Act
        result = agent_service.delete_agent(agent_id)

        # Assert
        assert result is True
        mock_client.delete_agent.assert_called_once_with(agent_id)

    def test_delete_agent_failure(self, agent_service, mock_client):
        """Test deleting an agent that fails."""
        # Arrange
        agent_id = str(uuid4())
        mock_client.delete_agent.side_effect = Exception("Delete failed")

        # Act
        result = agent_service.delete_agent(agent_id)

        # Assert
        assert result is False
        mock_client.delete_agent.assert_called_once_with(agent_id)
