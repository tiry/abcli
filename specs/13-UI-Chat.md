# UI Chat Refactoring

## Overview

The current UI for chat (ab_cli/abui/views/chat.py) is using a basic form rather than using a dedicated chat component like chat_message. This specification outlines improvements to enhance the chat user interface.

## Requirements

1. Use the dedicated Streamlit chat_message component for displaying messages
2. Display the tools associated with the agent currently selected (visual cue that the tools are activated)
3. Allow sending a JSON task to task agents
4. Dynamically switch between chat and JSON input modes based on agent type

## Implementation Details

### 1. User Interface Components

#### 1.1 Chat Interface

For agents of type "chat" or "rag", we'll implement a chat interface with:
- Streamlit `st.chat_message()` component for message display
- Chat history with properly styled user and assistant messages
- Simple text input for the user to send messages

```python
# Example chat message display
with st.chat_message("user"):
    st.markdown(f"{message['content']}")

with st.chat_message("assistant"):
    st.markdown(f"{response}")
```

#### 1.2 Task Interface

For agents of type "task", we'll implement a JSON-based interface with:
- JSON editor with schema validation based on the agent's inputSchema
- Toggle option to switch to a chat-like interface if preferred
- Structured display of responses

#### 1.3 Tool Display

- Display tools associated with the agent as simple badges/icons
- Place tools in a distinct section near the agent information
- Each tool will be displayed with its name and a visual indicator

### 2. Logic Flow

1. Determine agent type when selected (chat, task, rag)
2. Based on type:
   - If "task" and has inputSchema: Show JSON editor with schema validation
   - Otherwise: Show chat interface
3. Display any tools the agent has as visual indicators
4. Process messages appropriately based on the agent type and user interface mode

### 3. Response Handling

- Text responses: Display in chat_message component
- Structured/JSON responses: Display in formatted JSON viewer
- Tool responses: Highlight which tools were used in the response

### 4. Detailed Component Implementations

#### 4.1 Chat Message Component

```python
def display_chat_history(chat_history, agent_name):
    """Display chat history using st.chat_message components."""
    for message in chat_history:
        role = message["role"]
        content = message["content"]
        
        # Use appropriate role for chat message component
        display_role = "user" if role == "user" else "assistant"
        
        with st.chat_message(display_role):
            st.markdown(content)
```

#### 4.2 JSON Editor Component

```python
def json_task_editor(input_schema):
    """Create a JSON editor with schema validation."""
    # Show a schema-based editor for task input
    default_json = {}
    for prop, details in input_schema.get("properties", {}).items():
        # Create default values based on type
        if details.get("type") == "string":
            default_json[prop] = ""
        elif details.get("type") == "number":
            default_json[prop] = 0
        # Add more types as needed

    json_str = st.text_area(
        "Task Input (JSON):",
        value=json.dumps(default_json, indent=2),
        height=200
    )
    
    # Validate JSON against schema
    try:
        json_data = json.loads(json_str)
        # TODO: Add proper JSON schema validation
        return json_data
    except json.JSONDecodeError:
        st.error("Invalid JSON format")
        return None
```

#### 4.3 Tool Display Component

```python
def display_agent_tools(agent):
    """Display the tools associated with an agent."""
    tools = agent.get("agent_config", {}).get("tools", [])
    
    if not tools:
        return
    
    st.subheader("Available Tools")
    for tool in tools:
        with st.container():
            # Create a visual tool badge
            tool_type = tool.get("type", "unknown")
            tool_name = tool.get("name", "Unnamed Tool")
            
            # Display as a badge-like component
            st.markdown(f"**{tool_name}** `{tool_type}`")
            if "description" in tool:
                st.caption(tool["description"])
```

### 5. Data Flow

1. User selects an agent
2. System determines agent type and displays appropriate interface
3. User inputs message (text or JSON)
4. System processes input based on agent type:
   - Chat: Send as text message
   - Task: Send as JSON structure if using JSON editor
5. Display response using appropriate component based on content type

## Testing Considerations

- Test with different agent types (chat, task, rag)
- Test with agents that have tools configured
- Test with agents that have inputSchema
- Test both text and structured responses
- Verify proper display of chat history

## Implementation Plan

1. Update the `chat_interface()` function to use st.chat_message
2. Create new `task_interface()` function for task agents
3. Implement tool display component
4. Implement logic to switch between interfaces based on agent type
5. Enhance response handling for different content types
6. Update the UI to reflect the new components and interactions
7. Create tests to verify the new functionality