"""Data provider for UI testing."""

import json
import os
import uuid
from typing import Any, Optional
from datetime import datetime, UTC, timezone

from ab_cli.abui.providers.mock_data_provider import MockDataProvider
from ab_cli.models.agent import Agent, AgentCreate, AgentUpdate, AgentVersion, VersionConfig


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

        # In-memory test agents dictionary - now storing Agent models
        self.test_agents: dict[str, Agent] = {}
        
        # In-memory test agent versions dictionary - storing AgentVersion models
        self.test_agent_versions: dict[str, AgentVersion] = {}
    
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

    def add_test_agent(self, agent_data: dict[str, Any]) -> Agent:
        """Add a test agent that will be retrievable through get_agent.
        
        Args:
            agent_data: Dictionary containing agent data. Must include an 'id' key.
            
        Returns:
            The Agent model that was added
            
        Raises:
            ValueError: If agent_data doesn't include an 'id' key
        """
        if "id" not in agent_data:
            raise ValueError("Agent data must include an 'id' key")
        
        self._track_method_call("add_test_agent")
        
        # Convert dict to Agent model
        agent = Agent.model_validate(agent_data)
        agent_id = str(agent.id)
        
        self.test_agents[agent_id] = agent
        
        # Also add to agents list in cache if it's not there already
        if "agents" in self.cache:
            agents = self.cache["agents"]
            if not any(str(a.id) == agent_id for a in agents):
                agents.append(agent)
        
        return agent
    
    def add_test_agent_version(self, agent_version: AgentVersion) -> AgentVersion:
        """Add a test agent version that will be retrievable through get_agent.
        
        Args:
            agent_version: AgentVersion model containing agent and version data.
            
        Returns:
            The AgentVersion model that was added
        """
        self._track_method_call("add_test_agent_version")
        
        agent_id = str(agent_version.agent.id)
        self.test_agent_versions[agent_id] = agent_version
        
        # Also add the agent to test_agents
        self.test_agents[agent_id] = agent_version.agent
        
        return agent_version
    
    def get_agents(self) -> list[Agent]:
        """Get list of available agents with test tracking.
        
        Returns:
            List of Agent Pydantic models
            
        Raises:
            RuntimeError: If error simulation is enabled
        """
        self._track_method_call("get_agents")
        
        if self.simulate_error["get_agents"]:
            raise RuntimeError("Simulated error in get_agents")
        
        agents = super().get_agents()
        
        # Add any test agents to the list
        for agent_id, agent in self.test_agents.items():
            if not any(str(a.id) == agent_id for a in agents):
                agents.append(agent)
        
        return agents
    
    def get_agent(self, agent_id: str) -> AgentVersion | None:
        """Get agent details by ID with test tracking.
        
        Args:
            agent_id: The ID of the agent to retrieve
            
        Returns:
            AgentVersion Pydantic model or None if not found
            
        Raises:
            RuntimeError: If error simulation is enabled
        """
        self._track_method_call("get_agent")
        
        if self.simulate_error["get_agent"]:
            raise RuntimeError(f"Simulated error in get_agent for ID {agent_id}")
        
        # Check test agent versions first
        if agent_id in self.test_agent_versions:
            return self.test_agent_versions[agent_id]
        
        # Check if we have a test agent without version
        if agent_id in self.test_agents:
            agent = self.test_agents[agent_id]
            # Create a default version for the test agent
            default_version = VersionConfig(
                id=str(uuid.uuid4()),
                number=1,
                version_label="v1.0.0",
                notes="Test version",
                created_at=agent.created_at,
                created_by=agent.created_by,
                config={},
            )
            agent_version = AgentVersion(agent=agent, version=default_version)
            # Cache it for future use
            self.test_agent_versions[agent_id] = agent_version
            return agent_version
        
        return super().get_agent(agent_id)
    
    def create_agent(self, agent_data: dict[str, Any] | AgentCreate) -> AgentVersion:
        """Create a new agent with test tracking.
        
        Args:
            agent_data: Dictionary or AgentCreate model containing agent data
            
        Returns:
            Created AgentVersion Pydantic model
            
        Raises:
            RuntimeError: If error simulation is enabled
        """
        self._track_method_call("create_agent")
        
        if self.simulate_error["create_agent"]:
            raise RuntimeError("Simulated error in create_agent")
        
        # Convert dict to AgentCreate if needed
        if isinstance(agent_data, dict):
            agent_data = AgentCreate.model_validate(agent_data)
        
        agent_version = super().create_agent(agent_data)
        
        # Store in test agents for tracking
        agent_id = str(agent_version.agent.id)
        self.test_agents[agent_id] = agent_version.agent
        self.test_agent_versions[agent_id] = agent_version
        
        return agent_version
    
    def update_agent(self, agent_id: str, agent_data: dict[str, Any] | AgentUpdate) -> AgentVersion:
        """Update an existing agent with test tracking.
        
        Args:
            agent_id: The ID of the agent to update
            agent_data: Dictionary or AgentUpdate model containing agent data
            
        Returns:
            Updated AgentVersion Pydantic model
            
        Raises:
            RuntimeError: If error simulation is enabled
        """
        self._track_method_call("update_agent")
        
        if self.simulate_error["update_agent"]:
            raise RuntimeError(f"Simulated error in update_agent for ID {agent_id}")
        
        # Convert to dict if it's a Pydantic model
        if isinstance(agent_data, AgentUpdate):
            agent_data_dict = agent_data.model_dump(by_alias=True)
        else:
            agent_data_dict = agent_data
        
        # First check test agents
        if agent_id in self.test_agents:
            agent = self.test_agents[agent_id]
            
            # Create new version
            created_at = datetime.now(timezone.utc).isoformat() + "Z"
            
            # Determine next version number
            next_number = 1
            if agent_id in self.test_agent_versions:
                next_number = self.test_agent_versions[agent_id].version.number + 1
            
            new_version = VersionConfig(
                id=str(uuid.uuid4()),
                number=next_number,
                version_label=agent_data_dict.get("version_label", f"v1.0.{next_number}"),
                notes=agent_data_dict.get("notes", f"Version {next_number}"),
                created_at=created_at,
                created_by="system",
                config=agent_data_dict.get("config", {}),
            )
            
            agent_version = AgentVersion(agent=agent, version=new_version)
            self.test_agent_versions[agent_id] = agent_version
            
            return agent_version
        
        # Convert dict to AgentUpdate if needed for parent call
        if isinstance(agent_data, dict):
            agent_data = AgentUpdate.model_validate(agent_data)
        
        # Try parent's update_agent which will check cached agents
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
        deleted = False
        if agent_id in self.test_agents:
            del self.test_agents[agent_id]
            deleted = True
        
        if agent_id in self.test_agent_versions:
            del self.test_agent_versions[agent_id]
            deleted = True
        
        if deleted:
            return True
        
        return super().delete_agent(agent_id)
    
    def clear_cache(self) -> None:
        """Clear the data cache with test tracking."""
        self._track_method_call("clear_cache")
        super().clear_cache()


# For backward compatibility, also mark as not a test
TestDataProvider = MockTestingProvider
TestDataProvider.__test__ = False
