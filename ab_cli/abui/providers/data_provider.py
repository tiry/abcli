"""Interface for data providers used by the Agent Builder UI.

This interface defines the contract that all data providers must implement.
Providers can use different backends (mock data, CLI subprocess, direct API calls).
"""

from abc import ABC, abstractmethod

from ab_cli.api.pagination import PaginatedResult
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


class DataProvider(ABC):
    """Abstract base class for data providers.

    All data providers must implement these methods with strongly typed returns.
    This ensures type safety and consistency across different provider implementations.
    """

    # ==================== Agent Operations ====================

    @abstractmethod
    def get_agents(self) -> list[Agent]:
        """Get list of all available agents.

        Returns:
            List of Agent objects with basic metadata.
        """
        pass

    @abstractmethod
    def get_agents_paginated(self, limit: int, offset: int) -> PaginatedResult:
        """Get paginated list of agents.

        Args:
            limit: Maximum number of agents to return.
            offset: Number of agents to skip.

        Returns:
            PaginatedResult containing agents list and pagination metadata.
        """
        pass

    @abstractmethod
    def get_agent(self, agent_id: str) -> AgentVersion | None:
        """Get agent details with current version configuration.

        Args:
            agent_id: The ID of the agent to retrieve.

        Returns:
            AgentVersion object containing agent metadata and version config,
            or None if agent not found.
        """
        pass

    @abstractmethod
    def create_agent(self, agent_create: AgentCreate) -> AgentVersion:
        """Create a new agent.

        Args:
            agent_create: AgentCreate model with name, description, type, config, etc.

        Returns:
            AgentVersion object for the newly created agent.

        Raises:
            ValidationError: If agent_create is invalid.
            APIError: If creation fails.
        """
        pass

    @abstractmethod
    def update_agent(self, agent_id: str, agent_update: AgentUpdate) -> AgentVersion:
        """Update an existing agent (creates a new version).

        Args:
            agent_id: The ID of the agent to update.
            agent_update: AgentUpdate model with config, version_label, and notes.

        Returns:
            AgentVersion object with the new version.

        Raises:
            NotFoundError: If agent not found.
            ValidationError: If agent_update is invalid.
        """
        pass

    @abstractmethod
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent by ID.

        Args:
            agent_id: The ID of the agent to delete.

        Returns:
            True if deletion successful, False otherwise.
        """
        pass

    # ==================== Invocation ====================

    @abstractmethod
    def invoke_agent(self, agent_id: str, message: str, agent_type: str = "chat") -> InvokeResponse:
        """Invoke an agent with a message.

        Args:
            agent_id: The ID of the agent to invoke.
            message: The message to send (for chat) or task data JSON (for task).
            agent_type: Type of agent ("chat", "rag", "tool", "task").

        Returns:
            InvokeResponse containing the agent's response and metadata.

        Raises:
            NotFoundError: If agent not found.
            APIError: If invocation fails.
        """
        pass

    # ==================== Version Operations ====================

    @abstractmethod
    def get_versions(self, agent_id: str, limit: int = 50, offset: int = 0) -> VersionList:
        """Get list of versions for an agent.

        Args:
            agent_id: The ID of the agent.
            limit: Maximum number of versions to return.
            offset: Offset for pagination.

        Returns:
            VersionList containing versions and pagination metadata.

        Raises:
            NotFoundError: If agent not found.
        """
        pass

    @abstractmethod
    def get_version(self, agent_id: str, version_id: str) -> Version | None:
        """Get details of a specific version with full configuration.

        Args:
            agent_id: The ID of the agent.
            version_id: The ID of the version (or "latest").

        Returns:
            Version object with full configuration, or None if not found.
        """
        pass

    # ==================== Resource Operations ====================

    @abstractmethod
    def get_models(self, limit: int = 100, offset: int = 0) -> LLMModelList:
        """Get list of available LLM models.

        Args:
            limit: Maximum number of models to return.
            offset: Offset for pagination.

        Returns:
            LLMModelList containing available models.
        """
        pass

    @abstractmethod
    def get_guardrails(self, limit: int = 100, offset: int = 0) -> GuardrailList:
        """Get list of available guardrails.

        Args:
            limit: Maximum number of guardrails to return.
            offset: Offset for pagination.

        Returns:
            GuardrailList containing available guardrails.
        """
        pass

    @abstractmethod
    def get_agent_types(self, limit: int = 100, offset: int = 0) -> AgentTypeList:
        """Get list of available agent types.

        Args:
            limit: Maximum number of agent types to return.
            offset: Offset for pagination.

        Returns:
            AgentTypeList containing available agent types.
        """
        pass

    # ==================== Provider Health & Cache ====================

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the data provider is healthy and can communicate with backend.

        Returns:
            True if healthy, False otherwise.
        """
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        """Clear any cached data in the provider.

        This allows forcing a refresh of data from the backend.
        """
        pass
