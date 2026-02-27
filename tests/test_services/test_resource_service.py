"""Tests for ResourceService."""

from unittest.mock import Mock

import pytest

from ab_cli.models.resources import GuardrailList, GuardrailModel, LLMModel, LLMModelList
from ab_cli.services.resource_service import ResourceService


@pytest.fixture
def mock_client():
    """Create a mock API client."""
    return Mock()


@pytest.fixture
def resource_service(mock_client):
    """Create a ResourceService with a mock client."""
    return ResourceService(mock_client)


@pytest.fixture
def sample_model():
    """Create a sample LLM model."""
    return LLMModel(
        id="gpt-4",
        name="GPT-4",
        description="GPT-4 model",
        badge="recommended",
        metadata="{}",
        agent_types=["tool", "rag"],
        capabilities={"chat": True, "completion": True},
        regions=["us-east-1"],
    )


@pytest.fixture
def sample_guardrail():
    """Create a sample guardrail."""
    return GuardrailModel(
        name="Test Guardrail",
        description="A test guardrail",
    )


class TestResourceService:
    """Tests for ResourceService class."""

    def test_init(self, mock_client):
        """Test service initialization."""
        service = ResourceService(mock_client)
        assert service.client == mock_client

    def test_list_models(self, resource_service, mock_client, sample_model):
        """Test listing models."""
        # Arrange
        from ab_cli.models.agent import Pagination
        model_list = LLMModelList(
            models=[sample_model],
            pagination=Pagination(limit=100, offset=0, total_items=1),
        )
        mock_client.list_models.return_value = model_list

        # Act
        result = resource_service.list_models(limit=100, offset=0)

        # Assert
        assert result == model_list
        mock_client.list_models.assert_called_once_with(agent_type=None, limit=100, offset=0)

    def test_list_models_with_agent_type(self, resource_service, mock_client, sample_model):
        """Test listing models filtered by agent type."""
        # Arrange
        from ab_cli.models.agent import Pagination
        model_list = LLMModelList(
            models=[sample_model],
            pagination=Pagination(limit=100, offset=0, total_items=1),
        )
        mock_client.list_models.return_value = model_list

        # Act
        result = resource_service.list_models(limit=100, offset=0, agent_type="tool")

        # Assert
        assert result == model_list
        mock_client.list_models.assert_called_once_with(agent_type="tool", limit=100, offset=0)

    def test_list_models_default_params(self, resource_service, mock_client, sample_model):
        """Test listing models with default parameters."""
        # Arrange
        from ab_cli.models.agent import Pagination
        model_list = LLMModelList(
            models=[sample_model],
            pagination=Pagination(limit=100, offset=0, total_items=1),
        )
        mock_client.list_models.return_value = model_list

        # Act
        result = resource_service.list_models()

        # Assert
        assert result == model_list
        mock_client.list_models.assert_called_once_with(agent_type=None, limit=100, offset=0)

    def test_list_guardrails(self, resource_service, mock_client, sample_guardrail):
        """Test listing guardrails."""
        # Arrange
        from ab_cli.models.agent import Pagination
        guardrail_list = GuardrailList(
            guardrails=[sample_guardrail],
            pagination=Pagination(limit=100, offset=0, total_items=1),
        )
        mock_client.list_guardrails.return_value = guardrail_list

        # Act
        result = resource_service.list_guardrails(limit=100, offset=0)

        # Assert
        assert result == guardrail_list
        mock_client.list_guardrails.assert_called_once_with(limit=100, offset=0)

    def test_list_guardrails_default_params(self, resource_service, mock_client, sample_guardrail):
        """Test listing guardrails with default parameters."""
        # Arrange
        from ab_cli.models.agent import Pagination
        guardrail_list = GuardrailList(
            guardrails=[sample_guardrail],
            pagination=Pagination(limit=100, offset=0, total_items=1),
        )
        mock_client.list_guardrails.return_value = guardrail_list

        # Act
        result = resource_service.list_guardrails()

        # Assert
        assert result == guardrail_list
        mock_client.list_guardrails.assert_called_once_with(limit=100, offset=0)

    def test_list_knowledge_bases(self, resource_service, mock_client):
        """Test listing knowledge bases (placeholder)."""
        # Act
        result = resource_service.list_knowledge_bases(limit=50, offset=10)

        # Assert
        assert isinstance(result, dict)
        assert result["items"] == []
        assert result["total"] == 0
        assert result["limit"] == 50
        assert result["offset"] == 10
        # Client should not be called since this is a placeholder
        mock_client.list_knowledge_bases.assert_not_called()
