"""Agents page for the Agent Builder UI."""

import json
import subprocess
from typing import Any, cast

import streamlit as st

from ab_cli.abui.components.agent_card import agent_card

# Create a top-level cache dictionary to store results from CLI commands
cli_cache: dict[str, Any] = {
    "agents": None,
    "models": None,
    "guardrails": None,
}


def clear_cache() -> None:
    """Clear the CLI command cache."""
    global cli_cache
    cli_cache = {
        "agents": None,
        "models": None,
        "guardrails": None,
    }
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
    # Remove redundant subheader since we already have one in the parent function

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

    # Use the CLI to get the list of agents
    try:
        # In a real implementation, we would use the ab-cli as a library
        # For now, we'll simulate with placeholder data
        agents = get_agents()

        if not agents:
            st.info("No agents found. Create a new agent to get started.")
            return

        # Display agents based on selected view mode
        # Fix the type checking error by ensuring view_mode is not None
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
                unsafe_allow_html=True
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
                st.markdown(f"<span style='color:{color}; font-weight:bold;'>{agent_status}</span>", unsafe_allow_html=True)

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
            st.markdown('</div>', unsafe_allow_html=True)
            
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

    # Try to find JSON content in the text
    json_start = -1
    # Look for the first occurrence of { or [
    for i, c in enumerate(text):
        if c in "{[":
            json_start = i
            break

    if json_start == -1:
        if verbose:
            print("No JSON markers found in the text")
        return None

    # Extract text from the first JSON marker
    possible_json = text[json_start:]

    # Try to find where JSON content ends
    # This is more complex as we need to respect nesting
    stack = []
    json_end = -1

    # In case there are multiple JSON objects, try to find balanced braces
    for i, c in enumerate(possible_json):
        if c in "{[":
            stack.append(c)
        elif c == "}" and stack and stack[-1] == "{" or c == "]" and stack and stack[-1] == "[":
            stack.pop()
            if not stack:
                json_end = i + 1
                break

    if json_end == -1:
        # Couldn't find balanced ending, try a simpler approach
        closing_brace = possible_json.rfind("}")
        closing_bracket = possible_json.rfind("]")
        json_end = max(closing_brace, closing_bracket) + 1

    if json_end <= 0:
        if verbose:
            print("Couldn't find JSON end markers")
        return None

    json_str = possible_json[:json_end]

    if verbose:
        print(f"Extracted JSON string: {json_str}")

    try:
        return cast(dict[str, Any], json.loads(json_str))
    except json.JSONDecodeError as e:
        if verbose:
            print(f"Failed to parse JSON: {e}")
        return None


def get_agents() -> list[dict[str, Any]]:
    """Get the list of agents from the API.

    Uses the AgentBuilderClient to fetch the list of agents.

    Returns:
        List of agent dictionaries
    """
    # Check cache first
    global cli_cache
    if cli_cache["agents"] is not None:
        return cast(list[dict[str, Any]], cli_cache["agents"])

    try:
        # Get config and verbose flag from session state
        config = st.session_state.get("config")
        verbose = st.session_state.get("verbose", False)

        if not config:
            st.error("Configuration not loaded. Please check your settings.")
            raise ValueError("No configuration available")

        # Use the CLI directly
        # Run the CLI command to get agents with config at the top level
        cmd = ["ab"]

        # Add verbose flag if enabled - this needs to be at the top level
        if verbose:
            cmd.append("--verbose")

        # Add config path if available
        if hasattr(config, "config_path") and config.config_path:
            cmd.extend(["--config", str(config.config_path)])

        cmd.extend(["agents", "list", "--format", "json"])

        # Show the command in verbose mode
        if verbose:
            print(f"Executing command: {' '.join(cmd)}")

        try:
            cmd_str = " ".join(cmd)
            if verbose:
                print(f"Executing shell command: {cmd_str}")

            # Use a loading spinner while the command executes
            with st.spinner("Loading agents..."):
                result = subprocess.run(
                    cmd_str,
                    shell=True,  # Use shell to properly handle any special characters
                    capture_output=True,
                    text=True,
                    check=True,
                )

            # Log command output in verbose mode
            if verbose:
                if result.stdout:
                    print(f"Command stdout length: {len(result.stdout)} characters")
                if result.stderr:
                    print(f"Command stderr:\n{result.stderr}")

            # Parse the JSON output
            # In verbose mode, there might be debug output before the JSON
            if verbose:
                agents_data = extract_json_from_text(result.stdout, verbose)
                if not agents_data:
                    print("Could not parse JSON from output, using fallback")
                    # Fallback to placeholder data
                    return get_fallback_agents()
            else:
                try:
                    agents_data = cast(dict[str, Any], json.loads(result.stdout))
                except json.JSONDecodeError:
                    # If we can't parse the JSON directly, try to extract it
                    agents_data = extract_json_from_text(result.stdout, verbose)
                    if not agents_data:
                        print("Could not parse JSON from output, using fallback")
                        # Fallback to placeholder data
                        return get_fallback_agents()

            # Convert agents to our format
            agents: list[dict[str, Any]] = []
            if agents_data and "agents" in agents_data:
                for agent in agents_data["agents"]:
                    # No longer adding the model field since it's not used in the UI
                    agents.append(agent)

                # Cache the results
                cli_cache["agents"] = agents
                return agents
            else:
                st.warning("No agents found in API response")
                return []

        except subprocess.CalledProcessError as e:
            print(f"CLI command failed: {e}")
            print(f"Error details:\n{e.stderr}")
            raise

    except Exception as e:
        print(f"Error fetching agents: {e}")
        import traceback

        print(traceback.format_exc())

        # Fallback to placeholder data in case of error
        return get_fallback_agents()


