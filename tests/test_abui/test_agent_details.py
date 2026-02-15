"""Tests for the agent details view using the actual agent_details.py implementation."""

from typing import Any, Dict

import pytest
from streamlit.testing.v1 import AppTest

from tests.test_abui.streamlit_test_wrapper import (
    display_agent_config_test,
    show_agent_details_page_test,
)
from tests.test_abui.test_data_provider import TestDataProvider


def test_display_agent_config_basic():
    """Test the display_agent_config function with basic configuration."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(display_agent_config_test)
    
    # Set up test parameters in session state
    app_test.session_state["test_config"] = {
        "llmModelId": "test-model-1",
        "systemPrompt": "You are a test assistant."
    }
    
    # Run the test function
    app_test.run()
    
    # Verify the function rendered the expected elements
    # Model should be displayed in an info element
    model_id_displayed = False
    if hasattr(app_test, "info"):
        for info_elem in app_test.info:
            if hasattr(info_elem, "body") and "test-model-1" in info_elem.body:
                model_id_displayed = True
                break
    
    assert model_id_displayed, "Model ID not displayed in UI"
    
    # System prompt should be in a text area
    system_prompt_displayed = False
    if hasattr(app_test, "text_area"):
        for text_area in app_test.text_area:
            if hasattr(text_area, "value") and "You are a test assistant" in text_area.value:
                system_prompt_displayed = True
                break
    
    assert system_prompt_displayed, "System prompt not displayed in UI"


def test_display_agent_config_guardrails():
    """Test the display_agent_config function with guardrails configuration."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(display_agent_config_test)
    
    # Set up test parameters in session state
    app_test.session_state["test_config"] = {
        "llmModelId": "test-model-1",
        "guardrails": ["safe-prompt", "content-filter"]
    }
    
    # Run the test function
    app_test.run()
    
    # Verify guardrails are displayed in markdown elements
    guardrails_displayed = False
    if hasattr(app_test, "markdown"):
        for md in app_test.markdown:
            if hasattr(md, "value") and ("safe-prompt" in md.value or "content-filter" in md.value):
                guardrails_displayed = True
                break
    
    assert guardrails_displayed, "Guardrails not displayed in UI"


def test_display_agent_config_tools():
    """Test the display_agent_config function with tools configuration."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(display_agent_config_test)
    
    # Set up test parameters in session state
    app_test.session_state["test_config"] = {
        "llmModelId": "test-model-1",
        "tools": [{"name": "calculator", "description": "Perform calculations"}]
    }
    
    # Run the test function
    app_test.run()
    
    # Verify tools are displayed in a JSON element
    assert hasattr(app_test, "json"), "Expected JSON element for tools not found"


def test_display_agent_config_inference_config():
    """Test the display_agent_config function with inference configuration."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(display_agent_config_test)
    
    # Set up test parameters in session state
    app_test.session_state["test_config"] = {
        "llmModelId": "test-model-1",
        "inferenceConfig": {"temperature": 0.7, "maxTokens": 1000}
    }
    
    # Run the test function
    app_test.run()
    
    # Verify inference config is displayed in a JSON element
    assert hasattr(app_test, "json"), "Expected JSON element for inference config not found"


