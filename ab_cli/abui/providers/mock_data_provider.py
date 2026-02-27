"""Mock data provider implementation for the Agent Builder UI.

This provider uses predefined data from JSON files and converts them to
strongly-typed Pydantic models for compatibility with the DataProvider interface.
"""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, cast

from ab_cli.abui.providers.data_provider import DataProvider
from ab_cli.api.pagination import PaginatedResult
from ab_cli.models.agent import Agent, AgentVersion, Pagination, Version, VersionConfig, VersionList
from ab_cli.models.invocation import InvokeResponse
from ab_cli.models.resources import (
    GuardrailList,
    GuardrailModel,
    LLMModel,
    LLMModelList,
)


class MockDataProvider(DataProvider):
    """Data provider that uses predefined data from JSON files.

    This provider loads mock data and converts it to strongly-typed Pydantic models
    for testing and demonstration purposes.
    """

    def __init__(self, config: Any = None, data_dir: str | None = None):
        """Initialize with path to data directory.

        Args:
            config: Configuration object with necessary settings
            data_dir: Directory containing mock data files (optional)
        """
        # Default to data directory in the package
        if data_dir is None and config and hasattr(config, "ui"):
            data_dir = getattr(config.ui, "mock_data_dir", None)

        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")

        self.data_dir = data_dir
        self.verbose = getattr(config, "verbose", False) if config else False

        # Cache for loaded data
        self.cache: dict[str, Any] = {}

    def _load_json_file(self, filename: str) -> Any:
        """Load and parse a JSON file.

        Args:
            filename: Name of the JSON file to load

        Returns:
            Parsed JSON content
        """
        file_path = os.path.join(self.data_dir, filename)
        try:
            with open(file_path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            if self.verbose:
                print(f"Error loading {filename}: {str(e)}")
            raise RuntimeError(f"Error loading {filename}: {str(e)}")

    def clear_cache(self) -> None:
        """Clear the data cache."""
        self.cache = {}
        if self.verbose:
            print("Cache cleared")

    def get_agents(self) -> list[Agent]:
        """Get list of available agents.

        Returns:
            List of Agent objects with basic metadata.
        """
        # Check cache first
        if "agents" in self.cache:
            return cast(list[Agent], self.cache["agents"])

        # Load agents from JSON file
        data = self._load_json_file("agents.json")
        agents_data = data.get("agents", [])

        # Convert to Agent models
        agents = [Agent.model_validate(agent_data) for agent_data in agents_data]

        # Cache the results
        self.cache["agents"] = agents
        return agents

    def get_agents_paginated(self, limit: int, offset: int) -> PaginatedResult:
        """Get paginated list of agents.

        Args:
            limit: Maximum number of agents to return
            offset: Number of agents to skip

        Returns:
            PaginatedResult with agents list and metadata
        """
        # Get all agents
        all_agents = self.get_agents()
        total = len(all_agents)

        # Apply pagination
        start = offset
        end = min(offset + limit, total)
        page_agents = all_agents[start:end]

        # Return paginated result
        return PaginatedResult(
            agents=page_agents,
            offset=offset,
            limit=limit,
            total_count=total,
            has_filters=False,
            agent_type=None,
            name_pattern=None,
        )

    def get_agent(self, agent_id: str) -> AgentVersion | None:
        """Get agent details with current version configuration.

        Args:
            agent_id: The ID of the agent to retrieve.

        Returns:
            AgentVersion object containing agent metadata and version config,
            or None if agent not found.
        """
        # Get all agents and find the one with matching ID
        agents = self.get_agents()
        for agent in agents:
            if str(agent.id) == agent_id:
                # Load version data for this agent
                try:
                    versions_response = self.get_versions(agent_id, limit=1, offset=0)
                    if versions_response.versions:
                        latest_version = versions_response.versions[0]
                        # Convert Version to VersionConfig by adding empty config
                        version_config = VersionConfig(
                            id=latest_version.id,
                            number=latest_version.number,
                            version_label=latest_version.version_label,
                            notes=latest_version.notes,
                            created_at=latest_version.created_at,
                            created_by=latest_version.created_by,
                            config={},  # Version doesn't have config, so use empty dict
                        )
                        return AgentVersion(
                            agent=agent,
                            version=version_config,
                        )
                    else:
                        # No versions, create a default one
                        default_version = VersionConfig(
                            id=str(uuid.uuid4()),  # type: ignore[arg-type]
                            number=1,
                            version_label="v1.0.0",
                            notes="Initial version",
                            created_at=agent.created_at,
                            created_by="system",
                            config={},
                        )
                        return AgentVersion(
                            agent=agent,
                            version=default_version,
                        )
                except Exception:
                    # If version loading fails, return agent with minimal version
                    default_version = VersionConfig(
                        id=str(uuid.uuid4()),  # type: ignore[arg-type]
                        number=1,
                        version_label="v1.0.0",
                        notes="Initial version",
                        created_at=agent.created_at,
                        created_by="system",
                        config={},
                    )
                    return AgentVersion(
                        agent=agent,
                        version=default_version,
                    )
        return None

    def create_agent(self, agent_data: dict) -> AgentVersion:
        """Create a new agent.

        Args:
            agent_data: Dictionary containing agent creation data.

        Returns:
            AgentVersion object for the newly created agent.
        """
        # Validate required fields
        required_fields = ["name", "type"]
        for field in required_fields:
            if field not in agent_data:
                raise ValueError(f"Missing required field: {field}")

        # Generate proper UUIDs
        new_id = str(uuid.uuid4())
        version_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat() + "Z"

        # Create the new agent object with all required fields
        new_agent = Agent(
            id=new_id,  # type: ignore[arg-type]
            name=str(agent_data.get("name", "")),
            description=agent_data.get("description", ""),
            type=str(agent_data.get("type", "chat")),
            status=agent_data.get("status", "CREATED"),
            is_global_agent=agent_data.get("isGlobalAgent", False),
            current_version_id=version_id,  # type: ignore[arg-type]
            created_at=created_at,
            created_by=agent_data.get("created_by", "system"),
            modified_at=created_at,
            modified_by=agent_data.get("modified_by", "system"),
        )

        # Create initial version - use VersionConfig which includes config field
        version = VersionConfig(
            id=version_id,  # type: ignore[arg-type]
            number=1,
            version_label=agent_data.get("version_label", "v1.0.0"),
            notes=agent_data.get("notes", "Initial version"),
            created_at=created_at,
            created_by=agent_data.get("created_by", "system"),
            config=agent_data.get("config", {}),
        )

        # Add to cache
        if "agents" in self.cache:
            self.cache["agents"].append(new_agent)

        if self.verbose:
            print(f"Created mock agent: {new_id}")

        return AgentVersion(agent=new_agent, version=version)

    def update_agent(self, agent_id: str, agent_data: dict) -> AgentVersion:
        """Update an existing agent (creates a new version).

        Args:
            agent_id: The ID of the agent to update.
            agent_data: Dictionary containing update data.

        Returns:
            AgentVersion object with the new version.
        """
        # Get the agent
        agents = self.get_agents()
        agent = None
        for a in agents:
            if str(a.id) == agent_id:
                agent = a
                break

        if agent is None:
            raise ValueError(f"Agent with ID {agent_id} not found")

        # Create new version
        created_at = datetime.now(timezone.utc).isoformat() + "Z"

        # Get existing versions to determine next version number
        versions_response = self.get_versions(agent_id, limit=1)
        next_number = 1
        if versions_response.versions:
            next_number = versions_response.versions[0].number + 1

        new_version = VersionConfig(
            id=str(uuid.uuid4()),  # type: ignore[arg-type]
            number=next_number,
            version_label=agent_data.get("version_label", f"v1.0.{next_number}"),
            notes=agent_data.get("notes", f"Version {next_number}"),
            created_at=created_at,
            created_by="system",
            config=agent_data.get("config", {}),
        )

        if self.verbose:
            print(f"Updated mock agent: {agent_id} (version {next_number})")

        return AgentVersion(agent=agent, version=new_version)

    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent by ID.

        Args:
            agent_id: The ID of the agent to delete.

        Returns:
            True if deletion successful, False otherwise.
        """
        # Get all agents
        agents = self.get_agents() if "agents" not in self.cache else self.cache["agents"]

        # Find and remove the agent
        for idx, agent in enumerate(agents):
            if str(agent.id) == agent_id:
                agents.pop(idx)
                self.cache["agents"] = agents
                if self.verbose:
                    print(f"Deleted mock agent: {agent_id}")
                return True

        return False

    def invoke_agent(self, agent_id: str, message: str, agent_type: str = "chat") -> InvokeResponse:
        """Invoke an agent with a message.

        Args:
            agent_id: The ID of the agent to invoke.
            message: The message to send (for chat) or task data JSON (for task).
            agent_type: Type of agent ("chat", "rag", "tool", "task").

        Returns:
            InvokeResponse containing the agent's response and metadata.
        """
        # Get the agent to check if it exists
        agent_version = self.get_agent(agent_id)
        if not agent_version:
            # Return error response
            return InvokeResponse(
                answer=f"Error: Agent with ID {agent_id} not found",
                metadata={},
            )

        agent = agent_version.agent
        agent_name = agent.name

        # Use a dictionary for agent response types
        responses = {
            "chat": f"This is a mock response from {agent_name}. You said: '{message}'",
            "task": f"I'll help you complete that task. Here's a step-by-step plan for '{message}':\n\n1. First step\n2. Second step\n3. Third step",
            "rag": f"Based on the documents I retrieved for '{message}', here is the information you're looking for...",
        }

        # Get response by type or use default
        response_text = responses.get(
            agent_type,
            f"Mock response from {agent_type} agent '{agent_name}': Received your message: '{message}'",
        )

        return InvokeResponse(
            answer=response_text,
            metadata={
                "agent_id": agent_id,
                "agent_name": agent_name,
                "agent_type": agent_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    def get_versions(self, agent_id: str, limit: int = 50, offset: int = 0) -> VersionList:
        """Get list of versions for an agent.

        Args:
            agent_id: The ID of the agent.
            limit: Maximum number of versions to return.
            offset: Offset for pagination.

        Returns:
            VersionList containing versions and pagination metadata.
        """
        try:
            # Get the agent first
            agent = None
            agents = self.get_agents()
            for a in agents:
                if str(a.id) == agent_id:
                    agent = a
                    break

            # If agent not found, create a minimal one
            if agent is None:
                agent = Agent(
                    id=agent_id,  # type: ignore[arg-type]
                    name="Unknown Agent",
                    description="",
                    type="chat",
                    status="CREATED",
                    is_global_agent=False,
                    current_version_id=None,
                    created_at=datetime.now(timezone.utc).isoformat() + "Z",
                    created_by="system",
                    modified_at=datetime.now(timezone.utc).isoformat() + "Z",
                    modified_by="system",
                )

            # Load versions from JSON file
            data = self._load_json_file("versions.json")
            all_versions_data = data.get("versions", [])

            # Filter versions for this agent
            agent_versions_data = [v for v in all_versions_data if v.get("agent_id") == agent_id]

            # Sort by version number (descending - newest first)
            agent_versions_data.sort(key=lambda v: v.get("number", 0), reverse=True)

            # Apply pagination
            total_items = len(agent_versions_data)
            paginated_versions_data = agent_versions_data[offset : offset + limit]

            # Convert to Version models
            versions = [Version.model_validate(v) for v in paginated_versions_data]

            # Create pagination metadata
            pagination = Pagination(
                limit=limit,
                offset=offset,
                total_items=total_items,
            )

            return VersionList(versions=versions, pagination=pagination, agent=agent)

        except Exception as e:
            if self.verbose:
                print(f"Error loading versions: {e}")
            # Create a minimal agent for error case
            error_agent = Agent(
                id=agent_id,  # type: ignore[arg-type]
                name="Unknown Agent",
                description="",
                type="chat",
                status="CREATED",
                is_global_agent=False,
                current_version_id=None,
                created_at=datetime.now(timezone.utc).isoformat() + "Z",
                created_by="system",
                modified_at=datetime.now(timezone.utc).isoformat() + "Z",
                modified_by="system",
            )
            # Return empty list on error
            return VersionList(
                versions=[],
                pagination=Pagination(limit=limit, offset=offset, total_items=0),
                agent=error_agent,
            )

    def get_version(self, agent_id: str, version_id: str) -> Version | None:
        """Get details of a specific version with full configuration.

        Args:
            agent_id: The ID of the agent.
            version_id: The ID of the version (or "latest").

        Returns:
            Version object with full configuration, or None if not found.
        """
        try:
            # Load versions from JSON file
            data = self._load_json_file("versions.json")
            all_versions_data = data.get("versions", [])

            # Handle "latest" version request
            if version_id == "latest":
                agent_versions = [v for v in all_versions_data if v.get("agent_id") == agent_id]
                if not agent_versions:
                    return None
                # Sort by version number and get the latest
                agent_versions.sort(key=lambda v: v.get("number", 0), reverse=True)
                version_data = agent_versions[0]
            else:
                # Find specific version
                version_data = None
                for v in all_versions_data:
                    if v.get("id") == version_id and v.get("agent_id") == agent_id:
                        version_data = v
                        break

                if not version_data:
                    return None

            # Convert to Version model
            return Version.model_validate(version_data)

        except Exception as e:
            if self.verbose:
                print(f"Error loading version: {e}")
            return None

    def get_models(self, limit: int = 100, offset: int = 0) -> LLMModelList:
        """Get list of available LLM models.

        Args:
            limit: Maximum number of models to return.
            offset: Offset for pagination.

        Returns:
            LLMModelList containing available models.
        """
        # Check cache first
        cache_key = f"models_{limit}_{offset}"
        if cache_key in self.cache:
            return cast(LLMModelList, self.cache[cache_key])

        try:
            # Load models from JSON file
            data = self._load_json_file("models.json")
            all_models_data = data.get("models", [])

            # Apply pagination
            total = len(all_models_data)
            paginated_models_data = all_models_data[offset : offset + limit]

            # Convert to LLMModel objects
            models = [LLMModel.model_validate(m) for m in paginated_models_data]

            # Create pagination
            pagination = Pagination(limit=limit, offset=offset, total_items=total)

            result = LLMModelList(models=models, pagination=pagination)

            # Cache the results
            self.cache[cache_key] = result
            return result

        except Exception as e:
            if self.verbose:
                print(f"Error loading models: {e}")
            # Fallback to default models
            fallback_models = [
                LLMModel(
                    id="gpt-4",
                    name="GPT-4",
                    description="OpenAI GPT-4 model",
                    badge="",
                    metadata="",
                    agent_types=["chat", "rag", "tool"],
                    capabilities={},
                    regions=["us-east-1"],
                ),
                LLMModel(
                    id="gpt-3.5-turbo",
                    name="GPT-3.5 Turbo",
                    description="OpenAI GPT-3.5 Turbo model",
                    badge="",
                    metadata="",
                    agent_types=["chat", "rag", "tool"],
                    capabilities={},
                    regions=["us-east-1"],
                ),
                LLMModel(
                    id="claude-3",
                    name="Claude 3",
                    description="Anthropic Claude 3 model",
                    badge="",
                    metadata="",
                    agent_types=["chat", "rag", "tool"],
                    capabilities={},
                    regions=["us-east-1"],
                ),
            ]
            pagination = Pagination(limit=limit, offset=offset, total_items=len(fallback_models))
            return LLMModelList(models=fallback_models, pagination=pagination)

    def get_guardrails(self, limit: int = 100, offset: int = 0) -> GuardrailList:
        """Get list of available guardrails.

        Args:
            limit: Maximum number of guardrails to return.
            offset: Offset for pagination.

        Returns:
            GuardrailList containing available guardrails.
        """
        # Check cache first
        cache_key = f"guardrails_{limit}_{offset}"
        if cache_key in self.cache:
            return cast(GuardrailList, self.cache[cache_key])

        try:
            # Load guardrails from JSON file
            data = self._load_json_file("guardrails.json")
            all_guardrails_data = data.get("guardrails", [])

            # Apply pagination
            total = len(all_guardrails_data)
            paginated_guardrails_data = all_guardrails_data[offset : offset + limit]

            # Convert to GuardrailModel objects
            guardrails = [GuardrailModel.model_validate(g) for g in paginated_guardrails_data]

            # Create pagination
            pagination = Pagination(limit=limit, offset=offset, total_items=total)

            result = GuardrailList(guardrails=guardrails, pagination=pagination)

            # Cache the results
            self.cache[cache_key] = result
            return result

        except Exception as e:
            if self.verbose:
                print(f"Error loading guardrails: {e}")
            # Fallback to default guardrails
            fallback_guardrails = [
                GuardrailModel(name="moderation", description="Content moderation"),
                GuardrailModel(name="pii-detection", description="PII detection"),
            ]
            pagination = Pagination(
                limit=limit, offset=offset, total_items=len(fallback_guardrails)
            )
            return GuardrailList(guardrails=fallback_guardrails, pagination=pagination)

    def health_check(self) -> bool:
        """Check if the data provider is healthy.

        Returns:
            True if healthy, False otherwise.
        """
        # Mock data provider is always healthy
        return True
