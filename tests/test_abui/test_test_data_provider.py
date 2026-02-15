"""Tests for the TestDataProvider class."""

import pytest
import os
from typing import Dict, Any

from tests.test_abui.test_data_provider import TestDataProvider


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
    
    # Verify that the first agent has expected fields
    agent = agents[0]
    assert "id" in agent
    assert "name" in agent
    assert "type" in agent
    assert "status" in agent
    
    # Test that we can get models
    models = provider.get_models()
    assert len(models) > 0
    assert isinstance(models, list)
    
    # Test that we can get guardrails
    guardrails = provider.get_guardrails()
    assert len(guardrails) > 0
    assert isinstance(guardrails, list)


def test_test_data_provider_call_tracking() -> None:
    """Test that the TestDataProvider tracks method calls."""
    provider = TestDataProvider()
    
    # Reset call tracking
    provider.reset_call_tracking()
    
    # Make some calls
    provider.get_agents()
    provider.get_agents()
    provider.get_models()
    
    # Check call counts
    assert provider.get_call_count("get_agents") == 2
    assert provider.get_call_count("get_models") == 1
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
    
    # Create a test agent
    new_agent = {
        "name": "Test Agent",
        "description": "A test agent",
        "type": "chat",
    }
    
    # Create the agent
    created_agent = provider.create_agent(new_agent)
    
    # Check that the agent was created with expected fields
    assert "id" in created_agent
    assert created_agent["name"] == "Test Agent"
    assert created_agent["description"] == "A test agent"
    assert created_agent["type"] == "chat"
    assert "status" in created_agent
    assert "created_at" in created_agent


def test_test_data_provider_update_agent() -> None:
    """Test that the TestDataProvider can update agents."""
    provider = TestDataProvider()
    
    # Get the first agent
    agents = provider.get_agents()
    agent_id = agents[0]["id"]
    
    # Update data
    update_data = {
        "name": "Updated Agent Name",
        "description": "Updated description",
    }
    
    # Update the agent
    updated_agent = provider.update_agent(agent_id, update_data)
    
    # Check that the agent was updated
    assert updated_agent["name"] == "Updated Agent Name"
    assert updated_agent["description"] == "Updated description"
    
    # Check that the ID didn't change
    assert updated_agent["id"] == agent_id
    
    # Check that modified_at was added
    assert "modified_at" in updated_agent