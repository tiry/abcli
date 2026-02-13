"""Agent card component for displaying agent information."""

from typing import Any

import streamlit as st


def agent_card(agent: dict[str, Any]) -> None:
    """Display an agent card with its information and actions.

    Args:
        agent: Dictionary containing agent information
    """
    with st.container():
        # Create a card-like container with a border
        # Handle potential missing fields safely
        agent_name = agent.get("name", "Unnamed Agent")
        with st.expander(f"{agent_name}", expanded=True):
            # Display agent information - removing model and created fields
            st.markdown(f"**ID:** {agent.get('id', 'Unknown')}")
            st.markdown(f"**Type:** {agent.get('type', 'Unknown')}")

            if agent.get("description"):
                st.markdown(f"**Description:** {agent['description']}")

            # Add action buttons - Chat, Details, and Edit
            col1, col2, col3 = st.columns(3)
            # Get agent ID, defaulting to a unique string if missing
            agent_id = agent.get("id", f"unknown-{id(agent)}")

            with col1:
                if st.button("Chat", key=f"chat_{agent_id}"):
                    # Navigate to the chat page by setting the navigation intent
                    st.session_state.selected_agent = agent
                    # Set the navigation intent to Chat
                    st.session_state.nav_intent = "Chat"
                    st.rerun()

            with col2:
                if st.button("Details", key=f"details_{agent_id}"):
                    # Store the selected agent for viewing in session state
                    st.session_state.agent_to_view = agent
                    # Navigate to the dedicated AgentDetails view
                    st.session_state.nav_intent = "AgentDetails"
                    st.rerun()

            with col3:
                if st.button("Edit", key=f"edit_{agent_id}"):
                    # Store the selected agent for editing in session state
                    st.session_state.agent_to_edit = agent
                    # Navigate to the dedicated EditAgent view
                    st.session_state.nav_intent = "EditAgent"
                    st.rerun()
