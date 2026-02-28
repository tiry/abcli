"""Tests for the TestDataProvider class."""

import pytest
import os
from typing import Dict, Any

from tests.test_abui.test_data_provider import TestDataProvider
from ab_cli.models.agent import Agent, AgentVersion


def test_test_data_provider_initialization() -> None:
    """Test that the TestDataProvider initializes correctly."""
    provider = TestDataProvider()
    assert provider is not None


def test_test_data_provider_loads_test_data() -> None:
    """Test that the TestDataProvider loads test data correctly."""
    provider = TestDataProvider()
    
    # Test that we can get agents
    agents = provider.get_agents()
    assert len(agents) > 0
    assert isinstance(agents, list)
    
    # Verify that the first agent is an Agent model with expected fields
    agent = agents[0]
    assert isinstance(agent, Agent)
    assert hasattr(agent, "id")
    assert hasattr(agent, "name")
    assert hasattr(agent, "type")
    assert hasattr(agent, "status")
    assert agent.id is not None
    assert agent.name is not None
    assert agent.type is not None
    assert agent.status is not None


def test_test_data_provider_call_tracking() -> None:
    """Test that the TestDataProvider tracks method calls."""
    provider = TestDataProvider()
    
    # Reset call tracking
    provider.reset_call_tracking()
    
    # Make some calls
    provider.get_agents()
    provider.get_agents()
    
    # Check call counts
    assert provider.get_call_count("get_agents") == 2
    assert provider.get_call_count("get_guardrails") == 0


def test_test_data_provider_error_simulation() -> None:
    """Test that the TestDataProvider can simulate errors."""
    provider = TestDataProvider()
    
    # Set up error simulation for get_agents
    provider.set_error_simulation("get_agents")
    
    # Check that get_agents now raises an error
    with pytest.raises(RuntimeError):
        provider.get_agents()
    
    # Reset error simulation
    provider.reset_error_simulation()
    
    # Check that get_agents works again
    agents = provider.get_agents()
    assert len(agents) > 0


def test_test_data_provider_create_agent() -> None:
    """Test that the TestDataProvider can create agents."""
    provider = TestDataProvider()
    
    # Create a test agent - use AgentCreate compatible fields
    new_agent = {
        "name": "Test Agent",
        "description": "A test agent",
        "agentType": "chat",  # AgentCreate uses agentType
        "config": {},  # AgentCreate uses config not agent_config
        "version_label": "v1.0",
        "notes": "Initial version"
    }
    
    # Create the agent - returns AgentVersion
    created_agent_version = provider.create_agent(new_agent)
    
    # Check that it's an AgentVersion model
    assert isinstance(created_agent_version, AgentVersion)
    assert hasattr(created_agent_version, "agent")
    assert hasattr(created_agent_version, "version")
    
    # Check the agent fields
    agent = created_agent_version.agent
    assert isinstance(agent, Agent)
    assert agent.id is not None
    assert agent.name == "Test Agent"
    assert agent.description == "A test agent"
    assert agent.type == "chat"
    assert agent.status is not None
    assert agent.created_at is not None


def test_test_data_provider_update_agent() -> None:
    """Test that the TestDataProvider can update agents."""
    provider = TestDataProvider()
    
    # Get the first agent
    agents = provider.get_agents()
    agent_id = str(agents[0].id)
    
    # Update data
    update_data = {
        "name": "Updated Agent Name",
        "description": "Updated description",
        "config": {"test": "value"},
    }
    
    # Update the agent - returns AgentVersion
    updated_agent_version = provider.update_agent(agent_id, update_data)
    
    # Check that it's an AgentVersion model
    assert isinstance(updated_agent_version, AgentVersion)
    
    # Check that the agent ID didn't change
    assert str(updated_agent_version.agent.id) == agent_id
    
    # Check that the version was created
    assert updated_agent_version.version is not None
    assert updated_agent_version.version.number >= 1
    assert updated_agent_version.version.created_at is not None


def test_test_data_provider_get_agent() -> None:
    """Test that the TestDataProvider can get a single agent with version."""
    provider = TestDataProvider()
    
    # Get all agents
    agents = provider.get_agents()
    agent_id = str(agents[0].id)
    
    # Get specific agent
    agent_version = provider.get_agent(agent_id)
    
    # Check that it's an AgentVersion model
    assert agent_version is not None
    assert isinstance(agent_version, AgentVersion)
    assert isinstance(agent_version.agent, Agent)
    assert str(agent_version.agent.id) == agent_id
    assert agent_version.version is not None


def test_test_data_provider_add_test_agent() -> None:
    """Test that the TestDataProvider can add test agents."""
    provider = TestDataProvider()
    
    # Add a test agent
    test_agent_data = {
        "id": "12345678-abcd-1234-abcd-123456789abc",
        "name": "Test Agent",
        "description": "A test agent",
        "type": "chat",
        "status": "CREATED",
        "isGlobalAgent": False,
        "currentVersionId": "12345678-abcd-1234-abcd-123456789abd",
        "created_at": "2024-01-01T00:00:00Z",
        "created_by": "test",
        "modified_at": "2024-01-01T00:00:00Z",
        "modified_by": "test",
        "agent_config": {}
    }
    
    added_agent = provider.add_test_agent(test_agent_data)
    
    # Check that it's an Agent model
    assert isinstance(added_agent, Agent)
    assert str(added_agent.id) == "12345678-abcd-1234-abcd-123456789abc"
    assert added_agent.name == "Test Agent"
    
    # Verify we can retrieve it
    retrieved_agent_version = provider.get_agent("12345678-abcd-1234-abcd-123456789abc")
    assert retrieved_agent_version is not None
    assert str(retrieved_agent_version.agent.id) == "12345678-abcd-1234-abcd-123456789abc"
