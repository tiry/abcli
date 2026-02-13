"""Agent details page for the Agent Builder UI."""

import time

import streamlit as st

from ab_cli.abui.providers.provider_factory import get_data_provider


def display_agent_config(agent_config: dict, verbose: bool = False) -> None:
    """Display agent configuration in a structured way.

    Args:
        agent_config: The agent configuration dictionary
        verbose: Whether to print verbose debugging output
    """
    # Debug output
    if verbose:
        print(f"Agent config keys: {list(agent_config.keys())}")
        if "guardrails" in agent_config:
            print(f"Guardrails: {agent_config['guardrails']}")
        else:
            print("No guardrails found in agent_config")
    # Extract and display key fields first
    if "llmModelId" in agent_config:
        st.markdown("#### Model")
        st.info(agent_config["llmModelId"])
        st.markdown("---")

    if "systemPrompt" in agent_config:
        st.markdown("#### System Prompt")
        st.text_area("", value=agent_config["systemPrompt"], height=100, disabled=True)
        st.markdown("---")

    # Display guardrails if available
    if "guardrails" in agent_config and agent_config["guardrails"]:
        st.markdown("#### Guardrails")
        for guardrail in agent_config["guardrails"]:
            st.markdown(f"- {guardrail}")
        st.markdown("---")

    # Display tools as JSON if available
    if "tools" in agent_config:
        st.markdown("#### Tools")
        tools = agent_config["tools"]
        if tools:  # If tools is not empty
            st.json(tools)
        else:  # If tools is empty
            st.info("No tools configured for this agent")
        st.markdown("---")

    # Display inferenceConfig as JSON
    if "inferenceConfig" in agent_config:
        st.markdown("#### Inference Configuration")
        st.json(agent_config["inferenceConfig"])
        st.markdown("---")

    # Display inputSchema if available (for task agents)
    if "inputSchema" in agent_config:
        st.markdown("#### Input Schema")
        st.json(agent_config["inputSchema"])
        st.markdown("---")

    # Create a copy of the config without the fields we've already displayed
    remaining_config = agent_config.copy()
    fields_to_remove = [
        "llmModelId",
        "systemPrompt",
        "guardrails",
        "tools",
        "inferenceConfig",
        "inputSchema",
    ]
    for field in fields_to_remove:
        if field in remaining_config:
            del remaining_config[field]

    # Display remaining configuration if anything is left
    if remaining_config:
        st.markdown("#### Additional Configuration")
        st.json(remaining_config)


# extract_json_from_text is now imported from utils


