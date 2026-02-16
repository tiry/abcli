"""Chat page for the Agent Builder UI."""

import json
from typing import Any, cast

import streamlit as st

from ab_cli.abui.providers.provider_factory import get_data_provider


def show_chat_page() -> None:
    """Show the chat interface."""
    st.title("Agent Builder Chat")

    config = st.session_state.get("config", {})
    data_provider = get_data_provider(config)
    agents = data_provider.get_agents()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}

    # Initialize if needed
    if "selected_agent" not in st.session_state:
        st.session_state.selected_agent = None

    # Clear agent selection if user explicitly returns to agent selection
    if "return_to_chat" in st.session_state and st.session_state.return_to_chat:
        st.session_state.selected_agent = None
        st.session_state.return_to_chat = False

    # Agent Selection
    if st.session_state.selected_agent is None:
        st.subheader("Select an Agent to Chat With")

        agent_names = [agent["name"] for agent in agents]
        agent_ids = [agent["id"] for agent in agents]

        selected_index = st.selectbox(
            "Choose an agent:", range(len(agent_names)), format_func=lambda i: agent_names[i]
        )

        if st.button("Chat with Agent"):
            selected_agent = next((a for a in agents if a["id"] == agent_ids[selected_index]), None)
            if selected_agent:
                st.session_state.selected_agent = selected_agent

                # Initialize chat history for this agent if needed
                if selected_agent["id"] not in st.session_state.chat_history:
                    st.session_state.chat_history[selected_agent["id"]] = []

                st.rerun()
    else:
        # Show chat interface with selected agent
        agent = st.session_state.selected_agent
        agent_type = agent.get("type", "chat").lower()

        if st.button("← Back to Agent Selection"):
            st.session_state.selected_agent = None
            st.rerun()

        # Display agent tools if available
        display_agent_tools(agent)

        # Different interfaces based on agent type
        if agent_type == "task":
            show_task_agent_interface(agent)
        else:
            show_chat_agent_interface(agent)


def show_chat_agent_interface(agent: dict[str, Any]) -> None:
    """Show the chat interface for chat and RAG agents."""
    agent_id = agent["id"]
    st.subheader(f"Chat with {agent['name']}")

    # Initialize or get chat history
    if agent_id not in st.session_state.chat_history:
        st.session_state.chat_history[agent_id] = []

    chat_history = st.session_state.chat_history[agent_id]

    # Display chat history
    display_chat_history(chat_history)

    # Chat input
    user_message = st.chat_input("Type a message...")
    if user_message:
        # Add user message to chat history
        chat_history.append({"role": "user", "content": user_message})

        # Simulate agent response (in a real app, this would call the API)
        config = st.session_state.get("config", {})
        data_provider = get_data_provider(config)

        try:
            agent_type = agent.get("type", "chat")
            response = data_provider.invoke_agent(agent_id, user_message, agent_type=agent_type)

            # Add agent response to chat history
            chat_history.append({"role": "assistant", "content": response})

            # Force UI refresh
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")


