"""Invocation service for business logic.

This service provides invocation-related operations with business logic
extracted from CLI commands, making it reusable by both CLI and UI.
"""

from uuid import UUID

from ab_cli.api.client import AgentBuilderClient
from ab_cli.models.invocation import ChatMessage, InvokeRequest, InvokeResponse, InvokeTaskRequest


class InvocationService:
    """Service for agent invocation operations.

    This service wraps the API client and provides invocation-related
    business logic that can be used by both CLI and UI components.
    """

    def __init__(self, client: AgentBuilderClient) -> None:
        """Initialize the invocation service.

        Args:
            client: The API client to use for requests.
        """
        self.client = client

    def invoke_agent(
        self,
        agent_id: str | UUID,
        message: str,
        _agent_type: str | None = None,
        version_id: str | UUID | None = None,
    ) -> InvokeResponse:
        """Invoke an agent with a message (for chat/tool agents).

        Args:
            agent_id: The agent ID.
            message: The message to send to the agent.
            _agent_type: The agent type (tool, rag) - reserved for future validation.
            version_id: The version ID or 'latest' (default: 'latest').

        Returns:
            InvokeResponse with the agent's response.

        Raises:
            ValidationError: If invocation data is invalid.
            NotFoundError: If agent not found.
        """
        # Use 'latest' if no version specified
        version = version_id or "latest"

        # Create invocation request with message
        request = InvokeRequest(messages=[ChatMessage(role="user", content=message)])

        # Call API client
        return self.client.invoke_agent(agent_id, version, request)

    def invoke_task(
        self,
        agent_id: str | UUID,
        input_data: dict,
        version_id: str | UUID | None = None,
    ) -> InvokeResponse:
        """Invoke a task agent with structured input.

        Args:
            agent_id: The agent ID.
            input_data: The structured input data for the task.
            version_id: The version ID or 'latest' (default: 'latest').

        Returns:
            InvokeResponse with the agent's response.

        Raises:
            ValidationError: If invocation data is invalid.
            NotFoundError: If agent not found.
        """
        # Use 'latest' if no version specified
        version = version_id or "latest"

        # Create task invocation request
        request = InvokeTaskRequest(inputs=input_data)

        # Call API client
        return self.client.invoke_task(agent_id, version, request)
