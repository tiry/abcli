"""Tests for InvocationService."""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from ab_cli.models.invocation import ChatMessage, InvokeResponse
from ab_cli.services.invocation_service import InvocationService


@pytest.fixture
def mock_client():
    """Create a mock API client."""
    return Mock()


@pytest.fixture
def invocation_service(mock_client):
    """Create an InvocationService with a mock client."""
    return InvocationService(mock_client)


@pytest.fixture
def sample_response():
    """Create a sample invocation response."""
    return InvokeResponse(
        messages=[
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there!"),
        ],
        model="gpt-4",
    )


class TestInvocationService:
    """Tests for InvocationService class."""

    def test_init(self, mock_client):
        """Test service initialization."""
        service = InvocationService(mock_client)
        assert service.client == mock_client

    def test_invoke_agent(self, invocation_service, mock_client, sample_response):
        """Test invoking an agent."""
        # Arrange
        agent_id = str(uuid4())
        message = "Hello, agent!"
        mock_client.invoke_agent.return_value = sample_response

        # Act
        result = invocation_service.invoke_agent(agent_id, message)

        # Assert
        assert result == sample_response
        assert mock_client.invoke_agent.called
        call_args = mock_client.invoke_agent.call_args
        assert call_args[0][0] == agent_id
        assert call_args[0][1] == "latest"

    def test_invoke_agent_with_version(self, invocation_service, mock_client, sample_response):
        """Test invoking an agent with specific version."""
        # Arrange
        agent_id = str(uuid4())
        version_id = str(uuid4())
        message = "Hello, agent!"
        mock_client.invoke_agent.return_value = sample_response

        # Act
        result = invocation_service.invoke_agent(agent_id, message, version_id=version_id)

        # Assert
        assert result == sample_response
        assert mock_client.invoke_agent.called
        call_args = mock_client.invoke_agent.call_args
        assert call_args[0][0] == agent_id
        assert call_args[0][1] == version_id

    def test_invoke_agent_with_agent_type(self, invocation_service, mock_client, sample_response):
        """Test invoking an agent with agent type specified."""
        # Arrange
        agent_id = str(uuid4())
        message = "Hello, agent!"
        mock_client.invoke_agent.return_value = sample_response

        # Act
        result = invocation_service.invoke_agent(agent_id, message, _agent_type="tool")

        # Assert
        assert result == sample_response
        assert mock_client.invoke_agent.called

    def test_invoke_task(self, invocation_service, mock_client, sample_response):
        """Test invoking a task agent."""
        # Arrange
        agent_id = str(uuid4())
        input_data = {"query": "Test query"}
        mock_client.invoke_task.return_value = sample_response

        # Act
        result = invocation_service.invoke_task(agent_id, input_data)

        # Assert
        assert result == sample_response
        assert mock_client.invoke_task.called
        call_args = mock_client.invoke_task.call_args
        assert call_args[0][0] == agent_id
        assert call_args[0][1] == "latest"

    def test_invoke_task_with_version(self, invocation_service, mock_client, sample_response):
        """Test invoking a task agent with specific version."""
        # Arrange
        agent_id = str(uuid4())
        version_id = str(uuid4())
        input_data = {"query": "Test query"}
        mock_client.invoke_task.return_value = sample_response

        # Act
        result = invocation_service.invoke_task(agent_id, input_data, version_id=version_id)

        # Assert
        assert result == sample_response
        assert mock_client.invoke_task.called
        call_args = mock_client.invoke_task.call_args
        assert call_args[0][0] == agent_id
        assert call_args[0][1] == version_id
