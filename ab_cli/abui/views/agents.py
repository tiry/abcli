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
    """Display a paginated list of available agents."""
    # Initialize pagination state - use 50 items to match CLI default
    if "agents_page" not in st.session_state:
        st.session_state.agents_page = 1
    if "agents_page_size" not in st.session_state:
        st.session_state.agents_page_size = 50

    # Get data provider from session state
    provider = st.session_state.data_provider

    # Fetch paginated data first (so we have the info for top row)
    try:
        offset = (st.session_state.agents_page - 1) * st.session_state.agents_page_size
        result = provider.get_agents_paginated(
            limit=st.session_state.agents_page_size, offset=offset
        )

        # Calculate pagination info for display
        total_pages = (
            (result.total_count + result.limit - 1) // result.limit if result.total_count > 0 else 1
        )
        current_page = st.session_state.agents_page
        start = result.offset + 1
        end = min(result.offset + result.limit, result.total_count)

        # Controls row: refresh, view mode, pagination info and navigation
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])

        with col1:
            if st.button("Refresh Agent List"):
                # Clear the cache when refreshing
                clear_cache()
                st.success("Cache cleared and agent list refreshed")

        with col2:
            # Use segmented_control with icons for view mode toggle
            view_mode = st.segmented_control(
                label="View Mode:", options=["🗂️ Cards", "📋 Table"], key="agent_view_mode"
            )

        with col3:
            st.caption(f"Showing {start}-{end} of {result.total_count} agents")

        with col4:
            # Simple page number input with -/+ buttons
            page_input = st.number_input(
                f"Page (1-{total_pages})",
                min_value=1,
                max_value=total_pages,
                value=current_page,
                key="page_input",
                label_visibility="visible",
            )
            if page_input != current_page:
                st.session_state.agents_page = page_input
                st.rerun()

        if not result.agents:
            st.info("No agents found. Create a new agent to get started.")
            return

        # Display agents based on selected view mode
        if view_mode is not None and "Cards" in view_mode:
            display_agents_as_cards(result.agents)
        else:
            display_agents_as_table(result.agents)

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
    """Display agents in a clean dataframe table with action buttons."""
    import pandas as pd

    # Add CSS to reduce padding and make table more compact
    st.markdown(
        """
    <style>
    /* Reduce dataframe container padding */
    [data-testid="stDataFrame"] {
        padding: 0 !important;
        margin: 0 !important;
    }
    /* Compact dataframe height */
    [data-testid="stDataFrame"] > div {
        height: 400px !important;
        max-height: 400px !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Prepare data for table
    table_data = []
    for agent in agents:
        agent_id = agent.get("id", "")
        short_id = agent_id[:10] + "..." if len(agent_id) > 10 else agent_id

        table_data.append(
            {
                "ID": short_id,
                "Name": agent.get("name", "Unknown"),
                "Type": agent.get("type", ""),
                "Status": agent.get("status", ""),
                "_full_id": agent_id,  # Hidden for tooltip
            }
        )

    df = pd.DataFrame(table_data)

    # Display dataframe with row selection
    event = st.dataframe(
        df[["ID", "Name", "Type", "Status"]],
        width="stretch",
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "ID": st.column_config.TextColumn("ID", help="Agent ID", width="medium"),
            "Name": st.column_config.TextColumn("Name", width="medium"),
            "Type": st.column_config.TextColumn("Type", width="small"),
            "Status": st.column_config.TextColumn("Status", width="small"),
        },
    )

    # Determine if a row is selected
    has_selection = bool(event.selection.rows)  # type: ignore[attr-defined]
    selected_agent = None
    selected_display = "None"

    if has_selection:
        selected_idx = event.selection.rows[0]  # type: ignore[attr-defined]
        selected_agent = agents[selected_idx]
        selected_display = f"{selected_agent.get('name')} ({table_data[selected_idx]['ID']})"

    # Always show action buttons, but disabled when no selection
    st.markdown("---")
    st.markdown(f"**Selected:** {selected_display}")

    # Show action buttons in columns (always visible, disabled when no selection)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if (
            st.button("📋 Copy Full ID", use_container_width=True, disabled=not has_selection)
            and selected_agent
        ):
            full_id = selected_agent.get("id", "")
            st.toast(f"ID: {full_id}", icon="📋")

    with col2:
        if (
            st.button("👁️ View Details", use_container_width=True, disabled=not has_selection)
            and selected_agent
        ):
            st.session_state.agent_to_view = selected_agent
            st.session_state.nav_intent = "AgentDetails"
            st.rerun()

    with col3:
        if (
            st.button("✏️ Edit Agent", use_container_width=True, disabled=not has_selection)
            and selected_agent
        ):
            st.session_state.agent_to_edit = selected_agent
            st.session_state.nav_intent = "EditAgent"
            st.rerun()

    with col4:
        if (
            st.button("💬 Chat", use_container_width=True, disabled=not has_selection)
            and selected_agent
        ):
            st.session_state.selected_agent = selected_agent
            st.session_state.nav_intent = "Chat"
            st.rerun()


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
