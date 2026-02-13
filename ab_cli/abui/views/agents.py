"""Agents page for the Agent Builder UI."""

from typing import Any, cast

import streamlit as st

from ab_cli.abui.components.agent_card import agent_card
from ab_cli.abui.providers.provider_factory import get_data_provider


def clear_cache() -> None:
    """Clear the data provider cache."""
    # Get data provider from session state
    if "data_provider" in st.session_state:
        st.session_state.data_provider.clear_cache()

    # Also clear any Streamlit cache
    st.cache_data.clear()


def show_agents_page() -> None:
    """Display the agents page."""
    st.title("Agent Management")

    # Get the configuration from the session state
    config = st.session_state.get("config")
    if not config:
        st.error("Configuration not loaded. Please check your settings.")
        return

    # Get or create data provider
    if "data_provider" not in st.session_state:
        st.session_state.data_provider = get_data_provider(config)

    # Add a create agent button at the top
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Available Agents")

    with col2:
        if st.button("➕ Create Agent", use_container_width=True):
            # Navigate to the EditAgent view with no agent to edit (for creating new)
            st.session_state.agent_to_edit = None
            st.session_state.nav_intent = "EditAgent"
            st.rerun()

    # Show the list of agents
    show_agent_list()


def show_agent_list() -> None:
    """Display a list of available agents."""
    # Add refresh button and view toggle in the same row
    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Refresh Agent List"):
            # Clear the cache when refreshing
            clear_cache()
            st.success("Cache cleared and agent list refreshed")

    with col2:
        # Use segmented_control with icons for view mode toggle
        # Icons: 📋 for list/table and 🗂️ for cards
        view_mode = st.segmented_control(
            label="View Mode:", options=["🗂️ Cards", "📋 Table"], key="agent_view_mode"
        )

    # Get data provider from session state
    provider = st.session_state.data_provider

    # Use data provider to get the list of agents
    try:
        agents = provider.get_agents()

        if not agents:
            st.info("No agents found. Create a new agent to get started.")
            return

        # Display agents based on selected view mode
        if view_mode is not None and "Cards" in view_mode:
            display_agents_as_cards(agents)
        else:
            display_agents_as_table(agents)

    except Exception as e:
        st.error(f"Error loading agents: {e}")


def display_agents_as_cards(agents: list[dict[str, Any]]) -> None:
    """Display agents in a grid with cards.

    Args:
        agents: List of agent dictionaries
    """
    # Display agents in a grid with cards
    col1, col2 = st.columns(2)

    for i, agent in enumerate(agents):
        with col1 if i % 2 == 0 else col2:
            # Use our agent card component
            agent_card(agent)