def show_agent_details_page() -> None:
    """Display detailed information for a specific agent."""
    # Debug navigation state
    verbose = st.session_state.get("verbose", False)
    if verbose:
        print("[DEBUG] Agent Details View - Current Navigation State:")
        print(f"  current_page: {st.session_state.get('current_page')}")
        print(f"  nav_intent: {st.session_state.get('nav_intent')}")

    # Check if we have an agent to view
    agent_to_view = st.session_state.get("agent_to_view")
    if verbose and agent_to_view:
        print(f"  agent_to_view: {agent_to_view.get('id')} - {agent_to_view.get('name')}")
    elif verbose:
        print("  agent_to_view: None")

    if not agent_to_view:
        st.error("No agent selected for viewing.")
        # Add a button to go back to the agents list
        if st.button("Back to Agents List"):
            st.session_state.nav_intent = "Agents"
            st.rerun()
        return

    # Get or create data provider
    config = st.session_state.get("config")
    if not config:
        st.error("Configuration not loaded. Please check your settings.")
        return

    if "data_provider" not in st.session_state:
        st.session_state.data_provider = get_data_provider(config)

    provider = st.session_state.data_provider

    # Display agent header information
    title_col, action_col1, action_col2 = st.columns([3, 1, 1])

    with title_col:
        st.title(f"Agent Details: {agent_to_view.get('name', 'Unknown Agent')}")

    with action_col1:
        # Edit button
        if st.button("Edit Agent", use_container_width=True):
            if verbose:
                print("[DEBUG] Edit button clicked")
            # Make sure to include the agent_config when navigating to edit
            if "agent_config" in agent_to_view:
                # agent_config is already part of agent_to_view
                st.session_state.agent_to_edit = agent_to_view
                # Store navigation intent
                st.session_state.nav_intent = "EditAgent"
                if verbose:
                    print("[DEBUG] Set nav_intent to EditAgent")
                    print("[DEBUG] agent_to_edit set with config")
                # Give some time for the session state to update
                time.sleep(0.1)
                st.rerun()
            else:
                # We need to fetch the configuration first
                with st.spinner("Fetching agent configuration..."):
                    try:
                        # Get agent details from data provider
                        agent_data = provider.get_agent(agent_to_view["id"])

                        if not agent_data:
                            st.error("Failed to get agent configuration")
                            return

                        # Check if agent_config is available
                        if "agent_config" in agent_data:
                            # Update agent_to_view with the full data including config
                            st.session_state.agent_to_view = agent_data
                            st.session_state.agent_to_edit = agent_data
                            # Store navigation intent
                            st.session_state.nav_intent = "EditAgent"
                            if verbose:
                                print(
                                    "[DEBUG] Setting nav_intent to EditAgent after fetching config"
                                )
                                print("[DEBUG] Set agent_to_edit with fetched config")
                            # Give some time for the session state to update
                            time.sleep(0.1)
                            st.rerun()
                        else:
                            st.error("Configuration not found in agent data")
                    except Exception as e:
                        st.error(f"Error fetching agent configuration: {e}")

    with action_col2:
        # Chat button
        if st.button("Chat with Agent", use_container_width=True):
            if verbose:
                print("[DEBUG] Chat button clicked")
            st.session_state.selected_agent = agent_to_view
            st.session_state.nav_intent = "Chat"
            if verbose:
                print("[DEBUG] Set nav_intent to Chat")
            # Give some time for the session state to update
            time.sleep(0.1)
            st.rerun()

    # Create tabs for different sections
    tabs = st.tabs(["General Info", "Configuration", "Versions", "Statistics"])

    # General Info tab
    with tabs[0]:
        # Show agent basic information (without the heading)
        st.markdown(f"**ID:** `{agent_to_view.get('id', 'Unknown')}`")
        st.markdown(f"**Name:** {agent_to_view.get('name', 'Unknown')}")
        st.markdown(f"**Type:** {agent_to_view.get('type', 'Unknown')}")
        st.markdown(f"**Status:** {agent_to_view.get('status', 'Unknown')}")
        if agent_to_view.get("description"):
            st.markdown(f"**Description:** {agent_to_view.get('description')}")

        if agent_to_view.get("created_at"):
            st.markdown(f"**Created:** {agent_to_view.get('created_at')}")
        if agent_to_view.get("modified_at"):
            st.markdown(f"**Last Modified:** {agent_to_view.get('modified_at')}")

    # Configuration tab
    with tabs[1]:
        st.markdown("### Agent Configuration")

        # Try to get configuration from agent_to_view
        agent_config = agent_to_view.get("agent_config", {})
        if agent_config:
            # Display the configuration in a structured way
            display_agent_config(agent_config, verbose=verbose)
        else:
            # Fetch detailed agent information including configuration
            with st.spinner("Fetching agent configuration..."):
                try:
                    # Get agent details from data provider
                    agent_data = provider.get_agent(agent_to_view["id"])

                    if not agent_data:
                        st.error("Failed to get agent details")
                        return

                    # Check if agent_config is available
                    if "agent_config" in agent_data:
                        agent_config = agent_data["agent_config"]

                        # Store in the session state for future reference
                        st.session_state.agent_to_view = agent_data

                        # Display the configuration in a structured way
                        display_agent_config(agent_config, verbose=verbose)
                    else:
                        st.warning("Configuration not available in agent data")

                except Exception as e:
                    st.error(f"Error fetching agent configuration: {e}")

    # Versions tab - For now, we still use the CLI directly for versions
    # In a future update, the data provider should also handle versions
    with tabs[2]:
        st.markdown("### Agent Versions")

        try:
            # TODO: Add versions to data provider
            # For now, display a placeholder
            st.info("Agent version history will be added in a future update.")

            # Create a placeholder table
            try:
                # Import pandas with a proper type ignore that won't trigger mypy warning
                from typing import TYPE_CHECKING

                if TYPE_CHECKING:
                    import pandas as pd
                else:
                    import pandas as pd

                # Create placeholder version data
                versions_table = [
                    {
                        "Number": "1",
                        "Label": "v1.0",
                        "Notes": "Initial version",
                        "Created": "2026-02-11 10:00",
                        "ID": "ver-123...",
                    }
                ]

                df = pd.DataFrame(versions_table)
                st.dataframe(df, use_container_width=True, hide_index=True)
            except ImportError:
                # Fallback if pandas is not installed
                st.warning("Pandas not installed. Displaying versions as a table.")
                st.markdown("**Version 1**")
                st.markdown("Label: v1.0")
                st.markdown("Notes: Initial version")
                st.markdown("Created: 2026-02-11 10:00")
                st.markdown("ID: ver-123...")

        except Exception as e:
            st.error(f"Error displaying versions: {e}")

    # Statistics tab
    with tabs[3]:
        st.markdown("### Agent Statistics")
        st.info("Agent usage statistics will be displayed here in a future update.")

        # Placeholder for stats
        col1, col2 = st.columns(2)

        with col1:
            st.metric(label="Total Invocations", value="0")
            st.metric(label="Success Rate", value="0%")

        with col2:
            st.metric(label="Average Response Time", value="0 ms")
            st.metric(label="Last Invoked", value="Never")

    # Add a button to go back to the agents list
    st.markdown("---")
    if st.button("Back to Agents List"):
        st.session_state.nav_intent = "Agents"
        st.session_state.current_page = "Agents"  # Also update current page for consistency
        if verbose:
            print("[DEBUG] Back button clicked, setting nav_intent and current_page to Agents")
        # Give some time for the session state to update
        time.sleep(0.1)
        st.rerun()
