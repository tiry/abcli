"""Direct data provider that calls CLI business logic directly.

This provider eliminates subprocess overhead by calling service layer methods directly,
providing significant performance improvements over the CLI-based provider.
"""

from typing import Any

from ab_cli.abui.providers.data_provider import DataProvider
from ab_cli.api.client import AgentBuilderClient
from ab_cli.api.pagination import PaginatedResult
from ab_cli.config.loader import find_config_file, load_config
from ab_cli.config.settings import ABSettings
from ab_cli.models.agent import (
    Agent,
    AgentCreate,
    AgentTypeList,
    AgentUpdate,
    AgentVersion,
    Version,
    VersionList,
)
from ab_cli.models.invocation import InvokeResponse
from ab_cli.models.resources import GuardrailList, LLMModelList
from ab_cli.services.agent_service import AgentService
from ab_cli.services.invocation_service import InvocationService
from ab_cli.services.resource_service import ResourceService
from ab_cli.services.version_service import VersionService


class DirectDataProvider(DataProvider):
    """Data provider that calls CLI business logic directly (no subprocess).

    This provider uses the service layer to access data directly from the API,
    eliminating the overhead of subprocess calls and JSON parsing.

    Benefits:
    - No subprocess overhead (faster startup)
    - No stdout parsing (direct object access)
    - Strong typing throughout
    - Better error handling
    """

    def __init__(self, settings: ABSettings | None = None) -> None:
        """Initialize the direct data provider.

        Args:
            settings: Optional settings object. If not provided, loads from config file.
        """
        # Use provided settings or load from config file
        if settings is None:
            config_file = find_config_file()
            settings = load_config(config_file)

        # Initialize API client
        self.client = AgentBuilderClient(settings)

        # Initialize service layer
        self.agent_service = AgentService(self.client)
        self.version_service = VersionService(self.client)
        self.resource_service = ResourceService(self.client)
        self.invocation_service = InvocationService(self.client)

    def __enter__(self) -> "DirectDataProvider":
        """Context manager entry."""
        self.client.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.client.__exit__(exc_type, exc_val, exc_tb)

    # ==================== Agent Operations ====================

    def get_agents(self) -> list[Agent]:
        """Get list of all available agents.

        Returns:
            List of Agent objects with basic metadata.
        """
        agent_list = self.agent_service.list_agents()
        return agent_list.agents

    def get_agents_paginated(self, limit: int, offset: int) -> PaginatedResult:
        """Get paginated list of agents.

        Args:
            limit: Maximum number of agents to return.
            offset: Number of agents to skip.

        Returns:
            PaginatedResult containing agents list and pagination metadata.
        """
        return self.agent_service.list_agents_paginated(limit, offset)

    def get_agent(self, agent_id: str) -> AgentVersion | None:
        """Get agent details with current version configuration.

        Args:
            agent_id: The ID of the agent to retrieve.

        Returns:
            AgentVersion object containing agent metadata and version config,
            or None if agent not found.
        """
        return self.agent_service.get_agent(agent_id)

    def create_agent(self, agent_create: AgentCreate) -> AgentVersion:
        """Create a new agent.

        Args:
            agent_create: AgentCreate model containing agent creation data.

        Returns:
            AgentVersion object for the newly created agent.
        """
        # Convert Pydantic model to dict for service layer
        agent_data = agent_create.model_dump(by_alias=True)
        return self.agent_service.create_agent(agent_data)

    def update_agent(self, agent_id: str, agent_update: AgentUpdate) -> AgentVersion:
        """Update an existing agent (creates a new version).

        Args:
            agent_id: The ID of the agent to update.
            agent_update: AgentUpdate model containing update data.

        Returns:
            AgentVersion object with the new version.
        """
        # Convert Pydantic model to dict for service layer
        agent_data = agent_update.model_dump(by_alias=True)
        return self.agent_service.update_agent(agent_id, agent_data)

    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent by ID.

        Args:
            agent_id: The ID of the agent to delete.

        Returns:
            True if deletion successful, False otherwise.
        """
        return self.agent_service.delete_agent(agent_id)

    # ==================== Invocation ====================

    def invoke_agent(self, agent_id: str, message: str, agent_type: str = "chat") -> InvokeResponse:
        """Invoke an agent with a message.

        Args:
            agent_id: The ID of the agent to invoke.
            message: The message to send (for chat) or task data JSON (for task).
            agent_type: Type of agent ("chat", "rag", "tool", "task").

        Returns:
            InvokeResponse containing the agent's response and metadata.
        """
        if agent_type == "task":
            # invoke_task expects dict, parse JSON string
            import json

            task_data = json.loads(message) if isinstance(message, str) else message
            return self.invocation_service.invoke_task(agent_id, task_data)
        else:
            return self.invocation_service.invoke_agent(agent_id, message, _agent_type=agent_type)

    # ==================== Version Operations ====================

    def get_versions(self, agent_id: str, limit: int = 50, offset: int = 0) -> VersionList:
        """Get list of versions for an agent.

        Args:
            agent_id: The ID of the agent.
            limit: Maximum number of versions to return.
            offset: Offset for pagination.

        Returns:
            VersionList containing versions and pagination metadata.
        """
        return self.version_service.list_versions(agent_id, limit, offset)

    def get_version(self, agent_id: str, version_id: str) -> Version | None:
        """Get details of a specific version with full configuration.

        Args:
            agent_id: The ID of the agent.
            version_id: The ID of the version (or "latest").

        Returns:
            Version object with full configuration, or None if not found.
        """
        result = self.version_service.get_version(agent_id, version_id)
        # Return type is actually AgentVersion from service, but interface expects Version
        # For now, return as-is and let type checker know we're aware of the mismatch
        return result  # type: ignore[return-value]

    # ==================== Resource Operations ====================

    def get_models(self, limit: int = 100, offset: int = 0) -> LLMModelList:
        """Get list of available LLM models.

        Args:
            limit: Maximum number of models to return.
            offset: Offset for pagination.

        Returns:
            LLMModelList containing available models.
        """
        return self.resource_service.list_models(limit, offset)

    def get_guardrails(self, limit: int = 100, offset: int = 0) -> GuardrailList:
        """Get list of available guardrails.

        Args:
            limit: Maximum number of guardrails to return.
            offset: Offset for pagination.

        Returns:
            GuardrailList containing available guardrails.
        """
        return self.resource_service.list_guardrails(limit, offset)

    def get_agent_types(self, _limit: int = 100, _offset: int = 0) -> AgentTypeList:
        """Get list of available agent types.

        Args:
            _limit: Maximum number of agent types to return (unused - API returns all).
            _offset: Offset for pagination (unused - API returns all).

        Returns:
            AgentTypeList containing available agent types.
        """
        return self.agent_service.list_agent_types()

    # ==================== Provider Health & Cache ====================

    def health_check(self) -> bool:
        """Check if the data provider is healthy and can communicate with backend.

        Returns:
            True if healthy, False otherwise.
        """
        try:
            # Try to list agents with minimal limit as health check
            self.agent_service.list_agents(limit=1)
            return True
        except Exception:
            return False

    def clear_cache(self) -> None:
        """Clear any cached data in the provider.

        Note: Direct provider doesn't implement caching yet.
        This is a no-op for now but kept for interface compatibility.
        """
        pass  # No caching implemented yet
