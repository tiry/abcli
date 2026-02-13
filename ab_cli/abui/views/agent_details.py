"""Agent details page for the Agent Builder UI."""

import json
import os
import re
import subprocess
import time
from typing import Any, cast

import streamlit as st

# Import shared cache functions


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


def extract_json_from_text(text: str, verbose: bool = False) -> dict[str, Any] | None:
    """Extract JSON content from text that might include non-JSON content.

    Args:
        text: Text that might contain JSON
        verbose: Whether to print verbose output

    Returns:
        Parsed JSON object or None if no valid JSON found
    """
    if not text:
        if verbose:
            print("No text to parse")
        return None

    # First try direct parsing
    try:
        return cast(dict[str, Any], json.loads(text))
    except json.JSONDecodeError:
        if verbose:
            print("Direct JSON parsing failed, trying to extract JSON content")

    # Try to find JSON content in the text
    json_pattern = r"(\{.*\}|\[.*\])"
    try:
        # Look for the largest JSON-like pattern in the text
        matches = list(re.finditer(json_pattern, text, re.DOTALL))
        if matches:
            # Sort by length, descending
            matches.sort(key=lambda m: len(m.group(0)), reverse=True)

            # Try each match, starting with the largest
            for match in matches:
                try:
                    json_str = match.group(0)
                    if verbose:
                        print(f"Found potential JSON: {json_str[:100]}...")
                    return cast(dict[str, Any], json.loads(json_str))
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        if verbose:
            print(f"Error extracting JSON with regex: {e}")

    if verbose:
        print("Could not extract JSON with regex")

    # More aggressive approach - try to find starting brace/bracket and parse from there
    try:
        start_index = -1
        for i, char in enumerate(text):
            if char in "{[":
                start_index = i
                break

        if start_index != -1:
            # Try to parse from this point
            try:
                return cast(dict[str, Any], json.loads(text[start_index:]))
            except json.JSONDecodeError:
                if verbose:
                    print(f"Failed to parse from start marker at position {start_index}")
    except Exception as e:
        if verbose:
            print(f"Error in aggressive JSON extraction: {e}")

    return None


