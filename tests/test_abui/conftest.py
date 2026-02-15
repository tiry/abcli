"""Test fixtures for Agent Builder UI tests."""

import os
from typing import Any, Dict, List, Optional

import pytest
from streamlit.testing.v1 import AppTest

from tests.test_abui.test_data_provider import TestDataProvider
from tests.test_abui.streamlit_test_wrapper import show_agents_page_test


def assert_element_contains_text(app_test: AppTest, element_type: str, text: str) -> bool:
    """Check if any element of the given type contains the specified text.
    
    Args:
        app_test: AppTest instance to check
        element_type: Type of element to check (e.g., "markdown", "text_input")
        text: Text to look for in the elements
        
    Returns:
        True if the text was found in any element of the specified type
    """
    # Get the list of elements of the given type
    elements = getattr(app_test, element_type, [])
    
    # Check if any element contains the text
    for element in elements:
        if hasattr(element, "value") and text in element.value:
            return True
        if hasattr(element, "body") and text in element.body:
            return True
    
    return False


def navigate_to_page(app_test: AppTest, page_name: str) -> None:
    """Simulate navigation to a different page in the app.
    
    Args:
        app_test: AppTest instance to use
        page_name: Name of the page to navigate to
    """
    # Set the current page and navigation intent
    app_test.session_state["current_page"] = page_name
    app_test.session_state["nav_intent"] = page_name
    
    # Run the app again to process the navigation
    app_test.run()


@pytest.fixture
def test_data_provider() -> TestDataProvider:
    """Create a TestDataProvider instance with test data.
    
    Returns:
        Initialized TestDataProvider instance
    """
    # Create data provider with test data directory
    test_data_dir = os.path.join(os.path.dirname(__file__), "test_data")
    provider = TestDataProvider(config=None, data_dir=test_data_dir)
    
    # Reset the provider state
    provider.reset_call_tracking()
    provider.reset_error_simulation()
    provider.clear_cache()
    
    return provider


@pytest.fixture
def mock_config() -> Dict[str, Any]:
    """Create a mock configuration for testing.
    
    Returns:
        Mock configuration dictionary
    """
    return {
        "api": {
            "endpoint": "https://test-api.example.com",
            "auth_url": "https://test-auth.example.com",
            "client_id": "test-client-id",
        },
        "ui": {
            "page_title": "Test Agent Builder UI",
            "mock": True,
            "mock_data_dir": os.path.join(os.path.dirname(__file__), "test_data"),
        },
    }


@pytest.fixture
def test_agent() -> Dict[str, Any]:
    """Create a test agent with full configuration.
    
    Returns:
        Test agent dictionary with configuration
    """
    return {
        "id": "test-agent-1",
        "name": "Test Chat Agent",
        "description": "A test chat agent for UI testing",
        "type": "chat",
        "status": "CREATED",
        "created_at": "2026-01-01T00:00:00Z",
        "agent_config": {
            "llmModelId": "test-model-1",
            "systemPrompt": "You are a test chat assistant.",
            "guardrails": ["test-guardrail-1", "test-guardrail-2"],
            "inferenceConfig": {
                "temperature": 0.5,
                "maxRetries": 2,
                "timeout": 1800,
                "maxTokens": 2000
            },
            "tools": []
        }
    }


@pytest.fixture
def streamlit_app(test_data_provider: TestDataProvider, mock_config: Dict[str, Any]) -> AppTest:
    """Create a preconfigured AppTest instance for testing the agents list view.
    
    Args:
        test_data_provider: TestDataProvider fixture
        mock_config: Mock configuration fixture
        
    Returns:
        Configured AppTest instance
    """
    # Create a new AppTest instance
    app_test = AppTest.from_function(show_agents_page_test)
    
    # Set up common session state
    app_test.session_state["current_page"] = "Agents"
    app_test.session_state["config"] = mock_config
    app_test.session_state["data_provider"] = test_data_provider
    
    return app_test
