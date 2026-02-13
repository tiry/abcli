"""Edit Agent page for the Agent Builder UI."""

import contextlib
import json
import os
import subprocess
import tempfile
from typing import Any

import streamlit as st

# Import the model and guardrail functions from agents.py to use the cache
from ab_cli.abui.views.agents import clear_cache, get_guardrails, get_models


def show_edit_agent_page() -> None:
    """Display the edit agent page."""
    # Check if we have an agent to edit
    agent_to_edit = st.session_state.get("agent_to_edit")

    if agent_to_edit:
        st.title(f"Edit Agent: {agent_to_edit.get('name', 'Unknown Agent')}")
    else:
        st.title("Create New Agent")

    # Create a form for agent creation or editing
    with st.form("agent_form"):
        # Get default values from agent_to_edit if available
        default_name = agent_to_edit.get("name", "") if agent_to_edit else ""
        default_description = agent_to_edit.get("description", "") if agent_to_edit else ""
        default_type = agent_to_edit.get("type", "chat") if agent_to_edit else "chat"
        default_model = agent_to_edit.get("model", "") if agent_to_edit else ""

        # Extract configuration values if we're editing
        agent_config: dict[str, Any] = {}
        if agent_to_edit and "agent_config" in agent_to_edit:
            agent_config = agent_to_edit["agent_config"]

        # Basic agent information with default values
        name = st.text_input("Agent Name", value=default_name)
        description = st.text_area("Description", value=default_description)

        # Agent type (hard-coded options)
        agent_type = st.selectbox(
            "Agent Type",
            options=["chat", "task", "qa", "rag", "custom"],
            index=["chat", "task", "qa", "rag", "custom"].index(default_type)
            if default_type in ["chat", "task", "qa", "rag", "custom"]
            else 0,
        )

        # Model selection (fetched from CLI)
        models = get_models()
        # Get model from agent_config if available, otherwise use default_model
        current_model = agent_config.get("llmModelId", default_model)
        model_index = models.index(current_model) if current_model in models else 0
        model = st.selectbox("Model", options=models, index=model_index)

        # System prompt - load from agent_config if available
        default_prompt = agent_config.get(
            "systemPrompt", f"You are a {agent_type} assistant named {name}."
        )
        system_prompt = st.text_area("System Prompt", value=default_prompt, height=150)

        # Guardrails selection (fetched from CLI)
        guardrails = get_guardrails()
        default_guardrails = agent_config.get("guardrails", [])
        selected_guardrails = st.multiselect(
            "Guardrails",
            options=guardrails,
            default=default_guardrails if all(g in guardrails for g in default_guardrails) else [],
        )

        # Advanced configuration sections with JSON editors
        st.markdown("---")
        st.markdown("### Advanced Configuration")

        with st.expander("Inference Configuration", expanded=False):
            # Default inference config
            default_inference = {
                "temperature": 0.0,
                "maxRetries": 3,
                "timeout": 1800,
                "maxTokens": 4000,
            }
            # Use existing inference config if available
            current_inference = agent_config.get("inferenceConfig", default_inference)
            inference_json = st.text_area(
                "Inference Configuration (JSON)",
                value=json.dumps(current_inference, indent=2),
                height=200,
            )

        with st.expander("Tools Configuration", expanded=False):
            # Default empty tools array
            default_tools: list[dict[str, Any]] = []
            # Use existing tools if available
            current_tools = agent_config.get("tools", default_tools)
            tools_json = st.text_area(
                "Tools Configuration (JSON)", value=json.dumps(current_tools, indent=2), height=300
            )

        with st.expander("Input Schema (for Task Agents)", expanded=False):
            # Default empty input schema
            default_schema = {"type": "object", "properties": {}, "required": []}
            # Use existing input schema if available
            current_schema = agent_config.get("inputSchema", default_schema)
            schema_json = st.text_area(
                "Input Schema Configuration (JSON)",
                value=json.dumps(current_schema, indent=2),
                height=300,
            )

        # Create columns for submit and cancel buttons
        st.markdown("---")
        col1, col2 = st.columns([1, 1])

        with col1:
            # Submit button text based on mode
            submit_text = "Update Agent" if agent_to_edit else "Create Agent"
            submitted = st.form_submit_button(submit_text)

        with col2:
            # The "cancel" button needs to be outside the form since forms only allow one submit button
            # We'll implement its logic after the form
            pass

        if submitted:
            if not name:
                st.error("Agent name is required")
            else:
                try:
                    # Get configuration from session state
                    config = st.session_state.get("config")
                    verbose = st.session_state.get("verbose", False)

                    if not config:
                        st.error("Configuration not loaded. Please check your settings.")
                        return

                    # Parse the JSON inputs
                    try:
                        inference_config = json.loads(inference_json)
                        tools = json.loads(tools_json)
                        input_schema = json.loads(schema_json) if schema_json.strip() else {}
                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON in configuration: {str(e)}")
                        return

                    # Create agent configuration JSON
                    agent_config = {
                        "llmModelId": model,
                        "systemPrompt": system_prompt,
                        "inferenceConfig": inference_config,
                        "tools": tools,
                    }

                    # Add guardrails if selected
                    if selected_guardrails:
                        agent_config["guardrails"] = selected_guardrails

                    # Add input schema if provided and agent type is task
                    if agent_type == "task" and schema_json.strip():
                        agent_config["inputSchema"] = input_schema

                    # Create a temporary file for the config
                    with tempfile.NamedTemporaryFile(
                        mode="w", suffix=".json", delete=False
                    ) as tmp_config:
                        json.dump(agent_config, tmp_config, indent=2)
                        tmp_config_path = tmp_config.name

                    try:
                        # Build the CLI command based on whether we're creating or updating
                        cmd = ["ab"]

                        # Add verbose flag if enabled
                        if verbose:
                            cmd.append("--verbose")

                        # Add config path if available
                        if hasattr(config, "config_path") and config.config_path:
                            cmd.extend(["--config", str(config.config_path)])

                        if agent_to_edit:
                            # Update existing agent
                            cmd.extend(
                                [
                                    "agents",
                                    "update",
                                    agent_to_edit["id"],
                                    "--agent-config",
                                    tmp_config_path,
                                    "--version-label",
                                    "v2.0",  # You could make this dynamic
                                    "--notes",
                                    "UpdatedViaUI",
                                ]
                            )
                            action_type = "update"
                        else:
                            # Create new agent
                            cmd.extend(
                                [
                                    "agents",
                                    "create",
                                    "--name",
                                    name,
                                    "--description",
                                    description if description else "",
                                    "--type",
                                    agent_type,
                                    "--agent-config",
                                    tmp_config_path,
                                    "--version-label",
                                    "v1.0",  # You could make this dynamic
                                    "--notes",
                                    "Initial version",
                                ]
                            )
                            action_type = "create"

                        # Execute the command with a loading spinner
                        with st.spinner(f"{'Updating' if agent_to_edit else 'Creating'} agent..."):
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
                                    print(f"Command failed with return code {result.returncode}")
                                    print(f"STDERR: {result.stderr}")
                                    print(f"STDOUT: {result.stdout}")

                                # Show error details in the UI
                                st.error(f"Failed to {action_type} agent")
                                with st.expander("Error Details", expanded=True):
                                    st.markdown("### Command Output")
                                    if result.stdout:
                                        st.markdown("**Standard Output:**")
                                        st.code(result.stdout)

                                    if result.stderr:
                                        st.markdown("**Error Output:**")
                                        st.code(result.stderr)
                                    else:
                                        st.markdown("*No error output was returned.*")

                                    st.markdown("**Command Used:**")
                                    st.code(" ".join(cmd))

                                # Display the agent configuration that was attempted
                                with st.expander("Configuration Attempted", expanded=False):
                                    st.json(agent_config)
                            else:
                                st.success(f"Agent '{name}' {action_type}d successfully!")

                                # Clear the agent listing cache before returning
                                clear_cache()

                                # Return to agents list
                                st.session_state.agent_to_edit = None
                                st.session_state.nav_intent = "Agents"
                                st.rerun()

                    finally:
                        # Clean up the temporary file - using contextlib.suppress to properly handle exceptions
                        with contextlib.suppress(FileNotFoundError, PermissionError):
                            os.unlink(tmp_config_path)
                except Exception as e:
                    st.error(f"Error {'updating' if agent_to_edit else 'creating'} agent: {e}")

    # Cancel button (outside the form)
    if st.button("Cancel", key="cancel_edit"):
        # Clear the agent_to_edit from session state
        st.session_state.agent_to_edit = None
        # Clear the cache to ensure fresh data when returning to agents list
        clear_cache()
        # Navigate back to agents list
        st.session_state.nav_intent = "Agents"
        st.rerun()


# These functions are now imported from agents.py to use the shared cache