def show_agent_details_page() -> None:
    """Display detailed information for a specific agent."""
    # Debug navigation state
    print("[DEBUG] Agent Details View - Current Navigation State:")
    print(f"  current_page: {st.session_state.get('current_page')}")
    print(f"  nav_intent: {st.session_state.get('nav_intent')}")

    # Check if we have an agent to view
    agent_to_view = st.session_state.get("agent_to_view")
    if agent_to_view:
        print(f"  agent_to_view: {agent_to_view.get('id')} - {agent_to_view.get('name')}")
    else:
        print("  agent_to_view: None")

    if not agent_to_view:
        st.error("No agent selected for viewing.")
        # Add a button to go back to the agents list
        if st.button("Back to Agents List"):
            st.session_state.nav_intent = "Agents"
            st.rerun()
        return

    # Display agent header information
    title_col, action_col1, action_col2 = st.columns([3, 1, 1])

    with title_col:
        st.title(f"Agent Details: {agent_to_view.get('name', 'Unknown Agent')}")

    with action_col1:
        # Edit button
        if st.button("Edit Agent", use_container_width=True):
            print("[DEBUG] Edit button clicked")
            # Make sure to include the agent_config when navigating to edit
            if "agent_config" in agent_to_view:
                # agent_config is already part of agent_to_view
                st.session_state.agent_to_edit = agent_to_view
                # Store navigation intent
                st.session_state.nav_intent = "EditAgent"
                print("[DEBUG] Set nav_intent to EditAgent")
                print("[DEBUG] agent_to_edit set with config")
                # Give some time for the session state to update
                time.sleep(0.1)
                st.rerun()
            else:
                # We need to fetch the configuration first
                with st.spinner("Fetching agent configuration..."):
                    try:
                        # Get configuration from session state
                        config = st.session_state.get("config")
                        verbose = st.session_state.get("verbose", False)

                        if not config:
                            st.error("Configuration not loaded. Please check your settings.")
                            return

                        # Build the CLI command
                        cmd = ["ab"]
                        if verbose:
                            cmd.append("--verbose")
                        if hasattr(config, "config_path") and config.config_path:
                            cmd.extend(["--config", str(config.config_path)])
                        cmd.extend(["agents", "get", agent_to_view["id"], "--format", "json"])

                        # Execute the command
                        module_cmd = ["python", "-m", "ab_cli.cli.main"]
                        module_cmd.extend(cmd[1:])  # Skip the "ab" at the beginning
                        result = subprocess.run(
                            module_cmd,
                            capture_output=True,
                            text=True,
                            cwd=os.path.join(os.path.dirname(__file__), "../../../"),
                        )

                        if result.returncode != 0:
                            st.error(
                                "Failed to get agent configuration. Please try viewing the Configuration tab first."
                            )
                            return

                        # Try to extract JSON from the response
                        agent_data = extract_json_from_text(result.stdout, verbose=verbose)
                        if not agent_data:
                            st.error("Failed to extract valid JSON from the response")
                            return

                        # Check if version and configuration are available
                        if "version" in agent_data and "config" in agent_data["version"]:
                            agent_config = agent_data["version"]["config"]
                            # Update agent with the config and navigate
                            agent_to_view["agent_config"] = agent_config
                            st.session_state.agent_to_edit = agent_to_view
                            # Store navigation intent
                            print("[DEBUG] Setting nav_intent to EditAgent after fetching config")
                            st.session_state.nav_intent = "EditAgent"
                            print("[DEBUG] Set agent_to_edit with fetched config")
                            # Give some time for the session state to update
                            time.sleep(0.1)
                            st.rerun()
                        else:
                            st.error(
                                "Configuration not found in agent data. Please try viewing the Configuration tab first."
                            )
                    except Exception as e:
                        st.error(f"Error fetching agent configuration: {e}")

    with action_col2:
        # Chat button
        if st.button("Chat with Agent", use_container_width=True):
            print("[DEBUG] Chat button clicked")
            st.session_state.selected_agent = agent_to_view
            st.session_state.nav_intent = "Chat"
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
            display_agent_config(agent_config, verbose=st.session_state.get("verbose", False))
        else:
            # Fetch detailed agent information including configuration
            try:
                # Get configuration from session state
                config = st.session_state.get("config")
                verbose = st.session_state.get("verbose", False)

                if not config:
                    st.error("Configuration not loaded. Please check your settings.")
                    return

                # Build the CLI command
                cmd = ["ab"]

                # Add verbose flag if enabled
                if verbose:
                    cmd.append("--verbose")

                # Add config path if available
                if hasattr(config, "config_path") and config.config_path:
                    cmd.extend(["--config", str(config.config_path)])

                cmd.extend(["agents", "get", agent_to_view["id"], "--format", "json"])

                # Execute the command with a loading spinner
                with st.spinner("Fetching agent configuration..."):
                    if verbose:
                        print(f"Executing command: {cmd}")

                    # Try executing with the Python module approach
                    # This can help if the PATH isn't set up correctly when running from streamlit
                    module_cmd = ["python", "-m", "ab_cli.cli.main"]
                    module_cmd.extend(cmd[1:])  # Skip the "ab" at the beginning

                    if verbose:
                        print(f"Executing module command: {module_cmd}")

                    result = subprocess.run(
                        module_cmd,
                        capture_output=True,
                        text=True,
                        cwd=os.path.join(
                            os.path.dirname(__file__), "../../../"
                        ),  # Run from the ab-cli directory
                    )

                    if result.returncode != 0:
                        if verbose:
                            print(f"Command failed: {result.stderr}")
                        st.error(f"Failed to get agent configuration: {result.stderr}")
                    else:
                        try:
                            # Parse the JSON output
                            if verbose:
                                st.code(result.stdout, language="json")
                                print(f"Raw stdout: {result.stdout[:1000]}")

                            # Try to extract JSON from the response
                            agent_data = extract_json_from_text(result.stdout, verbose=verbose)

                            if not agent_data:
                                st.error("Failed to extract valid JSON from the response")
                                # Display raw output as a fallback
                                st.expander("Show Raw Response", expanded=False).code(result.stdout)
                                return

                            # Check if version and configuration are available based on the expected structure
                            # The structure is: {"agent": {...}, "version": {"config": {...}}}
                            if verbose:
                                print(f"Agent data keys: {list(agent_data.keys())}")
                                if "version" in agent_data:
                                    print(f"Version keys: {list(agent_data['version'].keys())}")

                            if "version" in agent_data and "config" in agent_data["version"]:
                                agent_config = agent_data["version"]["config"]

                                # Store in the session state for future reference
                                if "agent_to_view" in st.session_state:
                                    st.session_state.agent_to_view["agent_config"] = agent_config
                                    print("[DEBUG] Stored agent_config in agent_to_view")

                                # Also update the agent data with the latest information from the API
                                if "agent" in agent_data and "agent_to_view" in st.session_state:
                                    # Update agent data but preserve existing fields we might need
                                    updated_agent = {
                                        **st.session_state.agent_to_view,
                                        **agent_data["agent"],
                                    }
                                    st.session_state.agent_to_view = updated_agent

                                # Display the configuration in a structured way
                                display_agent_config(agent_config, verbose=verbose)
                            else:
                                # Try other known formats:
                                # Alternative 1: "agent": {...}, "agent_config": {...}
                                if "agent" in agent_data and "agent_config" in agent_data:
                                    agent_config = agent_data["agent_config"]

                                    # Store in the session state
                                    if "agent_to_view" in st.session_state:
                                        st.session_state.agent_to_view["agent_config"] = (
                                            agent_config
                                        )
                                        print(
                                            "[DEBUG] Stored agent_config in agent_to_view (alt 1)"
                                        )

                                    # Display the configuration in a structured way
                                    display_agent_config(agent_config, verbose=verbose)
                                # Alternative 2: Direct config at top level
                                elif "config" in agent_data:
                                    agent_config = agent_data["config"]

                                    # Store in the session state
                                    if "agent_to_view" in st.session_state:
                                        st.session_state.agent_to_view["agent_config"] = (
                                            agent_config
                                        )
                                        print(
                                            "[DEBUG] Stored agent_config in agent_to_view (alt 2)"
                                        )

                                    # Display the configuration in a structured way
                                    display_agent_config(agent_config, verbose=verbose)
                                else:
                                    if verbose:
                                        st.warning(
                                            f"Configuration not found in expected locations. Available keys: {list(agent_data.keys())}"
                                        )
                                    else:
                                        st.warning("Configuration not available in agent data")
                        except json.JSONDecodeError as e:
                            st.error(f"Failed to parse agent configuration: {e}")
                            if verbose:
                                print(f"JSON decode error: {e}")
                                print(f"First 200 chars of output: {result.stdout[:200]}")

                            # Display raw output as a fallback
                            with st.expander("Show Raw Response", expanded=True):
                                st.code(result.stdout, language="text")
                        except Exception as e:
                            st.error(
                                f"Error processing agent configuration: {type(e).__name__}: {e}"
                            )
                            if verbose:
                                print(f"Exception: {type(e).__name__}: {e}")

            except Exception as e:
                st.error(f"Error fetching agent configuration: {e}")

    # Versions tab
    with tabs[2]:
        st.markdown("### Agent Versions")

        try:
            # Get configuration from session state
            config = st.session_state.get("config")
            verbose = st.session_state.get("verbose", False)

            if not config:
                st.error("Configuration not loaded. Please check your settings.")
                return

            # Build the CLI command
            cmd = ["ab"]

            # Add verbose flag if enabled
            if verbose:
                cmd.append("--verbose")

            # Add config path if available
            if hasattr(config, "config_path") and config.config_path:
                cmd.extend(["--config", str(config.config_path)])

            cmd.extend(["versions", "list", agent_to_view["id"], "--format", "json"])

            # Execute the command with a loading spinner
            with st.spinner("Fetching agent versions..."):
                if verbose:
                    print(f"Executing command: {cmd}")

                # Try executing with the Python module approach
                # This can help if the PATH isn't set up correctly when running from streamlit
                module_cmd = ["python", "-m", "ab_cli.cli.main"]
                module_cmd.extend(cmd[1:])  # Skip the "ab" at the beginning

                if verbose:
                    print(f"Executing module command: {module_cmd}")

                result = subprocess.run(
                    module_cmd,
                    capture_output=True,
                    text=True,
                    cwd=os.path.join(
                        os.path.dirname(__file__), "../../../"
                    ),  # Run from the ab-cli directory
                )

                if result.returncode != 0:
                    if verbose:
                        print(f"Command failed: {result.stderr}")
                    st.error(f"Failed to get agent versions: {result.stderr}")
                else:
                    try:
                        # Parse the JSON output
                        versions_data = json.loads(result.stdout)

                        # Check if versions are available
                        if "versions" in versions_data and versions_data["versions"]:
                            versions = versions_data["versions"]

                            # Create a table to display versions
                            try:
                                # Import pandas with a proper type ignore that won't trigger mypy warning
                                from typing import TYPE_CHECKING

                                if TYPE_CHECKING:
                                    import pandas as pd
                                else:
                                    import pandas as pd

                                # Extract relevant fields for the table
                                versions_table = []
                                for version in versions:
                                    versions_table.append(
                                        {
                                            "Number": version.get("number", ""),
                                            "Label": version.get("versionLabel", "")
                                            if version.get("versionLabel")
                                            else "-",
                                            "Notes": version.get("notes", "")
                                            if version.get("notes")
                                            else "-",
                                            "Created": version.get("createdAt", "")[:16]
                                            if version.get("createdAt")
                                            else "-",
                                            "ID": version.get("id", "")[:8] + "..."
                                            if version.get("id")
                                            else "-",
                                        }
                                    )

                                df = pd.DataFrame(versions_table)
                                st.dataframe(df, use_container_width=True, hide_index=True)
                            except ImportError:
                                # Fallback if pandas is not installed
                                st.warning("Pandas not installed. Displaying versions as a table.")
                                for version in versions:
                                    st.markdown(f"**Version {version.get('number', 'Unknown')}**")
                                    st.markdown(f"Label: {version.get('versionLabel', '-')}")
                                    st.markdown(f"Notes: {version.get('notes', '-')}")
                                    st.markdown(
                                        f"Created: {version.get('createdAt', '-')[:16] if version.get('createdAt') else '-'}"
                                    )
                                    st.markdown(f"ID: {version.get('id', '-')[:8]}...")
                                    st.markdown("---")
                        else:
                            st.info("No version history available for this agent")
                    except json.JSONDecodeError:
                        st.error("Failed to parse agent versions data")

        except Exception as e:
            st.error(f"Error fetching agent versions: {e}")

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
        print("[DEBUG] Back button clicked, setting nav_intent and current_page to Agents")
        # Give some time for the session state to update
        time.sleep(0.1)
        st.rerun()
