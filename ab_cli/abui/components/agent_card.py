"""Agent card component for displaying agent information."""

import streamlit as st

from ab_cli.models.agent import Agent


def agent_card(agent: Agent) -> None:
    """Display an agent card with its information and actions.

    Args:
        agent: Agent model object
    """
    with st.container():
        # Create a card-like container with a border
        agent_name = agent.name
        with st.expander(f"{agent_name}", expanded=True):
            # Display agent information
            st.markdown(f"**ID:** {agent.id}")
            st.markdown(f"**Type:** {agent.type}")

            if agent.description:
                st.markdown(f"**Description:** {agent.description}")

            # Add action buttons - Chat, Details, and Edit
            col1, col2, col3 = st.columns(3)
            # Use agent ID for button keys
            agent_id = str(agent.id)

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
