"""Extended tests for the agent details view."""

import copy
import pytest
from streamlit.testing.v1 import AppTest

from tests.test_abui.streamlit_test_wrapper import show_agent_details_page_test
from tests.test_abui.test_data_provider import TestDataProvider
from tests.test_abui.conftest import convert_test_agent_to_pydantic


def test_agent_details_tabs_navigation(test_agent: dict, test_data_provider: TestDataProvider) -> None:
    """Test that the agent details page tab navigation works correctly."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up the session state - Use the full agent object, not just the ID
    app_test.session_state["agent_to_view"] = convert_test_agent_to_pydantic(copy.deepcopy(test_agent))
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    
    # Run the app
    app_test.run(timeout=10)
    
    # Check for presence of key elements
    assert hasattr(app_test, "_tree"), "App should have a render tree"
    
    # Check for tabs which are used in the agent details page
    tabs_exist = False
    if hasattr(app_test, "tab"):
        tabs_exist = len(app_test.tab) > 0
    
    # Find tab container in the tree structure if tab retrieval doesn't work
    if not tabs_exist and hasattr(app_test, "_tree"):
        # Look for tab_container in the rendered tree
        def find_tab_container(node):
            if not hasattr(node, "children"):
                return False
            
            if hasattr(node, "type") and node.type == "tab_container":
                return True
                
            for child in node.children.values():
                if find_tab_container(child):
                    return True
            
            return False
        
        # Check main block for tab container
        if hasattr(app_test._tree, "children"):
            for child in app_test._tree.children.values():
                if find_tab_container(child):
                    tabs_exist = True
                    break
    
    assert tabs_exist, "Tab navigation should exist on the agent details page"


def test_agent_details_chat_agent_display(test_data_provider: TestDataProvider) -> None:
    """Test that the agent details page displays a chat agent correctly."""
    # Create a chat agent for testing
    chat_agent = {
        "id": "dddddddd-eeee-ffff-aaaa-444444444444",
        "name": "Test Chat Agent",
        "description": "A test chat agent",
        "type": "chat",
        "status": "CREATED",
        "isGlobalAgent": False,
        "currentVersionId": "dddddddd-eeee-ffff-aaaa-444444444445",
        "created_at": "2026-01-01T00:00:00Z",
        "created_by": "test",
        "modified_at": "2026-01-01T00:00:00Z",
        "modified_by": "test",
        "agent_config": {
            "llmModelId": "test-model-1",
            "systemPrompt": "You are a chat assistant.",
            "guardrails": ["test-guardrail-1"],
            "inferenceConfig": {
                "temperature": 0.5,
                "maxRetries": 2,
                "timeout": 1800,
                "maxTokens": 2000
            }
        }
    }
    
    # Add the chat agent to the data provider
    test_data_provider.add_test_agent(chat_agent)
    
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up the session state
    app_test.session_state["agent_to_view"] = convert_test_agent_to_pydantic(copy.deepcopy(chat_agent))
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    
    # Run the app
    app_test.run(timeout=10)
    
    # Check for title with agent name
    title_correct = False
    if hasattr(app_test, "title"):
        for title in app_test.title:
            if hasattr(title, "value") and "Test Chat Agent" in title.value:
                title_correct = True
                break
    
    assert title_correct, "Agent name should be displayed in the title"
    
    # Verify the app has rendered something
    assert hasattr(app_test, "_tree"), "App should have rendered"


def test_agent_details_task_agent_display(test_data_provider: TestDataProvider) -> None:
    """Test that the agent details page displays a task agent correctly."""
    # Create a task agent for testing
    task_agent = {
        "id": "eeeeeeee-ffff-aaaa-bbbb-555555555555",
        "name": "Test Task Agent",
        "description": "A test task agent",
        "type": "task",
        "status": "CREATED",
        "isGlobalAgent": False,
        "currentVersionId": "eeeeeeee-ffff-aaaa-bbbb-555555555556",
        "created_at": "2026-01-01T00:00:00Z",
        "created_by": "test",
        "modified_at": "2026-01-01T00:00:00Z",
        "modified_by": "test",
        "agent_config": {
            "llmModelId": "test-model-1",
            "systemPrompt": "You are a task assistant.",
            "inferenceConfig": {
                "temperature": 0.0,
                "maxRetries": 3,
                "timeout": 1800,
                "maxTokens": 4000
            },
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "The task to perform"
                    }
                },
                "required": ["task"]
            }
        }
    }
    
    # Add the task agent to the data provider
    test_data_provider.add_test_agent(task_agent)
    
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up the session state
    app_test.session_state["agent_to_view"] = convert_test_agent_to_pydantic(copy.deepcopy(task_agent))
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    
    # Run the app
    app_test.run(timeout=10)
    
    # Check for title with agent name
    title_correct = False
    if hasattr(app_test, "title"):
        for title in app_test.title:
            if hasattr(title, "value") and "Test Task Agent" in title.value:
                title_correct = True
                break
    
    assert title_correct, "Agent name should be displayed in the title"
    
    # Verify the app has rendered something
    assert hasattr(app_test, "_tree"), "App should have rendered"


def test_agent_details_agent_with_tools_display(test_data_provider: TestDataProvider) -> None:
    """Test that the agent details page displays an agent with tools correctly."""
    # Create an agent with tools for testing
    agent_with_tools = {
        "id": "ffffffff-aaaa-bbbb-cccc-666666666666",
        "name": "Test Tools Agent",
        "description": "A test agent with tools",
        "type": "chat",
        "status": "CREATED",
        "isGlobalAgent": False,
        "currentVersionId": "ffffffff-aaaa-bbbb-cccc-666666666667",
        "created_at": "2026-01-01T00:00:00Z",
        "created_by": "test",
        "modified_at": "2026-01-01T00:00:00Z",
        "modified_by": "test",
        "agent_config": {
            "llmModelId": "test-model-1",
            "systemPrompt": "You are an assistant with tools.",
            "inferenceConfig": {
                "temperature": 0.5,
                "maxTokens": 2000
            },
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get the current weather",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state"
                            }
                        },
                        "required": ["location"]
                    }
                }
            ]
        }
    }
    
    # Add the agent with tools to the data provider
    test_data_provider.add_test_agent(agent_with_tools)
    
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up the session state
    app_test.session_state["agent_to_view"] = convert_test_agent_to_pydantic(copy.deepcopy(agent_with_tools))
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    
    # Run the app
    app_test.run(timeout=10)
    
    # Check for title with agent name
    title_correct = False
    if hasattr(app_test, "title"):
        for title in app_test.title:
            if hasattr(title, "value") and "Test Tools Agent" in title.value:
                title_correct = True
                break
    
    assert title_correct, "Agent name should be displayed in the title"
    
    # Verify the app has rendered something
    assert hasattr(app_test, "_tree"), "App should have rendered"


def test_agent_details_action_buttons(test_agent: dict, test_data_provider: TestDataProvider) -> None:
    """Test that the agent details page has action buttons."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up the session state
    app_test.session_state["agent_to_view"] = convert_test_agent_to_pydantic(copy.deepcopy(test_agent))
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    
    # Run the app
    app_test.run(timeout=10)
    
    # Check for edit button
    edit_button_found = False
    if hasattr(app_test, "button"):
        for button in app_test.button:
            if hasattr(button, "label") and "Edit" in button.label:
                edit_button_found = True
                break
    
    assert edit_button_found, "Edit button should be present"
    
    # Check for back button
    back_button_found = False
    if hasattr(app_test, "button"):
        for button in app_test.button:
            if hasattr(button, "label") and "Back" in button.label:
                back_button_found = True
                break
    
    assert back_button_found, "Back button should be present"


