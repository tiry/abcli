"""Resource service for business logic.

This service provides resource-related operations with business logic
extracted from CLI commands, making it reusable by both CLI and UI.
"""

from ab_cli.api.client import AgentBuilderClient
from ab_cli.models.resources import GuardrailList, LLMModelList


class ResourceService:
    """Service for resource operations.

    This service wraps the API client and provides resource-related
    business logic that can be used by both CLI and UI components.
    """

    def __init__(self, client: AgentBuilderClient) -> None:
        """Initialize the resource service.

        Args:
            client: The API client to use for requests.
        """
        self.client = client

    def list_models(
        self, limit: int = 100, offset: int = 0, agent_type: str | None = None
    ) -> LLMModelList:
        """List available LLM models.

        Args:
            limit: Maximum number of models to return (default: 100).
            offset: Offset for pagination (default: 0).
            agent_type: Filter by agent type (tool, rag, task) - optional.

        Returns:
            LLMModelList with models and pagination metadata.
        """
        return self.client.list_models(agent_type=agent_type, limit=limit, offset=offset)

    def list_guardrails(self, limit: int = 100, offset: int = 0) -> GuardrailList:
        """List available guardrails.

        Args:
            limit: Maximum number of guardrails to return (default: 100).
            offset: Offset for pagination (default: 0).

        Returns:
            GuardrailList with guardrails and pagination metadata.
        """
        return self.client.list_guardrails(limit=limit, offset=offset)

    def list_knowledge_bases(self, limit: int = 100, offset: int = 0) -> dict:
        """List available knowledge bases.

        Args:
            limit: Maximum number of knowledge bases to return (default: 100).
            offset: Offset for pagination (default: 0).

        Returns:
            Dictionary with knowledge bases and pagination metadata.

        Note:
            Knowledge base listing is not yet fully implemented in the API client.
            This method returns a placeholder dict for now.
        """
        # TODO: Implement when knowledge base API is available
        return {
            "items": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
        }
