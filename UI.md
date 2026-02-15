# Agent Builder UI

This document provides a brief overview of the Agent Builder UI, its features, and how to use it.

## Overview

The Agent Builder UI is a web-based interface for the Agent Builder CLI, providing a graphical way to manage and interact with agents. Built with Streamlit, it offers an intuitive way to create, edit, and chat with agents without having to use the command-line interface.

## Getting Started

To launch the UI, use the `ab ui` command:

```bash
ab ui
```

This will start the Streamlit server and open a browser window with the UI.

Additional options:
```bash
# Specify a configuration file
ab ui --config path/to/config.yaml

# Specify a port
ab ui --port 8501

# Don't open the browser automatically
ab ui --no-browser

# Launch UI with mock data provider (no API connection needed)
ab ui --mock
```

## Main Features

### Agent Management

The Agents page allows you to:
- View all your agents in a list
- Create new agents
- View detailed information about agents
- Edit existing agents
- Delete agents

### Agent Details

The Agent Details page provides comprehensive information about a selected agent:

- **General Info**: Basic agent properties like ID, name, type, and status
- **Configuration**: Detailed agent configuration including model, system prompt, and tools
- **Versions**: History of agent versions with metadata
- **Statistics**: Usage metrics (placeholder for future expansion)

Action buttons at the top of the page allow you to quickly:
- Edit the agent
- Start a chat with the agent

### Chat Interface

The Chat page lets you interact with your agents through two types of interfaces:

#### Chat Interface (for chat and RAG agents)
- Uses Streamlit's native `st.chat_message()` component for a modern chat experience
- Send messages to an agent and see its responses in a conversational format
- View the chat history with proper styling for user and assistant messages
- Displays any tools associated with the agent as visual indicators
- Automatically formats structured (JSON) responses for better readability
- Clear the conversation or change agents using buttons at the bottom

#### Task Interface (for task agents)
- Provides a JSON editor with schema validation based on the agent's inputSchema
- Shows required fields and validates input against the schema
- Displays task history using the same chat message component
- Presents structured responses in a properly formatted JSON viewer
- Shows any tools that the task agent has access to

Both interfaces display agent details and tools in expandable sections, making it easy to understand the agent's capabilities and configuration.

## Navigation

The UI uses a consistent navigation pattern:
- The sidebar contains main navigation buttons for Agents and Chat
- The currently selected page is highlighted
- The UI maintains your state as you navigate between pages

## Architecture and Design

The UI is built with a clean separation between UI components and data access logic:

1. **Data Provider Pattern**:
   - Clear separation between UI components and data access
   - Pluggable providers for different data sources
   - Consistent API for accessing agent data and services

2. **Provider Types**:
   - **CLI Data Provider**: Uses CLI commands to interact with the API
   - **Mock Data Provider**: Uses predefined data for development and testing

3. **Configuration**:
   - Configurable via `config.yaml` under the `ui` section
   - Switch between providers based on your needs

## UI Configuration

The UI behavior can be configured in the `config.yaml` file:

```yaml
# UI Configuration
ui:
  # Data Provider mode: "cli" or "mock"
  data_provider: "cli"  # Default
  
  # Directory for mock data (optional)
  mock_data_dir: "path/to/mock/data"  # Default: built-in data directory
```

## UI Improvements

The UI has been improved with the following key changes:

1. **Navigation Enhancement**:
   - Replaced radio buttons with proper action buttons for clearer navigation
   - Added visual indication of the current page (primary/secondary button styling)
   - Fixed duplicate navigation links issue in the sidebar

2. **Agent Details Layout**:
   - Action buttons moved to the top of the page for better visibility and usability
   - Removed redundant headings for cleaner information display
   - Organized information into clear, tabbed sections

3. **Enhanced Chat Interface**:
   - Upgraded to use Streamlit's `st.chat_message()` component for a more intuitive chat experience
   - Added automatic detection of agent type to provide appropriate interface (chat or task)
   - Implemented JSON editor with validation for task agents
   - Added visual indicators of agent tools to make capabilities transparent
   - Improved handling of structured (JSON) responses with proper formatting
   - Added task-specific interface for agents with inputSchema defined

4. **Error Handling**:
   - Added robust error handling for API interactions
   - Improved feedback for configuration issues
   - Enhanced model information extraction with multiple fallback strategies

5. **Code Organization**:
   - Improved modularity with Data Provider pattern
   - Eliminated code duplication across views
   - Better testability through clean separation of concerns

## UI Testing Framework

The UI comes with a comprehensive testing framework that allows automated testing of Streamlit components and functionality without requiring a browser.

### Testing Architecture

