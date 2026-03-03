"""Edit Agent page for the Agent Builder UI."""

import json
from typing import Any

import streamlit as st

# Import functions from agents.py
from ab_cli.abui.views.agents import clear_cache, get_agent_types, get_guardrails, get_models

# Import Pydantic models
from ab_cli.models.agent import AgentCreate, AgentUpdate

# Import version utility
from ab_cli.utils.version import increment_version


def show_edit_agent_page() -> None:
    """Display the edit agent page."""
    # Check if we have an agent to edit
    agent_to_edit = st.session_state.get("agent_to_edit")

    # Normalize agent_to_edit: handle both Agent and AgentVersion objects
    # Chat view sends Agent objects, Agents list sends AgentVersion objects
    if agent_to_edit and not hasattr(agent_to_edit, "agent"):
        # It's an Agent object - we need to fetch it as AgentVersion
        # Get data provider first
        if "data_provider" not in st.session_state:
            config = st.session_state.get("config")
            if config:
                from ab_cli.abui.providers.provider_factory import get_data_provider
                st.session_state.data_provider = get_data_provider(config)

        provider = st.session_state.get("data_provider")
        if provider:
            try:
                agent_id = str(agent_to_edit.id)
                agent_to_edit = provider.get_agent(agent_id)
                st.session_state.agent_to_edit = agent_to_edit  # Update session state
            except Exception as e:
                st.error(f"Failed to load agent details: {e}")
                agent_to_edit = None

    if agent_to_edit:
        # agent_to_edit is now guaranteed to be AgentVersion with .agent and .version
        agent_name = agent_to_edit.agent.name if hasattr(agent_to_edit, "agent") else "Unknown Agent"
        st.title(f"Edit Agent: {agent_name}")
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

    # Always fetch fresh data from server when editing to ensure we have latest config
    latest_version_label = None
    if agent_to_edit:
        with st.spinner("Loading latest agent configuration..."):
            try:
                agent_id = str(agent_to_edit.agent.id)
                fresh_agent_data = provider.get_agent(agent_id)
                if fresh_agent_data:
                    # Update with fresh data (AgentVersion object)
                    agent_to_edit = fresh_agent_data
                    st.session_state.agent_to_edit = fresh_agent_data

                    # Also fetch version history to get the actual latest version label
                    try:
                        versions_data = provider.get_versions(agent_id, limit=100, offset=0)
                        if versions_data and versions_data.versions:
                            # Get the last version (most recent)
                            latest_version = versions_data.versions[-1]
                            latest_version_label = latest_version.version_label
                    except Exception:
                        # If we can't get versions, fall back to agent's version_label
                        pass
                else:
                    st.warning("Could not load latest configuration, using cached data")
            except Exception as e:
                st.error(f"Error loading latest configuration: {e}")
                # Continue with cached data

    # Fetch models, guardrails, and agent types BEFORE creating the form
    # This prevents Streamlit from hanging inside the form
    models = get_models()
    guardrails = get_guardrails()
    agent_types = get_agent_types()

    # Get default values from agent_to_edit if available
    default_name = agent_to_edit.agent.name if agent_to_edit else ""
    default_description = agent_to_edit.agent.description if agent_to_edit else ""
    default_type = agent_to_edit.agent.type if agent_to_edit else "chat"
    default_model = ""

    # Extract configuration values if we're editing
    agent_config: dict[str, Any] = {}
    if agent_to_edit and agent_to_edit.version.config:
        agent_config = agent_to_edit.version.config

    # Get model from agent_config if available, otherwise use default_model
    current_model = agent_config.get("llmModelId", default_model)
    model_index = models.index(current_model) if current_model in models else 0

    # Get default guardrails
    default_guardrails = agent_config.get("guardrails", [])

    # Calculate default system prompt BEFORE the form
    # Use existing prompt if editing, or simple default if creating
    if agent_to_edit and agent_config:
        default_prompt = agent_config.get("systemPrompt", "")
    else:
        # For new agents, provide a simple default that user will customize
        default_prompt = "You are a helpful assistant."

    # Create a form for agent creation or editing
    with st.form("agent_form"):
        # Basic agent information with default values
        name = st.text_input("Agent Name", value=default_name)
        description = st.text_area("Description", value=default_description)

        # Agent type (fetched dynamically from API)
        agent_type = st.selectbox(
            "Agent Type",
            options=agent_types,
            index=agent_types.index(default_type) if default_type in agent_types else 0,
        )

        # Model selection (using pre-fetched models list)
        model = st.selectbox("Model", options=models, index=model_index)

        # System prompt - use the pre-calculated default
        system_prompt = st.text_area("System Prompt", value=default_prompt, height=150)

        # Guardrails selection (using pre-fetched guardrails list)
        selected_guardrails = st.multiselect(
            "Guardrails",
            options=guardrails,
            default=default_guardrails if all(g in guardrails for g in default_guardrails) else [],
        )

        # RAG Parameters Section (only for RAG agents)
        if agent_type == "rag":
            st.markdown("---")
            st.markdown("### 🔍 RAG Parameters")

            col1, col2, col3 = st.columns(3)

            with col1:
                hxql_query = st.text_input(
                    "HXQL Query",
                    value=agent_config.get("hxqlQuery", ""),
                    help="Hyland Query Language query for filtering results",
                )

                hybrid_search = st.checkbox(
                    "Hybrid Search",
                    value=agent_config.get("hybridSearch", False),
                    help="Enable hybrid search combining multiple search strategies",
                )

                enable_deep_search = st.checkbox(
                    "Enable Deep Search",
                    value=agent_config.get("enableDeepSearch", False),
                    help="Enable deep search for more thorough results",
                )

            with col2:
                limit = st.number_input(
                    "Chunk Limit",
                    min_value=1,
                    max_value=100,
                    value=agent_config.get("limit", 10),
                    help="Maximum number of chunks to retrieve",
                )

                adjacent_range = st.number_input(
                    "Adjacent Embedding Range",
                    min_value=0,
                    max_value=10,
                    value=agent_config.get("adjacentEmbeddingRange", 0),
                    help="Number of adjacent chunks to fetch (0 = disabled)",
                )

                adjacent_merge = st.checkbox(
                    "Merge Adjacent Chunks",
                    value=agent_config.get("adjacentEmbeddingMerge", False),
                    help="Merge adjacent chunks into parent document",
                )

            with col3:
                reranker_enabled = st.checkbox(
                    "Enable Reranker",
                    value=agent_config.get("rerankerEnabled", False),
                    help="Enable reranker post-processing",
                )

                reranker_top_n = st.number_input(
                    "Reranker Top N",
                    min_value=1,
                    max_value=50,
                    value=agent_config.get("rerankerTopN", 5),
                    help="Top N results after reranking",
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

        # Version information (for updates)
        st.markdown("---")
        if agent_to_edit:
            st.markdown("### Version Information")

            # Use latest version from version history if available, otherwise fall back to agent's version_label
            current_version = latest_version_label or agent_to_edit.version.version_label or "v1.0"

            default_new_version = increment_version(current_version)

            col_v1, col_v2 = st.columns(2)
            with col_v1:
                version_label = st.text_input(
                    "Version Label",
                    value=default_new_version,
                    help=f"Auto-incremented from latest version: {current_version}. Edit if needed.",
                )
            with col_v2:
                version_notes = st.text_input(
                    "Version Notes",
                    value="Updated via UI",
                    help="Brief description of changes in this version",
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

                    # Add RAG parameters directly to agent_config if agent type is rag
                    if agent_type == "rag":
                        # Add all RAG parameters directly to the config (using camelCase for API)
                        if hxql_query:  # Only add if not empty
                            agent_config["hxqlQuery"] = hxql_query
                        agent_config["hybridSearch"] = hybrid_search
                        agent_config["enableDeepSearch"] = enable_deep_search
                        agent_config["limit"] = limit
                        agent_config["adjacentEmbeddingRange"] = adjacent_range
                        agent_config["adjacentEmbeddingMerge"] = adjacent_merge
                        agent_config["rerankerEnabled"] = reranker_enabled
                        agent_config["rerankerTopN"] = reranker_top_n

                    # Add input schema if provided and agent type is task
                    if agent_type == "task" and schema_json.strip():
                        agent_config["inputSchema"] = input_schema

                    # Determine action type before attempting operation
                    action_type = "update" if agent_to_edit else "create"

                    # Use data provider to create/update agent
                    with st.spinner(f"{'Updating' if agent_to_edit else 'Creating'} agent..."):
                        try:
                            if agent_to_edit:
                                # Update existing agent - create AgentUpdate model
                                agent_id = str(agent_to_edit.agent.id)
                                agent_update = AgentUpdate(
                                    config=agent_config,
                                    version_label=version_label,
                                    notes=version_notes,
                                )
                                provider.update_agent(agent_id, agent_update)
                            else:
                                # Create new agent - create AgentCreate model
                                agent_create = AgentCreate(
                                    name=name,
                                    description=description,
                                    agent_type=agent_type,
                                    config=agent_config,
                                    version_label="v1.0",
                                    notes="Initial version",
                                )
                                provider.create_agent(agent_create)

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