def get_fallback_agents() -> list[dict[str, Any]]:
    """Return placeholder agent data for testing or when API fails."""
    st.warning("Using placeholder agent data")
    return [
        {
            "id": "agent-123",
            "name": "Demo Agent",
            "description": "A sample agent for demonstration purposes",
            "type": "chat",
            "model": "gpt-4",  # Use actual model name, not type
            "agent_config": {"model": "gpt-4"},
            "created_at": "2026-02-11T10:00:00Z",
        },
        {
            "id": "agent-456",
            "name": "Task Helper",
            "description": "Assists with task completion",
            "type": "task",
            "model": "claude-3",  # Use actual model name, not type
            "agent_config": {"model": "claude-3"},
            "created_at": "2026-02-10T14:30:00Z",
        },
    ]


def get_models() -> list[str]:
    """Get the list of available models from the CLI.

    Returns:
        List of model names
    """
    # Check cache first
    global cli_cache
    if cli_cache["models"] is not None:
        return cast(list[str], cli_cache["models"])

    try:
        # Get config and verbose flag from session state
        config = st.session_state.get("config")
        verbose = st.session_state.get("verbose", False)

        if not config:
            st.error("Configuration not loaded. Please check your settings.")
            return ["gpt-4", "gpt-3.5-turbo", "claude-3", "claude-2", "mistral-large"]

        # Use the CLI to get the models
        # Build the command
        cmd = ["ab"]

        # Add verbose flag if enabled
        if verbose:
            cmd.append("--verbose")

        # Add config path if available
        if hasattr(config, "config_path") and config.config_path:
            cmd.extend(["--config", str(config.config_path)])

        cmd.extend(["resources", "models", "--format", "json"])

        # Execute the command
        with st.spinner("Loading models..."):
            cmd_str = " ".join(cmd)
            if verbose:
                print(f"Executing shell command: {cmd_str}")

            result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                if verbose:
                    print(f"Command failed: {result.stderr}")
                # Fallback to placeholder data
                models = ["gpt-4", "gpt-3.5-turbo", "claude-3", "claude-2", "mistral-large"]
            else:
                # Parse the JSON output
                try:
                    if verbose:
                        models_data = extract_json_from_text(result.stdout, verbose)
                    else:
                        models_data = cast(dict[str, Any], json.loads(result.stdout))

                    if models_data and "models" in models_data:
                        models = [model["id"] for model in models_data["models"]]
                    else:
                        # Fallback
                        models = ["gpt-4", "gpt-3.5-turbo", "claude-3", "claude-2", "mistral-large"]
                except Exception as e:
                    if verbose:
                        print(f"Failed to parse models data: {e}")
                    # Fallback
                    models = ["gpt-4", "gpt-3.5-turbo", "claude-3", "claude-2", "mistral-large"]

        # Cache the results
        cli_cache["models"] = models
        return models

    except Exception as e:
        print(f"Error fetching models: {e}")
        # Fallback data
        return ["gpt-4", "gpt-3.5-turbo", "claude-3", "claude-2", "mistral-large"]


def get_guardrails() -> list[str]:
    """Get the list of available guardrails from the CLI.

    Returns:
        List of guardrail names
    """
    # Check cache first
    global cli_cache
    if cli_cache["guardrails"] is not None:
        return cast(list[str], cli_cache["guardrails"])

    try:
        # Get config and verbose flag from session state
        config = st.session_state.get("config")
        verbose = st.session_state.get("verbose", False)

        if not config:
            st.error("Configuration not loaded. Please check your settings.")
            return ["moderation", "pii-detection", "sensitive-topics", "custom-policy-1"]

        # Use the CLI to get the guardrails
        # Build the command
        cmd = ["ab"]

        # Add verbose flag if enabled
        if verbose:
            cmd.append("--verbose")

        # Add config path if available
        if hasattr(config, "config_path") and config.config_path:
            cmd.extend(["--config", str(config.config_path)])

        cmd.extend(["resources", "guardrails", "--format", "json"])

        # Execute the command
        with st.spinner("Loading guardrails..."):
            cmd_str = " ".join(cmd)
            if verbose:
                print(f"Executing shell command: {cmd_str}")

            result = subprocess.run(cmd_str, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                if verbose:
                    print(f"Command failed: {result.stderr}")
                # Fallback to placeholder data
                guardrails = ["moderation", "pii-detection", "sensitive-topics", "custom-policy-1"]
            else:
                # Parse the JSON output
                try:
                    if verbose:
                        guardrails_data = extract_json_from_text(result.stdout, verbose)
                    else:
                        guardrails_data = cast(dict[str, Any], json.loads(result.stdout))

                    if guardrails_data and "guardrails" in guardrails_data:
                        # Use 'name' field instead of 'id' as shown in the example JSON output
                        guardrails = [
                            guardrail["name"] for guardrail in guardrails_data["guardrails"]
                        ]
                    else:
                        # Fallback
                        guardrails = [
                            "moderation",
                            "pii-detection",
                            "sensitive-topics",
                            "custom-policy-1",
                        ]
                except Exception as e:
                    if verbose:
                        print(f"Failed to parse guardrails data: {e}")
                    # Fallback
                    guardrails = [
                        "moderation",
                        "pii-detection",
                        "sensitive-topics",
                        "custom-policy-1",
                    ]

        # Cache the results
        cli_cache["guardrails"] = guardrails
        return guardrails

    except Exception as e:
        print(f"Error fetching guardrails: {e}")
        # Fallback data
        return ["moderation", "pii-detection", "sensitive-topics", "custom-policy-1"]
