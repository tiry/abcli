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

        # Get response from agent
        config = st.session_state.get("config", {})
        data_provider = get_data_provider(config)

        try:
            agent_type = agent.get("type", "chat")
            response_data = data_provider.invoke_agent(agent_id, user_message, agent_type=agent_type)

            # Store full response structure with metadata
            chat_history.append({
                "role": "assistant",
                "content": response_data.get("response_text", ""),
                "metadata": {
                    "model": response_data.get("model"),
                    "source_nodes": response_data.get("source_nodes", []),
                    "rag_mode": response_data.get("rag_mode"),
                    "created_at": response_data.get("created_at"),
                }
            })

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


def display_chat_history(chat_history: list[dict[str, Any]]) -> None:
    """Display chat history using st.chat_message components with Markdown and source citations.

    Args:
        chat_history: List of message dictionaries with role, content, and optional metadata.
    """
    for message in chat_history:
        role = message["role"]
        content = message.get("content", "")
        metadata = message.get("metadata", {})

        with st.chat_message(role):
            if role == "user":
                # User messages - check if JSON (for task agents)
                try:
                    if content.strip().startswith("{") and content.strip().endswith("}"):
                        json_data = json.loads(content)
                        st.json(json_data)
                    else:
                        st.markdown(content)
                except (json.JSONDecodeError, AttributeError):
                    st.markdown(content)
            else:
                # Assistant messages - render with Markdown and show metadata
                if content:
                    st.markdown(content)
                
                # Display source citations if available
                source_nodes = metadata.get("source_nodes", [])
                if source_nodes:
                    display_source_citations(source_nodes)
                
                # Display metadata
                if metadata:
                    display_message_metadata(metadata)


def display_source_citations(source_nodes: list[dict[str, Any]]) -> None:
    """Display source citations in an expandable section.

    Args:
        source_nodes: List of source node dictionaries with docId, chunkId, score, text.
    """
    if not source_nodes:
        return
    
    # Sort by score (highest first)
    sorted_sources = sorted(source_nodes, key=lambda x: x.get("score", 0), reverse=True)
    
    with st.expander(f"📚 Sources ({len(sorted_sources)} documents)", expanded=False):
        for idx, source in enumerate(sorted_sources, 1):
            doc_id = source.get("docId", "Unknown")
            chunk_id = source.get("chunkId", "Unknown")
            score = source.get("score", 0)
            text = source.get("text", "")
            
            # Display source header
            st.markdown(f"**Source {idx}** (Score: {score:.3f})")
            
            # Display IDs in a compact format
            col1, col2 = st.columns(2)
            with col1:
                # Truncate long document IDs
                short_doc_id = doc_id[:40] + "..." if len(doc_id) > 40 else doc_id
                st.caption(f"📄 Doc: `{short_doc_id}`")
            with col2:
                short_chunk_id = chunk_id[:40] + "..." if len(chunk_id) > 40 else chunk_id
                st.caption(f"🔖 Chunk: `{short_chunk_id}`")
            
            # Display chunk content with Markdown
            if text:
                with st.container():
                    st.markdown("**Content:**")
                    # Limit text length to avoid overwhelming the UI
                    display_text = text[:500] + "..." if len(text) > 500 else text
                    st.markdown(display_text)
            
            # Add separator between sources
            if idx < len(sorted_sources):
                st.markdown("---")


def display_message_metadata(metadata: dict[str, Any]) -> None:
    """Display message metadata in a compact format.

    Args:
        metadata: Dictionary containing model, rag_mode, created_at, etc.
    """
    model = metadata.get("model")
    rag_mode = metadata.get("rag_mode")
    created_at = metadata.get("created_at")
    
    # Build metadata string
    meta_parts = []
    if model:
        meta_parts.append(f"Model: {model}")
    if rag_mode:
        meta_parts.append(f"RAG Mode: {rag_mode}")
    if created_at:
        # Convert timestamp to readable format
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(created_at)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            meta_parts.append(f"Time: {time_str}")
        except Exception:
            pass
    
    if meta_parts:
        st.caption(" | ".join(meta_parts))


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
