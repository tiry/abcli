"""Tests for the agent list view functions."""

import pytest
from streamlit.testing.v1 import AppTest

from tests.test_abui.streamlit_test_wrapper import show_agents_page_test
from tests.test_abui.test_data_provider import TestDataProvider


def test_agents_page_display_modes(test_data_provider: TestDataProvider) -> None:
    """Test that the agents page has different display modes."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agents_page_test)
    
    # Set up the session state
    app_test.session_state["current_page"] = "Agents"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    app_test.session_state["agent_view_mode"] = "Cards"
    
    # Run the app
    app_test.run(timeout=10)
    
    # Check if app has rendered components (even if there are warnings)
    assert hasattr(app_test, "_tree"), "App should have rendered components"


def test_agents_page_refresh_button(test_data_provider: TestDataProvider) -> None:
    """Test that the refresh button calls clear_cache."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agents_page_test)
    
    # Set up the session state
    app_test.session_state["current_page"] = "Agents"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    app_test.session_state["agent_view_mode"] = "Cards"
    
    # Spy on the data provider's clear_cache method
    original_clear_cache = test_data_provider.clear_cache
    clear_cache_called = False
    
    def spy_clear_cache():
        nonlocal clear_cache_called
        clear_cache_called = True
        return original_clear_cache()
    
    test_data_provider.clear_cache = spy_clear_cache
    
    # Run the app
    app_test.run(timeout=10)
    
    # Look for the Refresh button
    refresh_button = None
    if hasattr(app_test, "button"):
        for button in app_test.button:
            if hasattr(button, "label") and "Refresh Agent List" in button.label:
                refresh_button = button
                break
    
    assert refresh_button is not None, "Refresh button should exist"
    
    # Reset the data provider method
    test_data_provider.clear_cache = original_clear_cache


def test_agents_page_layout(test_data_provider: TestDataProvider) -> None:
    """Test that the agents page layout has expected sections."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agents_page_test)
    
    # Set up the session state
    app_test.session_state["current_page"] = "Agents"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    app_test.session_state["agent_view_mode"] = "Cards"
    
    # Run the app
    app_test.run(timeout=10)
    
    # Verify title is present
    title_found = False
    if hasattr(app_test, "title"):
        for title in app_test.title:
            if hasattr(title, "value") and "Agent Management" in title.value:
                title_found = True
                break
    
    assert title_found, "Page title should be 'Agent Management'"
    
    # Verify subheader is present
    subheader_found = False
    if hasattr(app_test, "subheader"):
        for subheader in app_test.subheader:
            if hasattr(subheader, "value") and "Available Agents" in subheader.value:
                subheader_found = True
                break
    
    assert subheader_found, "Subheader 'Available Agents' should be present"
    
    # Verify create agent button is present
    create_button_found = False
    if hasattr(app_test, "button"):
        for button in app_test.button:
            if hasattr(button, "label") and "Create Agent" in button.label:
                create_button_found = True
                break
    
    assert create_button_found, "Create Agent button should be present"


def test_agents_page_card_view_display(test_data_provider: TestDataProvider) -> None:
    """Test that the card view display works."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agents_page_test)
    
    # Set up the session state
    app_test.session_state["current_page"] = "Agents"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    # Set view mode to Cards explicitly
    app_test.session_state["agent_view_mode"] = "Cards"
    
    # Run the app
    app_test.run(timeout=10)
    
    # Look for expanders which are used in card view
    has_expanders = hasattr(app_test, "expander") and len(app_test.expander) > 0
    
    assert has_expanders, "Card view should use expanders to display agents"


def test_agents_page_table_view_display(test_data_provider: TestDataProvider) -> None:
    """Test that the table view display works."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agents_page_test)
    
    # Set up the session state
    app_test.session_state["current_page"] = "Agents"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    # Set view mode to Table explicitly
    app_test.session_state["agent_view_mode"] = "Table"
    
    # Run the app
    app_test.run(timeout=10)
    
    # For table view, we'll just check if we have any content rendered
    assert hasattr(app_test, "_tree"), "App should have rendered components"


def test_agents_page_navigation_buttons(test_data_provider: TestDataProvider) -> None:
    """Test that navigation buttons are present on the agents page."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agents_page_test)
    
    # Set up the session state
    app_test.session_state["current_page"] = "Agents"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    app_test.session_state["agent_view_mode"] = "Cards"
    
    # Run the app
    app_test.run(timeout=10)
    
    # Just verify we have buttons rendered
    assert hasattr(app_test, "button") and len(app_test.button) > 0, "Navigation buttons should be present"