def show_task_agent_interface(agent: dict[str, Any]) -> None:
    """Show the task interface for task agents."""
    agent_id = agent["id"]
    st.subheader(f"Task Agent: {agent['name']}")

    # Check if agent has full configuration loaded
    agent_config = agent.get("agent_config", {})

    # If agent_config is missing or empty, load full agent details
    if not agent_config:
        config = st.session_state.get("config", {})
        data_provider = get_data_provider(config)

        try:
            with st.spinner("Loading agent configuration..."):
                full_agent = data_provider.get_agent(agent_id)
                if full_agent and "agent_config" in full_agent:
                    # Update session state with full agent details
                    st.session_state.selected_agent = full_agent
                    agent = full_agent
                    agent_config = full_agent.get("agent_config", {})
                else:
                    st.error("Failed to load agent configuration")
                    return
        except Exception as e:
            st.error(f"Error loading agent details: {e}")
            return

    input_schema = agent_config.get("inputSchema", {})

    if not input_schema:
        st.warning("This task agent doesn't have an input schema defined.")
        return

    # Initialize or get chat history
    if agent_id not in st.session_state.chat_history:
        st.session_state.chat_history[agent_id] = []

    chat_history = st.session_state.chat_history[agent_id]

    # Display chat history
    display_chat_history(chat_history)

    # Display task input editor
    st.markdown("### Task Input")
    task_input, has_errors = json_task_editor(input_schema)

    # Disable button if there are validation errors
    if st.button("Submit Task", disabled=has_errors) and task_input:
        # Add task to chat history
        if agent_id not in st.session_state.chat_history:
            st.session_state.chat_history[agent_id] = []

        # Add formatted input as user message
        st.session_state.chat_history[agent_id].append(
            {"role": "user", "content": json.dumps(task_input, indent=2)}
        )

        # Simulate task execution (in a real app, call the API)
        config = st.session_state.get("config", {})
        data_provider = get_data_provider(config)

        try:
            # Use the standard invoke_agent method for task agents with agent_type
            agent_type = agent.get("type", "task")

            with st.spinner("Executing task..."):
                response = data_provider.invoke_agent(
                    agent_id, json.dumps(task_input), agent_type=agent_type
                )

            # Add response to chat history
            st.session_state.chat_history[agent_id].append(
                {"role": "assistant", "content": response}
            )

            # Force UI refresh
            st.rerun()
        except Exception as e:
            st.error(f"Error: {str(e)}")


def display_chat_history(chat_history: list[dict[str, str]]) -> None:
    """Display chat history using st.chat_message components.

    Args:
        chat_history: List of message dictionaries with role and content.
    """
    for message in chat_history:
        role = message["role"]
        content = message["content"]

        with st.chat_message(role):
            # Check if content looks like JSON
            try:
                if content.strip().startswith("{") and content.strip().endswith("}"):
                    # Try to parse and format JSON
                    json_data = json.loads(content)
                    st.json(json_data)
                else:
                    # Regular text
                    st.write(content)
            except (json.JSONDecodeError, AttributeError):
                # Not valid JSON or not a string, display as is
                st.write(content)


def json_task_editor(input_schema: dict[str, Any]) -> tuple[dict[str, Any] | None, bool]:
    """Create a JSON editor with schema validation.

    Args:
        input_schema: JSON schema for task input validation.

    Returns:
        Tuple of (validated JSON object or None, has_errors boolean)
    """
    # Create default JSON object based on schema
    default_json: dict[str, Any] = {}
    if "properties" in input_schema:
        for prop, prop_schema in input_schema["properties"].items():
            # Set sensible defaults based on type
            prop_type = prop_schema.get("type")
            if prop_type == "string":
                default_json[prop] = ""
            elif prop_type == "number" or prop_type == "integer":
                default_json[prop] = 0
            elif prop_type == "boolean":
                default_json[prop] = False
            elif prop_type == "array":
                default_json[prop] = []
            elif prop_type == "object":
                default_json[prop] = {}

    # Add required field indicators
    required_fields = input_schema.get("required", [])

    if required_fields:
        st.caption("Fields marked with * are required")

    json_str = st.text_area("JSON Input:", value=json.dumps(default_json, indent=2), height=200)

    # Validate JSON format
    try:
        task_input = json.loads(json_str)
    except json.JSONDecodeError as e:
        st.error(f"Invalid JSON format: {str(e)}")
        return None, True  # has errors

    # Validate required fields
    validation_errors = []
    for field in required_fields:
        if field not in task_input or task_input[field] == "":
            validation_errors.append(f"Field '{field}' is required.")

    # Show validation errors if any
    if validation_errors:
        for error in validation_errors:
            st.error(error)
        return None, True  # has errors

    return cast(dict[str, Any], task_input), False  # no errors


def display_agent_tools(agent: dict[str, Any]) -> None:
    """Display agent tools in an expandable section.

    Args:
        agent: The agent data.
    """
    tools = agent.get("agent_config", {}).get("tools", [])

    if tools:
        with st.expander("Agent Tools"):
            for tool in tools:
                tool_name = tool.get("name", "Unnamed Tool")
                tool_type = tool.get("type", "unknown")
                tool_desc = tool.get("description", "No description")

                st.markdown(f"**{tool_name}** ({tool_type})")
                st.markdown(f"{tool_desc}")
                st.markdown("---")
