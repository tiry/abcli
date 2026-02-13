"""Edit Agent page for the Agent Builder UI."""

import json
from typing import Any

import streamlit as st

# Import functions from agents.py
from ab_cli.abui.views.agents import clear_cache, get_guardrails, get_models


def show_edit_agent_page() -> None:
    """Display the edit agent page."""
    # Check if we have an agent to edit
    agent_to_edit = st.session_state.get("agent_to_edit")

    if agent_to_edit:
        st.title(f"Edit Agent: {agent_to_edit.get('name', 'Unknown Agent')}")
    else:
        st.title("Create New Agent")

    # Get data provider from session state
    if "data_provider" not in st.session_state:
        # Get configuration from session state
        config = st.session_state.get("config")
        if not config:
            st.error("Configuration not loaded. Please check your settings.")
            return

        # Create data provider
        from ab_cli.abui.providers.provider_factory import get_data_provider

        st.session_state.data_provider = get_data_provider(config)

    provider = st.session_state.data_provider

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

        # Model selection (fetched from data provider)
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

        # Guardrails selection (fetched from data provider)
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
            pass

        if submitted:
            if not name:
                st.error("Agent name is required")
            else:
                try:
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

                    # Create the agent data dictionary
                    agent_data = {
                        "name": name,
                        "description": description,
                        "type": agent_type,
                        "agent_config": agent_config,
                    }

                    # Add version information for updates
                    if agent_to_edit:
                        agent_data["version_label"] = "v2.0"
                        agent_data["notes"] = "UpdatedViaUI"
                    else:
                        agent_data["version_label"] = "v1.0"
                        agent_data["notes"] = "Initial version"

                    # Use data provider to create/update agent
                    with st.spinner(f"{'Updating' if agent_to_edit else 'Creating'} agent..."):
                        try:
                            if agent_to_edit:
                                # Update existing agent
                                provider.update_agent(agent_to_edit["id"], agent_data)
                                action_type = "update"
                            else:
                                # Create new agent
                                provider.create_agent(agent_data)
                                action_type = "create"

                            # Success!
                            st.success(f"Agent '{name}' {action_type}d successfully!")

                            # Clear the cache before returning
                            clear_cache()

                            # Return to agents list
                            st.session_state.agent_to_edit = None
                            st.session_state.nav_intent = "Agents"
                            st.rerun()

                        except Exception as e:
                            # Show error details in the UI
                            st.error(f"Failed to {action_type} agent: {str(e)}")

                            # Display the agent configuration that was attempted
                            with st.expander("Configuration Attempted", expanded=False):
                                st.json(agent_config)

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
