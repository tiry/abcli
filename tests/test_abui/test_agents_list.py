"""Tests for the agents list view."""

import pytest
from streamlit.testing.v1 import AppTest

from tests.test_abui.conftest import assert_element_contains_text, navigate_to_page
from tests.test_abui.streamlit_test_wrapper import show_agents_page_test
from tests.test_abui.test_data_provider import TestDataProvider


def test_agents_list_displays_page_title(test_data_provider: TestDataProvider) -> None:
    """Test that the agents list displays the page title correctly."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agents_page_test)
    
    # Set up the session state
    app_test.session_state["current_page"] = "Agents"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    
    # Use a simple value for agent_view_mode
    app_test.session_state["agent_view_mode"] = "Cards"
    
    # Run the app
    app_test.run(timeout=10)
    
    # Verify the page has loaded properly by checking that a title exists
    assert hasattr(app_test, 'title') and len(app_test.title) > 0
    
    # Get the title content - should contain "Agent Management"
    title_text = app_test.title[0].value if len(app_test.title) > 0 else ""
    assert "Agent Management" in title_text, "Page title doesn't contain 'Agent Management'"
    
    # Check that get_agents was called
    assert test_data_provider.get_call_count("get_agents") >= 1


def test_agents_list_has_create_button() -> None:
    """Test that the agents list has a create agent button."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agents_page_test)
    
    # Set up the session state
    app_test.session_state["current_page"] = "Agents"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["agent_view_mode"] = "Cards"
    
    # Run the app
    app_test.run(timeout=10)
    
    # Verify the Create Agent button exists
    create_button_found = False
    if hasattr(app_test, "button"):
        for button in app_test.button:
            if hasattr(button, "label") and "Create Agent" in button.label:
                create_button_found = True
                break
    
    assert create_button_found, "Create Agent button not found"


def test_agents_list_error_state(test_data_provider: TestDataProvider) -> None:
    """Test that the agents list shows an error message when there's an error fetching agents."""
    # Set up the data provider to simulate an error
    test_data_provider.set_error_simulation("get_agents")
    
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agents_page_test)
    
    # Set up the session state
    app_test.session_state["current_page"] = "Agents"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    app_test.session_state["agent_view_mode"] = "Cards"
    
    # Run the app
    app_test.run(timeout=10)
    
    # Check for error message in the UI
    error_displayed = False
    if hasattr(app_test, "error"):
        for error in app_test.error:
            if hasattr(error, "body") and "Error" in error.body:
                error_displayed = True
                break
    
    assert error_displayed, "Error message not displayed when fetching agents fails"


def test_create_agent_button_exists() -> None:
    """Test that the Create Agent button exists."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agents_page_test)
    
    # Set up the session state
    app_test.session_state["current_page"] = "Agents"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["agent_view_mode"] = "Cards"
    
    # Run the app
    app_test.run(timeout=10)
    
    # Verify the Create Agent button exists
    create_button_found = False
    if hasattr(app_test, "button"):
        for button in app_test.button:
            if hasattr(button, "label") and "Create Agent" in button.label:
                create_button_found = True
                break
    
    assert create_button_found, "Create Agent button not found"


def test_refresh_button_exists(test_data_provider: TestDataProvider) -> None:
    """Test that the refresh button exists."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agents_page_test)
    
    # Set up the session state
    app_test.session_state["current_page"] = "Agents"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    app_test.session_state["agent_view_mode"] = "Cards"
    
    # Run the app
    app_test.run(timeout=10)
    
    # Verify that the refresh button exists
    refresh_button_found = False
    if hasattr(app_test, "button"):
        for button in app_test.button:
            if hasattr(button, "label") and "Refresh Agent List" in button.label:
                refresh_button_found = True
                break
    
    assert refresh_button_found, "Refresh Agent List button not found"


def test_provider_data_access(test_data_provider: TestDataProvider) -> None:
    """Test that the provider is correctly accessed by the page."""
    # Reset call tracking
    test_data_provider.reset_call_tracking()
    
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agents_page_test)
    
    # Set up the session state
    app_test.session_state["current_page"] = "Agents"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    # Use a simple value
    app_test.session_state["agent_view_mode"] = "Cards"
    
    # Run the app, which should trigger data provider calls
    app_test.run(timeout=10)
    
    # Check that get_agents was called
    assert test_data_provider.get_call_count("get_agents") >= 1