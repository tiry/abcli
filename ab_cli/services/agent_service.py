"""Agent service for business logic.

This service provides agent-related operations with business logic
extracted from CLI commands, making it reusable by both CLI and UI.
"""

from typing import Any
from uuid import UUID

from ab_cli.api.client import AgentBuilderClient
from ab_cli.api.pagination import PaginatedResult
from ab_cli.models.agent import Agent, AgentCreate, AgentList, AgentPatch, AgentUpdate, AgentVersion


class AgentService:
    """Service for agent operations.

    This service wraps the API client and provides agent-related
    business logic that can be used by both CLI and UI components.
    """

    def __init__(self, client: AgentBuilderClient) -> None:
        """Initialize the agent service.

        Args:
            client: The API client to use for requests.
        """
        self.client = client

    def list_agents(
        self,
        limit: int | None = None,
        offset: int = 0,
        _agent_type: str | None = None,
        _name_pattern: str | None = None,
    ) -> AgentList:
        """List agents with optional filtering.

        Args:
            limit: Maximum number of agents to return (default: 50).
            offset: Offset for pagination (default: 0).
            _agent_type: Filter by agent type (tool, rag, task) - reserved for future use.
            _name_pattern: Filter by name pattern - reserved for future use.

        Returns:
            AgentList with items and pagination metadata.

        Note:
            Currently the API client doesn't support agent_type and name_pattern
            filtering in list_agents(). These parameters are reserved for future
            compatibility and can be used for client-side filtering if needed.
        """
        # Use default limit if not provided
        actual_limit = limit if limit is not None else 50

        # Call the API client
        agent_list = self.client.list_agents(limit=actual_limit, offset=offset)

        # TODO: Apply client-side filtering if _agent_type or _name_pattern provided
        # This can be implemented when needed for the CLI/UI

        return agent_list

    def list_agents_paginated(self, limit: int, offset: int) -> PaginatedResult:
        """List agents with pagination metadata.

        Args:
            limit: Maximum number of agents to return.
            offset: Offset for pagination.

        Returns:
            PaginatedResult with agents and pagination metadata.
        """
        agent_list = self.client.list_agents(limit=limit, offset=offset)

        # Convert AgentList to PaginatedResult
        return PaginatedResult(
            agents=agent_list.agents,
            offset=offset,
            limit=limit,
            total_count=agent_list.pagination.total_items,
            has_filters=False,
            agent_type=None,
            name_pattern=None,
        )

    def get_agent(
        self, agent_id: str | UUID, version_id: str | UUID | None = None
    ) -> AgentVersion | None:
        """Get an agent with a specific version or the latest version.

        Args:
            agent_id: The agent ID.
            version_id: The version ID or 'latest' (default: 'latest').

        Returns:
            AgentVersion with agent metadata and version configuration,
            or None if not found.
        """
        try:
            return self.client.get_agent(agent_id, version_id)
        except Exception:
            # Return None if agent not found
            return None

    def create_agent(self, agent_data: dict[str, Any]) -> AgentVersion:
        """Create a new agent.

        Args:
            agent_data: Dictionary containing agent creation data.
                Should include: name, description, agent_type, version_label,
                notes, and config.

        Returns:
            AgentVersion with the created agent and its initial version.

        Raises:
            ValidationError: If agent data is invalid.
        """
        # Create AgentCreate model from dict
        agent_create = AgentCreate.model_validate(agent_data)

        # Call API client
        response = self.client.create_agent(agent_create)

        # The create_agent endpoint returns a dict, we need to get the full
        # agent with its version using get_agent
        agent_id = response.get("id")
        if not agent_id:
            # Fallback: try to construct from response
            raise ValueError("API response missing agent ID")

        # Fetch the complete agent with version
        agent_version = self.client.get_agent(agent_id)
        return agent_version

    def update_agent(self, agent_id: str | UUID, agent_data: dict[str, Any]) -> AgentVersion:
        """Update an agent (creates a new version).

        Args:
            agent_id: The agent ID to update.
            agent_data: Dictionary containing update data.
                Should include: config, version_label (optional), notes (optional).

        Returns:
            AgentVersion with the updated agent and new version.

        Raises:
            ValidationError: If update data is invalid.
            NotFoundError: If agent not found.
        """
        # Create AgentUpdate model from dict
        agent_update = AgentUpdate.model_validate(agent_data)

        # Call API client
        return self.client.update_agent(agent_id, agent_update)

    def patch_agent(
        self, agent_id: str | UUID, name: str | None = None, description: str | None = None
    ) -> Agent:
        """Patch an agent's name or description without creating a new version.

        Args:
            agent_id: The agent ID to patch.
            name: New name (optional).
            description: New description (optional).

        Returns:
            Updated Agent metadata.

        Raises:
            ValidationError: If patch data is invalid.
            NotFoundError: If agent not found.
        """
        # Create AgentPatch model
        patch_data = {}
        if name is not None:
            patch_data["name"] = name
        if description is not None:
            patch_data["description"] = description

        agent_patch = AgentPatch.model_validate(patch_data)

        # Call API client
        return self.client.patch_agent(agent_id, agent_patch)

    def delete_agent(self, agent_id: str | UUID) -> bool:
        """Delete an agent.

        Args:
            agent_id: The agent ID.

        Returns:
            True if deleted successfully, False otherwise.

        Raises:
            NotFoundError: If agent not found.
        """
        try:
            self.client.delete_agent(agent_id)
            return True
        except Exception:
            return False

    def list_agent_types(self) -> Any:
        """List available agent types.

        Returns:
            AgentTypeList with available agent types.

        Raises:
            APIError: If the API request fails.
        """
        return self.client.list_agent_types()
