"""Interface for data providers used by the Agent Builder UI."""

from abc import ABC, abstractmethod
from typing import Any


class DataProvider(ABC):
    """Interface for data providers used by the Agent Builder UI."""

    @abstractmethod
    def get_agents(self) -> list[dict[str, Any]]:
        """Get list of available agents."""
        pass

    @abstractmethod
    def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        """Get agent details by ID."""
        pass

    @abstractmethod
    def create_agent(self, agent_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new agent."""
        pass

    @abstractmethod
    def update_agent(self, agent_id: str, agent_data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing agent."""
        pass

    @abstractmethod
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent by ID."""
        pass

    @abstractmethod
    def invoke_agent(self, agent_id: str, message: str, agent_type: str = "chat") -> str:
        """Invoke an agent with a message.

        Args:
            agent_id: The ID of the agent to invoke
            message: The message to send (for chat) or task data JSON (for task)
            agent_type: Type of agent ("chat", "rag", "tool", "task")

        Returns:
            Agent response as text
        """
        pass

    @abstractmethod
    def get_models(self) -> list[str]:
        """Get list of available models."""
        pass

    @abstractmethod
    def get_guardrails(self) -> list[str]:
        """Get list of available guardrails."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the data provider is healthy."""
        pass

    @abstractmethod
    def clear_cache(self) -> None:
        """Clear any cached data."""
        pass
