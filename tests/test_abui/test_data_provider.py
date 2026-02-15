"""Data provider for UI testing."""

import json
import os
import pytest
from typing import Any, Optional, cast
from datetime import datetime, UTC

from ab_cli.abui.providers.mock_data_provider import MockDataProvider


# Use pytest's collection configuration to prevent collection
# The class name starts with "Mock" not "Test" to avoid pytest collection
class MockTestingProvider(MockDataProvider):
    """Data provider for UI testing with controlled test data and error simulation.
    
    This provider extends the MockDataProvider with additional testing capabilities:
    1. Uses test-specific data files
    2. Provides methods to simulate errors
    3. Tracks method calls for assertion
    4. Has deterministic behavior for testing
    """
    
    # Adding __test__ = False explicitly tells pytest not to collect this class
    __test__ = False
    
    def __init__(self, config: Any = None, data_dir: Optional[str] = None):
        """Initialize with path to test data directory.
        
        Args:
            config: Configuration object with settings
            data_dir: Directory containing test data files
        """
        # Default to test data directory if not provided
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "test_data")
        
        # Call parent initializer
        super().__init__(config, data_dir)
        
        # Track method calls for testing
        self.method_calls: dict[str, int] = {}
        
        # Flag to simulate various error conditions
        self.simulate_error: dict[str, bool] = {
            "get_agents": False,
            "get_agent": False,
            "create_agent": False,
            "update_agent": False,
            "delete_agent": False,
            "invoke_agent": False,
            "get_models": False,
            "get_guardrails": False,
        }

        # In-memory test agents dictionary
        self.test_agents: dict[str, dict[str, Any]] = {}
    
    def _track_method_call(self, method_name: str) -> None:
        """Track a method call for later assertions.
        
        Args:
            method_name: Name of the method being called
        """
        if method_name not in self.method_calls:
            self.method_calls[method_name] = 0
        self.method_calls[method_name] += 1
    
    def get_call_count(self, method_name: str) -> int:
        """Get the number of times a method has been called.
        
        Args:
            method_name: Name of the method to check
            
        Returns:
            Number of times the method has been called
        """
        return self.method_calls.get(method_name, 0)
    
    def reset_call_tracking(self) -> None:
        """Reset the call tracking counters."""
        self.method_calls = {}
    
    def set_error_simulation(self, method_name: str, simulate: bool = True) -> None:
        """Configure the provider to simulate an error for a specific method.
        
        Args:
            method_name: Name of the method to simulate error for
            simulate: Whether to simulate the error (True) or not (False)
        """
        if method_name in self.simulate_error:
            self.simulate_error[method_name] = simulate
    
    def reset_error_simulation(self) -> None:
        """Reset all error simulation flags to False."""
        for method in self.simulate_error:
            self.simulate_error[method] = False

    def add_test_agent(self, agent_data: dict[str, Any]) -> dict[str, Any]:
        """Add a test agent that will be retrievable through get_agent.
        
        Args:
            agent_data: Dictionary containing agent data. Must include an 'id' key.
            
        Returns:
            The agent data that was added
            
        Raises:
            ValueError: If agent_data doesn't include an 'id' key
        """
        if "id" not in agent_data:
            raise ValueError("Agent data must include an 'id' key")
        
        self._track_method_call("add_test_agent")
        
        agent_id = agent_data["id"]
        self.test_agents[agent_id] = agent_data
        
        # Also add to agents list if it's not there already
        agents = super().get_agents()
        if not any(agent["id"] == agent_id for agent in agents):
            agents.append(agent_data)
        
        return agent_data
    
    def get_agents(self) -> list[dict[str, Any]]:
        """Get list of available agents with test tracking.
        
        Returns:
            List of agent dictionaries
            
        Raises:
            RuntimeError: If error simulation is enabled
        """
        self._track_method_call("get_agents")
        
        if self.simulate_error["get_agents"]:
            raise RuntimeError("Simulated error in get_agents")
        
        agents = super().get_agents()
        
        # Add any test agents to the list
        for agent_id, agent_data in self.test_agents.items():
            if not any(agent["id"] == agent_id for agent in agents):
                agents.append(agent_data)
        
        return agents
    
    def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        """Get agent details by ID with test tracking.
        
        Args:
            agent_id: The ID of the agent to retrieve
            
        Returns:
            Agent dictionary or None if not found
            
        Raises:
            RuntimeError: If error simulation is enabled
        """
        self._track_method_call("get_agent")
        
        if self.simulate_error["get_agent"]:
            raise RuntimeError(f"Simulated error in get_agent for ID {agent_id}")
        
        # Check test agents first
        if agent_id in self.test_agents:
            return self.test_agents[agent_id]
        
        return super().get_agent(agent_id)
    
    def create_agent(self, agent_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new agent with test tracking.
        
        Args:
            agent_data: Dictionary containing agent data
            
        Returns:
            Created agent dictionary
            
        Raises:
            RuntimeError: If error simulation is enabled
        """
        self._track_method_call("create_agent")
        
        if self.simulate_error["create_agent"]:
            raise RuntimeError("Simulated error in create_agent")
        
        return super().create_agent(agent_data)
    
    def update_agent(self, agent_id: str, agent_data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing agent with test tracking.
        
        Args:
            agent_id: The ID of the agent to update
            agent_data: Dictionary containing agent data
            
        Returns:
            Updated agent dictionary
            
        Raises:
            RuntimeError: If error simulation is enabled
        """
        self._track_method_call("update_agent")
        
        if self.simulate_error["update_agent"]:
            raise RuntimeError(f"Simulated error in update_agent for ID {agent_id}")
        
        # Update in test agents if it exists there
        if agent_id in self.test_agents:
            updated_agent = {**self.test_agents[agent_id], **agent_data}
            updated_agent["modified_at"] = datetime.now(UTC).isoformat() + "Z"
            self.test_agents[agent_id] = updated_agent
            return updated_agent
        
        return super().update_agent(agent_id, agent_data)
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent by ID with test tracking.
        
        Args:
            agent_id: The ID of the agent to delete
            
        Returns:
            True if deleted successfully, False otherwise
            
        Raises:
            RuntimeError: If error simulation is enabled
        """
        self._track_method_call("delete_agent")
        
        if self.simulate_error["delete_agent"]:
            raise RuntimeError(f"Simulated error in delete_agent for ID {agent_id}")
        
        # Delete from test agents if it exists there
        if agent_id in self.test_agents:
            del self.test_agents[agent_id]
            return True
        
        return super().delete_agent(agent_id)
    
    def invoke_agent(self, agent_id: str, message: str) -> str:
        """Invoke an agent with a message with test tracking.
        
        Args:
            agent_id: The ID of the agent to invoke
            message: The message to send to the agent
            
        Returns:
            Agent response as text
            
        Raises:
            RuntimeError: If error simulation is enabled
        """
        self._track_method_call("invoke_agent")
        
        if self.simulate_error["invoke_agent"]:
            raise RuntimeError(f"Simulated error in invoke_agent for ID {agent_id}")
        
        return super().invoke_agent(agent_id, message)
    
    def get_models(self) -> list[str]:
        """Get list of available models with test tracking.
        
        Returns:
            List of model names
            
        Raises:
            RuntimeError: If error simulation is enabled
        """
        self._track_method_call("get_models")
        
        if self.simulate_error["get_models"]:
            raise RuntimeError("Simulated error in get_models")
        
        return super().get_models()
    
    def get_guardrails(self) -> list[str]:
        """Get list of available guardrails with test tracking.
        
        Returns:
            List of guardrail names
            
        Raises:
            RuntimeError: If error simulation is enabled
        """
        self._track_method_call("get_guardrails")
        
        if self.simulate_error["get_guardrails"]:
            raise RuntimeError("Simulated error in get_guardrails")
        
        return super().get_guardrails()
    
    def clear_cache(self) -> None:
        """Clear the data cache with test tracking."""
        self._track_method_call("clear_cache")
        super().clear_cache()


# For backward compatibility, also mark as not a test
TestDataProvider = MockTestingProvider
TestDataProvider.__test__ = False