"""Chat page for the Agent Builder UI."""

from typing import Any

import streamlit as st

from ab_cli.abui.providers.provider_factory import get_data_provider


def show_chat_page() -> None:
    """Display the chat page with agent conversation interface."""
    st.title("Chat with Agent")

    # Get the configuration from the session state
    config = st.session_state.get("config")
    if not config:
        st.error("Configuration not loaded. Please check your settings.")
        return

    # Get or create data provider
    if "data_provider" not in st.session_state:
        st.session_state.data_provider = get_data_provider(config)

    # Check if an agent is selected
    selected_agent = st.session_state.get("selected_agent")

    # If no agent is selected, show a selection dropdown
    if not selected_agent:
        agent_selection()
    else:
        chat_interface(selected_agent)


def agent_selection() -> None:
    """Display agent selection interface."""
    st.subheader("Select an Agent to Chat With")

    # Get data provider from session state
    provider = st.session_state.data_provider

    try:
        # Get list of agents from data provider
        agents = provider.get_agents()

        if not agents:
            st.info("No agents found. Create an agent first.")
            if st.button("Go to Agent Management"):
                st.session_state.nav_intent = "Agents"
                st.rerun()
            return

        # Create a selectbox with agent names
        agent_names = [agent["name"] for agent in agents]
        selected_name = st.selectbox("Choose an agent", agent_names)

        # Find the selected agent
        selected_agent = next((a for a in agents if a["name"] == selected_name), None)

        if selected_agent and st.button("Start Chat"):
            st.session_state.selected_agent = selected_agent

            # Initialize chat history for this agent
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = {}

            agent_id = selected_agent["id"]
            if agent_id not in st.session_state.chat_history:
                st.session_state.chat_history[agent_id] = []

            st.rerun()

    except Exception as e:
        st.error(f"Error loading agents: {e}")


def chat_interface(agent: dict[str, Any]) -> None:
    """Display the chat interface for a selected agent.

    Args:
        agent: Dictionary containing agent information
    """
    st.subheader(f"Chat with {agent['name']}")

    # Show agent information
    with st.expander("Agent Details", expanded=False):
        st.markdown(f"**ID:** {agent['id']}")
        st.markdown(f"**Type:** {agent['type']}")

        # Get model information - check different possible locations
        model = None
        # Try to get from direct model field
        if "model" in agent:
            model = agent["model"]
        # Try to get from agent_config if available
        elif "agent_config" in agent and "llmModelId" in agent["agent_config"]:
            model = agent["agent_config"]["llmModelId"]
        # Fallback to type
        else:
            model = agent.get("type", "unknown")

        st.markdown(f"**Model:** {model}")

        if agent.get("description"):
            st.markdown(f"**Description:** {agent['description']}")

    # Get or initialize chat history for this agent
    agent_id = agent["id"]
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    if agent_id not in st.session_state.chat_history:
        st.session_state.chat_history[agent_id] = []

    # Display chat history
    chat_history = st.session_state.chat_history[agent_id]

    # Chat container with fixed height and scrolling
    chat_container = st.container()
    with chat_container:
        for message in chat_history:
            role = message["role"]
            content = message["content"]

            # Style based on role
            if role == "user":
                st.markdown(f"**You**: {content}")
            else:
                st.markdown(f"**{agent['name']}**: {content}")

            # Add a separator
            st.markdown("---")

    # Input area for new message
    with st.form("chat_input_form"):
        user_input = st.text_area("Your message:", height=100)
        submitted = st.form_submit_button("Send")

        if submitted and user_input:
            # Add user message to history
            chat_history.append({"role": "user", "content": user_input})

            # Get data provider from session state
            provider = st.session_state.data_provider

            # Get agent response with a loading spinner
            with st.spinner(f"Invoking agent {agent['name']}..."):
                try:
                    response = provider.invoke_agent(agent["id"], user_input)

                    # Add agent response to history with agent name for clarity
                    display_response = f"{response}"
                    chat_history.append({"role": "assistant", "content": display_response})

                    # Update session state
                    st.session_state.chat_history[agent_id] = chat_history

                    # Rerun to update the UI
                    st.rerun()

                except Exception as e:
                    st.error(f"Error getting response: {e}")

    # Button to clear chat history
    if st.button("Clear Chat History"):
        st.session_state.chat_history[agent_id] = []
        st.rerun()

    # Button to go back to agent selection
    if st.button("Change Agent"):
        st.session_state.selected_agent = None
        st.rerun()


# The extract_json_from_text and extract_text_from_object functions are now imported from utils
# The get_agents, get_fallback_agents, and invoke_agent functions are no longer needed
# as the data provider handles this functionality