def display_agents_as_table(agents: list[dict[str, Any]]) -> None:
    """Display agents in a table format with correct alternating row colors."""

    # 1. Improved CSS to handle the row wrapper
    st.markdown(
        """
    <style>
    .table-header {
        font-weight: bold;
        background-color: #e6e6e6;
        padding: 10px;
        border-radius: 5px 5px 0px 0px;
        margin-bottom: 5px;
    }
    /* Style for the custom row wrapper */
    .agent-row-container {
        padding: 5px 10px;
        margin-bottom: 4px;
        border-radius: 4px;
        border: 1px solid #f0f2f6;
    }
    .even-bg { background-color: #f8f9fa; }
    .odd-bg { background-color: #ffffff; }
    /* Make buttons look better inside the table */
    .stButton > button {
        padding: 2px 8px !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Header
    st.markdown(
        """
    <div class="table-header">
        <div style="display: grid; grid-template-columns: 3fr 3fr 1fr 1fr 2fr; gap: 10px;">
            <div>ID</div>
            <div>Name</div>
            <div>Type</div>
            <div>Status</div>
            <div style="text-align: center;">Actions</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 2. Iterating through agents
    for i, agent in enumerate(agents):
        agent_id = agent.get("id", "")
        agent_name = agent.get("name", "Unknown")
        agent_type = agent.get("type", "")
        agent_status = agent.get("status", "")

        # Determine background color based on index
        bg_color = "#f8f9fa" if i % 2 == 0 else "#ffffff"

        # 3. Use a container to group the row elements
        with st.container():
            # Inject the background color as a wrapping div using a 'sandwich'
            st.markdown(
                f'<div style="background-color: {bg_color}; padding: 10px; border-radius: 4px; border: 1px solid #eee; margin-bottom: 4px;">',
                unsafe_allow_html=True,
            )

            # Draw the columns
            id_col, name_col, type_col, status_col, actions_col = st.columns([3, 3, 1, 1, 2])

            with id_col:
                st.markdown(f"<code>{agent_id}</code>", unsafe_allow_html=True)

            with name_col:
                st.write(agent_name)

            with type_col:
                st.write(agent_type)

            with status_col:
                # Optional: add color to status
                color = "green" if agent_status == "CREATED" else "gray"
                st.markdown(
                    f"<span style='color:{color}; font-weight:bold;'>{agent_status}</span>",
                    unsafe_allow_html=True,
                )

            with actions_col:
                btn_col1, btn_col2, btn_col3 = st.columns(3)
                with btn_col1:
                    if st.button("👁️", key=f"view_{i}", help="View details"):
                        st.session_state.agent_to_view = agent
                        st.session_state.nav_intent = "AgentDetails"
                        st.rerun()
                with btn_col2:
                    if st.button("✏️", key=f"edit_{i}", help="Edit agent"):
                        st.session_state.agent_to_edit = agent
                        st.session_state.nav_intent = "EditAgent"
                        st.rerun()
                with btn_col3:
                    if st.button("💬", key=f"chat_{i}", help="Chat with agent"):
                        st.session_state.selected_agent = agent
                        st.session_state.nav_intent = "Chat"
                        st.rerun()

            # Close the wrapping div
            st.markdown("</div>", unsafe_allow_html=True)


def _display_agents_as_table(agents: list[dict[str, Any]]) -> None:
    """Display agents in a table format with inline action buttons using columns.

    Args:
        agents: List of agent dictionaries
    """
    # Define CSS for styling the table and buttons
    st.markdown(
        """
    <style>
    /* Table header styling */
    .table-header {
        font-weight: bold;
        background-color: #e6e6e6;
        padding: 10px;
        border-radius: 5px 5px 0px 0px;
        margin-bottom: 5px;
    }
    /* Make buttons more compact */
    .stButton > button {
        padding: 0.2rem 0.6rem;
        line-height: 1;
        height: auto;
    }
    /* This targets the custom div we will wrap around our columns */
    .agent-row {
        padding: 8px;
        margin-bottom: 2px;
        border-radius: 4px;
        display: flex;
        align-items: center;
    }
    .even-row { background-color: #f8f9fa; }
    .odd-row { background-color: #ffffff; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Create the table header with columns - updated order and column widths
    # ID first, then Name, then narrower Type and Status columns, then Actions
    st.markdown(
        """
    <div class="table-header">
        <div style="display: grid; grid-template-columns: 3fr 3fr 1fr 1fr 2fr; gap: 10px;">
            <div>ID</div>
            <div>Name</div>
            <div>Type</div>
            <div>Status</div>
            <div style="text-align: center;">Actions</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Create a row for each agent
    for i, agent in enumerate(agents):
        # Extract agent details
        agent_id = agent.get("id", "")
        agent_name = agent.get("name", "Unknown")
        agent_type = agent.get("type", "")
        agent_status = agent.get("status", "")

        # Determine the background color based on the row index
        bg_color = "#f8f9fa" if i % 2 == 0 else "#ffffff"

        with st.container():
            # Use opening markdown tag with inline style for background color
            st.markdown(
                f'<div style="background-color: {bg_color}; padding: 10px; border-radius: 4px; border: 1px solid #eee; margin-bottom: 5px;">',
                unsafe_allow_html=True,
            )

            # Create columns for the content
            id_col, name_col, type_col, status_col, actions_col = st.columns([3, 3, 1, 1, 2])

            # Display agent details in each column
            with id_col:
                st.write(agent_id)

            with name_col:
                st.write(agent_name)

            with type_col:
                st.write(agent_type)

            with status_col:
                st.write(agent_status)

            # Display action buttons in the actions column
            with actions_col:
                # Create a horizontal layout for the buttons
                btn_col1, btn_col2, btn_col3 = st.columns(3)

                with btn_col1:
                    if st.button("👁️", key=f"view_{i}", help="View details"):
                        st.session_state.agent_to_view = agent
                        st.session_state.nav_intent = "AgentDetails"
                        st.rerun()

                with btn_col2:
                    if st.button("✏️", key=f"edit_{i}", help="Edit agent"):
                        st.session_state.agent_to_edit = agent
                        st.session_state.nav_intent = "EditAgent"
                        st.rerun()

                with btn_col3:
                    if st.button("💬", key=f"chat_{i}", help="Chat with agent"):
                        st.session_state.selected_agent = agent
                        st.session_state.nav_intent = "Chat"
                        st.rerun()

            # Close the div after all content
            st.markdown("</div>", unsafe_allow_html=True)


# Import extract_json_from_text from shared utilities instead of defining it here


# The get_agents, get_fallback_agents functions are no longer needed
# as the data provider handles this functionality


def get_models() -> list[str]:
    """Get the list of available models using the data provider.

    Returns:
        List of model names
    """
    # Get data provider from session state
    provider = st.session_state.get("data_provider")
    if not provider:
        return []

    with st.spinner("Loading models..."):
        models = provider.get_models()
        return cast(list[str], models)


def get_guardrails() -> list[str]:
    """Get the list of available guardrails using the data provider.

    Returns:
        List of guardrail names
    """
    # Get data provider from session state
    provider = st.session_state.get("data_provider")
    if not provider:
        return []

    with st.spinner("Loading guardrails..."):
        guardrails = provider.get_guardrails()
        return cast(list[str], guardrails)