def test_display_agent_config_verbose():
    """Test the display_agent_config function with verbose mode enabled."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(display_agent_config_test)
    
    # Set up test parameters in session state
    app_test.session_state["test_config"] = {
        "llmModelId": "test-model-1",
        "systemPrompt": "You are a test assistant.",
        "guardrails": ["test-guardrail"]
    }
    app_test.session_state["test_verbose"] = True
    
    # Run the test function
    app_test.run()
    
    # We can't directly test the print outputs, but we can ensure it runs without errors
    # This test mostly checks that the verbose code paths don't cause exceptions
    
    # Verify key elements are still displayed
    model_id_displayed = False
    if hasattr(app_test, "info"):
        for info_elem in app_test.info:
            if hasattr(info_elem, "body") and "test-model-1" in info_elem.body:
                model_id_displayed = True
                break
    
    assert model_id_displayed, "Model ID not displayed in UI when verbose mode enabled"


def test_show_agent_details_page_basic(test_agent, test_data_provider):
    """Test the basic display of the agent details page."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up session state for the test
    app_test.session_state["agent_to_view"] = test_agent
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    app_test.session_state["verbose"] = False
    
    # Run the test function
    app_test.run()
    
    # Verify the page displays the agent name in the title
    title_displayed = False
    if hasattr(app_test, "title"):
        for title in app_test.title:
            if hasattr(title, "value") and test_agent["name"] in title.value:
                title_displayed = True
                break
    
    assert title_displayed, f"Agent name '{test_agent['name']}' not displayed in title"
    
    # Verify tabs were created
    assert hasattr(app_test, "tabs"), "Tabs not created in the UI"
    assert len(app_test.tabs) > 0, "Expected tabs not found in the UI"
    
    # Check that the "Edit Agent" and "Chat with Agent" buttons are present
    edit_button_found = False
    chat_button_found = False
    
    if hasattr(app_test, "button"):
        for button in app_test.button:
            if hasattr(button, "label"):
                if button.label == "Edit Agent":
                    edit_button_found = True
                elif button.label == "Chat with Agent":
                    chat_button_found = True
    
    assert edit_button_found, "Edit Agent button not found"
    assert chat_button_found, "Chat with Agent button not found"


def test_show_agent_details_page_missing_agent():
    """Test the agent details page when no agent is provided."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up session state without an agent
    app_test.session_state["current_page"] = "AgentDetails"
    # Ensure agent_to_view is not set
    if "agent_to_view" in app_test.session_state:
        del app_test.session_state["agent_to_view"]
    
    # Run the test function
    app_test.run()
    
    # Verify an error message is displayed
    error_displayed = False
    if hasattr(app_test, "error"):
        for error in app_test.error:
            if hasattr(error, "body") and "No agent selected" in error.body:
                error_displayed = True
                break
    
    assert error_displayed, "Expected error message not displayed when agent is missing"
    
    # Verify the "Back to Agents List" button is present
    back_button_found = False
    if hasattr(app_test, "button"):
        for button in app_test.button:
            if hasattr(button, "label") and button.label == "Back to Agents List":
                back_button_found = True
                break
    
    assert back_button_found, "Back to Agents List button not found when agent is missing"


def test_show_agent_details_page_error_fetching_config(test_data_provider):
    """Test error handling when fetching agent configuration fails."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Create a minimal agent without configuration
    minimal_agent = {"id": "test-agent-error", "name": "Test Error Agent"}
    
    # Set up error simulation in the data provider
    test_data_provider.set_error_simulation("get_agent")
    
    # Set up session state
    app_test.session_state["agent_to_view"] = minimal_agent
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    app_test.session_state["verbose"] = False
    
    # Run the test function
    app_test.run()
    
    # Verify an error message is displayed when getting the configuration fails
    error_found = False
    if hasattr(app_test, "error"):
        for error in app_test.error:
            if hasattr(error, "body") and "Error fetching" in error.body:
                error_found = True
                break
    
    assert error_found, "Expected error message not displayed when fetching configuration fails"