1. **Test Data Provider**:
   - Custom `TestDataProvider` class extends `MockDataProvider` for predictable test data
   - Dedicated test data files in `tests/test_abui/test_data/`
   - Support for tracking method calls and simulating errors

2. **Streamlit AppTest**:
   - Leverages Streamlit's built-in `AppTest` for headless testing
   - Simulates UI rendering and user interactions
   - Inspects rendered components and session state

3. **Helper Functions**:
   - Simplified assertions for common UI testing patterns
   - Navigation helpers to simulate user actions
   - Element inspection utilities

### Key Testing Features

- **Isolation**: Each test runs with a fresh Streamlit instance
- **Predictable Data**: Test data is separate from development mock data
- **Testable Components**: UI components are designed for testability
- **Session State Access**: Direct access to session state for verification
- **Error Simulation**: Ability to test error handling paths

### How to Run UI Tests

Run all UI tests:
```bash
python -m pytest tests/test_abui/
```

Run specific test file:
```bash
python -m pytest tests/test_abui/test_agents_list.py
```

Run individual test:
```bash
python -m pytest tests/test_abui/test_agents_list.py::test_agents_list_displays_all_agents
```

### Writing UI Tests

Example of a UI test:

```python
def test_agents_list_displays_all_agents(streamlit_app: AppTest, test_data_provider: TestDataProvider) -> None:
    """Test that the agents list displays all agents from the data provider."""
    # Run the app - this should be in the default Agents page
    streamlit_app.run()
    
    # Get the agents from the test data provider
    agents = test_data_provider.get_agents()
    
    # Check that get_agents was called
    assert test_data_provider.get_call_count("get_agents") >= 1
    
    # Verify that each agent is displayed in the page content
    for agent in agents:
        # Check for agent name in subheaders
        agent_found = False
        for subheader_element in streamlit_app.subheader:
            if hasattr(subheader_element, 'value') and agent["name"] == subheader_element.value:
                agent_found = True
                break
        assert agent_found, f"Agent '{agent['name']}' not found in UI"
```

### Test Fixtures

The test framework provides several fixtures:

- **test_data_provider**: An instance of `TestDataProvider` with test data
- **mock_config**: A mock configuration dictionary for testing
- **streamlit_app**: A configured Streamlit AppTest instance ready to run

These fixtures are defined in `tests/test_abui/conftest.py` and are automatically available in all UI tests.

### Debug Utilities

The testing framework includes developer utilities for debugging Streamlit components:

- **debug_app.py**: Provides utilities to inspect the Streamlit app structure
  - Shows available attributes and tree structure
  - Displays all text, markdown, and other content elements
  - Exposes session state keys and values

- **debug_elements.py**: Offers detailed inspection of specific UI elements
  - Examines element properties like type, value, and children
  - Shows the structure of markdown and subheader elements
  - Displays current test data from the provider

These files have debugging functions prefixed with `debug_` to exclude them from normal test runs. They're kept as developer tools for future UI work and can be manually run with:

```bash
python -m pytest tests/test_abui/test_debug_app.py::debug_app_content -v
python -m pytest tests/test_abui/test_debug_elements.py::debug_element_contents -v
```

Note that these are primarily debugging tools and not functional tests.

## Troubleshooting

### Configuration Issues

If you encounter configuration errors:
- Ensure your `config.yaml` file exists and is properly formatted
- Check the API endpoint and credentials
- Try running the CLI commands directly to verify your configuration works
- Verify UI configuration settings if using custom data provider settings

### Navigation Problems

If you experience navigation issues:
- Try refreshing the page
- Check if the API is responding (look at the API status indicator in the sidebar)
- Restart the UI with `ab ui`

### Chat Errors

If you have issues with the chat interface:
- Verify the agent is properly configured
- Check if the agent is available and operational
- Try invoking the agent directly via the CLI to check for API issues
- For task agents, ensure your JSON input matches the required schema
- For structured responses, if JSON display looks incorrect, try clearing browser cache

### Using Mock Data Provider

There are three ways to use the mock data provider for development or testing:

1. **Command-line flag (easiest):**
   ```bash
   # Launch UI with mock data provider
   ab ui --mock
   ```

2. **Environment variable:**
   ```bash
   # Set environment variable
   export AB_UI_DATA_PROVIDER=mock
   
   # Launch UI
   ab ui
   ```

3. **Configuration setting:**
   ```yaml
   # In config.yaml
   ui:
     data_provider: "mock"
   ```
   Then restart the UI with `ab ui`

The mock provider uses predefined data from JSON files in the `ab_cli/abui/data` directory, allowing you to test and develop the UI without needing a live API connection.

When in verbose mode, the UI will show "**UI Mode: MOCK**" in the sidebar to indicate it's using mock data.