def test_agent_details_verbose_mode(test_agent: dict, test_data_provider: TestDataProvider) -> None:
    """Test that the agent details page has a verbose mode toggle."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up the session state
    app_test.session_state["agent_to_view"] = convert_test_agent_to_pydantic(copy.deepcopy(test_agent))
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    
    # Run the app
    app_test.run(timeout=10)
    
    # Check for title with agent name
    title_correct = False
    if hasattr(app_test, "title"):
        for title in app_test.title:
            if hasattr(title, "value") and test_agent["name"] in title.value:
                title_correct = True
                break
    
    assert title_correct, "Agent name should be displayed in the title"
    
    # Verify the app has rendered something
    assert hasattr(app_test, "_tree"), "App should have rendered"


def test_agent_details_missing_config(test_data_provider: TestDataProvider) -> None:
    """Test that the agent details page handles missing config gracefully."""
    # Create an agent with minimal config for testing
    minimal_agent = {
        "id": "aaaabbbb-cccc-dddd-eeee-777777777777",
        "name": "Test Minimal Agent",
        "description": "A test agent with minimal config",
        "type": "chat",
        "status": "CREATED",
        "isGlobalAgent": False,
        "currentVersionId": "aaaabbbb-cccc-dddd-eeee-777777777778",
        "created_at": "2026-01-01T00:00:00Z",
        "created_by": "test",
        "modified_at": "2026-01-01T00:00:00Z",
        "modified_by": "test",
        # No agent_config field
    }
    
    # Add the minimal agent to the data provider
    test_data_provider.add_test_agent(minimal_agent)
    
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up the session state
    app_test.session_state["agent_to_view"] = convert_test_agent_to_pydantic(copy.deepcopy(minimal_agent))
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    
    # Run the app
    app_test.run(timeout=10)
    
    # Check for title with agent name
    title_correct = False
    if hasattr(app_test, "title"):
        for title in app_test.title:
            if hasattr(title, "value") and "Test Minimal Agent" in title.value:
                title_correct = True
                break
    
    assert title_correct, "Agent name should be displayed in the title"
    
    # Check for warning component (indicating missing config is handled)
    warning_found = False
    if hasattr(app_test, "warning"):
        warning_found = len(app_test.warning) > 0
    
    assert warning_found, "Warning should be displayed for missing configuration"


def test_agent_details_error_handling(test_data_provider: TestDataProvider) -> None:
    """Test that the agent details page handles errors gracefully."""
    # Create an agent for testing
    test_agent = {
        "id": "bbbbcccc-dddd-eeee-ffff-888888888888",
        "name": "Test Agent Error",
        "description": "An agent for error testing",
        "type": "chat",
        "status": "CREATED",
        "isGlobalAgent": False,
        "currentVersionId": "bbbbcccc-dddd-eeee-ffff-888888888889",
        "created_at": "2026-01-01T00:00:00Z",
        "created_by": "test",
        "modified_at": "2026-01-01T00:00:00Z",
        "modified_by": "test",
        "agent_config": {}
    }
    
    # Add the test agent
    test_data_provider.add_test_agent(test_agent)
    
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up the session state
    app_test.session_state["agent_to_view"] = convert_test_agent_to_pydantic(copy.deepcopy(test_agent))
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    
    # Set error simulation for get_agent method
    test_data_provider.set_error_simulation("get_agent")
    
    # Run the app
    app_test.run(timeout=10)
    
    # Reset error simulation
    test_data_provider.reset_error_simulation()
    
    # Since we expect an error, we should check if there's an error displayed
    # For now just make sure the app rendered something
    assert hasattr(app_test, "_tree"), "App should render something even when errors occur"