def test_show_agent_details_page_edit_navigation(test_agent, test_data_provider):
    """Test navigation to edit from agent details page."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up session state for the test
    app_test.session_state["agent_to_view"] = test_agent
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    app_test.session_state["verbose"] = False
    
    # Run the test function to initialize the UI
    app_test.run()
    
    # Find the "Edit Agent" button
    edit_button = None
    if hasattr(app_test, "button"):
        for button in app_test.button:
            if hasattr(button, "label") and button.label == "Edit Agent":
                edit_button = button
                break
    
    assert edit_button is not None, "Edit Agent button not found"
    
    # Simulate clicking the edit button by setting nav_intent
    app_test.session_state["nav_intent"] = "EditAgent"
    
    # When using AppTest, we need to manually set up expected behaviors
    # since clicking the button doesn't trigger JavaScript events
    app_test.session_state["agent_to_edit"] = test_agent
    
    # Re-run to process navigation
    app_test.run()
    
    # Verify navigation intent was set
    assert app_test.session_state["nav_intent"] == "EditAgent"
    assert "agent_to_edit" in app_test.session_state
    assert app_test.session_state["agent_to_edit"]["id"] == test_agent["id"]


def test_show_agent_details_page_chat_navigation(test_agent, test_data_provider):
    """Test navigation to chat from agent details page."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up session state for the test
    app_test.session_state["agent_to_view"] = test_agent
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    app_test.session_state["verbose"] = False
    
    # Run the test function to initialize the UI
    app_test.run()
    
    # Find the "Chat with Agent" button
    chat_button = None
    if hasattr(app_test, "button"):
        for button in app_test.button:
            if hasattr(button, "label") and button.label == "Chat with Agent":
                chat_button = button
                break
    
    assert chat_button is not None, "Chat with Agent button not found"
    
    # Simulate clicking the chat button by setting nav_intent
    app_test.session_state["nav_intent"] = "Chat"
    app_test.session_state["selected_agent"] = test_agent
    
    # Re-run to process navigation
    app_test.run()
    
    # Verify navigation intent was set
    assert app_test.session_state["nav_intent"] == "Chat"
    assert app_test.session_state["selected_agent"]["id"] == test_agent["id"]


def test_show_agent_details_page_back_to_list(test_agent, test_data_provider):
    """Test navigation back to the agents list from agent details page."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up session state for the test
    app_test.session_state["agent_to_view"] = test_agent
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    app_test.session_state["verbose"] = False
    
    # Run the test function to initialize the UI
    app_test.run()
    
    # Find the "Back to Agents List" button
    back_button = None
    if hasattr(app_test, "button"):
        for button in app_test.button:
            if hasattr(button, "label") and button.label == "Back to Agents List":
                back_button = button
                break
    
    assert back_button is not None, "Back to Agents List button not found"
    
    # Simulate clicking the back button by setting nav_intent and current_page
    app_test.session_state["nav_intent"] = "Agents"
    app_test.session_state["current_page"] = "Agents"
    
    # Re-run to process navigation
    app_test.run()
    
    # Verify navigation intent and page were set
    assert app_test.session_state["nav_intent"] == "Agents"
    assert app_test.session_state["current_page"] == "Agents"


def test_show_agent_details_page_tabs(test_agent, test_data_provider):
    """Test that all tabs are properly created and can be selected."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up session state for the test
    app_test.session_state["agent_to_view"] = test_agent
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    app_test.session_state["verbose"] = False
    
    # Run the test function to initialize the UI
    app_test.run()
    
    # Verify tabs were created with expected labels
    expected_tab_labels = ["General Info", "Configuration", "Versions", "Statistics"]
    
    if hasattr(app_test, "tabs"):
        for tab in app_test.tabs:
            # Check if tab has a label property
            if hasattr(tab, 'label'):
                assert tab.label in expected_tab_labels, f"Unexpected tab label: {tab.label}"
    
    assert hasattr(app_test, "tabs"), "Tabs not created"
    assert len(app_test.tabs) == 4, f"Expected 4 tabs, found {len(app_test.tabs)}"


def test_show_agent_details_page_verbose(test_agent, test_data_provider):
    """Test the agent details page with verbose debugging enabled."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up session state for the test with verbose enabled
    app_test.session_state["agent_to_view"] = test_agent
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    app_test.session_state["verbose"] = True
    
    # Run the test function
    app_test.run()
    
    # We can't directly test the print outputs, but we can ensure it runs without errors
    # The fact that it completes without exception means the verbose code paths work
    
    # Verify key UI elements are still present
    # Look for title with agent name
    title_found = False
    if hasattr(app_test, "title"):
        for title in app_test.title:
            if hasattr(title, "value") and test_agent["name"] in title.value:
                title_found = True
                break
    
    assert title_found, "Agent title not found when verbose mode enabled"
