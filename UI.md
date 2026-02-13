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

The Chat page lets you interact with your agents:
- Send messages to an agent and see its responses
- View the chat history
- Clear the conversation
- Select a different agent to chat with

## Navigation

The UI uses a consistent navigation pattern:
- The sidebar contains main navigation buttons for Agents and Chat
- The currently selected page is highlighted
- The UI maintains your state as you navigate between pages

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

3. **Error Handling**:
   - Added robust error handling for API interactions
   - Improved feedback for configuration issues
   - Enhanced model information extraction with multiple fallback strategies

## Troubleshooting

### Configuration Issues

If you encounter configuration errors:
- Ensure your `config.yaml` file exists and is properly formatted
- Check the API endpoint and credentials
- Try running the CLI commands directly to verify your configuration works

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