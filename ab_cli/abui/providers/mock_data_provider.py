"""Mock data provider implementation for the Agent Builder UI."""

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any, cast

from ab_cli.abui.providers.data_provider import DataProvider
from ab_cli.api.pagination import PaginatedResult


class MockDataProvider(DataProvider):
    """Data provider that uses predefined data from JSON files."""

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
        self.agents_cache: list[dict[str, Any]] = []

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

    def get_agents(self) -> list[dict[str, Any]]:
        """Get list of available agents.

        Returns:
            List of agent dictionaries
        """
        # Check cache first
        if "agents" in self.cache:
            return cast(list[dict[str, Any]], self.cache["agents"])

        # Load agents from JSON file
        data = self._load_json_file("agents.json")
        agents = data.get("agents", [])

        # Cache the results
        self.agents_cache = agents
        self.cache["agents"] = agents
        return cast(list[dict[str, Any]], agents)

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
            agents=page_agents,  # type: ignore[arg-type]
            offset=offset,
            limit=limit,
            total_count=total,
            has_filters=False,
            agent_type=None,
            name_pattern=None,
        )

    def get_agent(self, agent_id: str) -> dict[str, Any] | None:
        """Get agent details by ID.

        Args:
            agent_id: The ID of the agent to retrieve

        Returns:
            Agent dictionary or None if not found
        """
        # Get all agents and find the one with matching ID
        agents = self.get_agents()
        for agent in agents:
            if agent.get("id") == agent_id:
                return agent
        return None

    def create_agent(self, agent_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new agent.

        Args:
            agent_data: Dictionary containing agent data

        Returns:
            Created agent dictionary
        """
        # Validate required fields
        required_fields = ["name", "type"]
        for field in required_fields:
            if field not in agent_data:
                raise ValueError(f"Missing required field: {field}")

        # Validate agent type
        valid_types = ["chat", "task", "rag", "tool", "qa", "custom"]
        if agent_data.get("type") not in valid_types:
            raise ValueError(f"Invalid agent type: {agent_data.get('type')}")

        # Generate a new agent ID
        new_id = f"agent-{str(uuid.uuid4())[:8]}"

        # Create the new agent object with mock data
        new_agent = {
            "id": new_id,
            "name": agent_data.get("name"),
            "description": agent_data.get("description", ""),
            "type": agent_data.get("type"),
            "status": "CREATED",
            "created_at": datetime.now(timezone.utc).isoformat() + "Z",
        }

        # Add agent_config if provided
        if "agent_config" in agent_data:
            new_agent["agent_config"] = agent_data["agent_config"]

        # Add the new agent to the cache
        if "agents" in self.cache:
            self.cache["agents"].append(new_agent)
        else:
            # Load existing agents first
            agents = self.get_agents()
            agents.append(new_agent)
            self.cache["agents"] = agents

        if self.verbose:
            print(f"Created mock agent: {new_id}")

        return new_agent

    def update_agent(self, agent_id: str, agent_data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing agent.

        Args:
            agent_id: The ID of the agent to update
            agent_data: Dictionary containing agent data

        Returns:
            Updated agent dictionary
        """
        # Get all agents
        agents = self.get_agents()

        # Find the agent to update
        agent_idx = None
        for idx, agent in enumerate(agents):
            if agent.get("id") == agent_id:
                agent_idx = idx
                break

        if agent_idx is None:
            raise ValueError(f"Agent with ID {agent_id} not found")

        # Update the agent
        updated_agent = agents[agent_idx].copy()

        # Update fields
        if "name" in agent_data:
            updated_agent["name"] = agent_data["name"]
        if "description" in agent_data:
            updated_agent["description"] = agent_data["description"]
        if "agent_config" in agent_data:
            updated_agent["agent_config"] = agent_data["agent_config"]

        # Add modified timestamp
        updated_agent["modified_at"] = datetime.now(timezone.utc).isoformat() + "Z"

        # Update in the list
        agents[agent_idx] = updated_agent

        # Update cache
        self.cache["agents"] = agents

        if self.verbose:
            print(f"Updated mock agent: {agent_id}")

        return updated_agent

    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent by ID.

        Args:
            agent_id: The ID of the agent to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        # Get all agents
        agents = self.get_agents()

        # Find the agent to delete
        agent_idx = None
        for idx, agent in enumerate(agents):
            if agent.get("id") == agent_id:
                agent_idx = idx
                break

        if agent_idx is None:
            return False

        # Remove the agent
        agents.pop(agent_idx)

        # Update cache
        self.cache["agents"] = agents

        if self.verbose:
            print(f"Deleted mock agent: {agent_id}")

        return True

    def invoke_agent(self, agent_id: str, message: str, agent_type: str = "chat") -> str:
        """Invoke an agent with a message.

        Args:
            agent_id: The ID of the agent to invoke
            message: The message to send (for chat) or task data JSON (for task)
            agent_type: Type of agent ("chat", "rag", "tool", "task")

        Returns:
            Agent response as text
        """
        # Get the agent to check if it exists
        agent = self.get_agent(agent_id)
        if not agent:
            return f"Error: Agent with ID {agent_id} not found"

        # Mock response based on agent type
        agent_type = agent.get("type", "chat")
        agent_name = agent.get("name", "Agent")

        # Use a dictionary for agent response types
        responses = {
            "chat": f"This is a mock response from {agent_name}. You said: '{message}'",
            "task": f"I'll help you complete that task. Here's a step-by-step plan for '{message}':\n\n1. First step\n2. Second step\n3. Third step",
            "rag": f"Based on the documents I retrieved for '{message}', here is the information you're looking for...",
        }

        # Get response by type or use default
        return responses.get(
            agent_type,
            f"Mock response from {agent_type} agent '{agent_name}': Received your message: '{message}'",
        )

    def get_models(self) -> list[str]:
        """Get list of available models.

        Returns:
            List of model names
        """
        # Check cache first
        if "models" in self.cache:
            return cast(list[str], self.cache["models"])

        try:
            # Load models from JSON file
            data = self._load_json_file("models.json")
            models = [model["id"] for model in data.get("models", [])]

            # Cache the results
            self.cache["models"] = models
            return models
        except Exception as e:
            if self.verbose:
                print(f"Error loading models: {e}")
            # Fallback to default models
            fallback_models = ["gpt-4", "gpt-3.5-turbo", "claude-3", "claude-2", "mistral-large"]
            self.cache["models"] = fallback_models
            return fallback_models

    def get_guardrails(self) -> list[str]:
        """Get list of available guardrails.

        Returns:
            List of guardrail names
        """
        # Check cache first
        if "guardrails" in self.cache:
            return cast(list[str], self.cache["guardrails"])

        try:
            # Load guardrails from JSON file
            data = self._load_json_file("guardrails.json")
            guardrails = [guardrail["name"] for guardrail in data.get("guardrails", [])]

            # Cache the results
            self.cache["guardrails"] = guardrails
            return guardrails
        except Exception as e:
            if self.verbose:
                print(f"Error loading guardrails: {e}")
            # Fallback to default guardrails
            fallback_guardrails = [
                "moderation",
                "pii-detection",
                "sensitive-topics",
                "custom-policy-1",
            ]
            self.cache["guardrails"] = fallback_guardrails
            return fallback_guardrails

    def health_check(self) -> bool:
        """Check if the data provider is healthy.

        Returns:
            True if healthy, False otherwise
        """
        # Mock data provider is always healthy
        return True

    def get_versions(self, agent_id: str, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """Get versions for an agent from mock data."""
        try:
            # Load versions from JSON file
            data = self._load_json_file("versions.json")
            all_versions = data.get("versions", [])

            # Filter versions for this agent
            agent_versions = [v for v in all_versions if v.get("agent_id") == agent_id]

            # Sort by version number (descending - newest first)
            agent_versions.sort(key=lambda v: v.get("number", 0), reverse=True)

            # Apply pagination
            total_items = len(agent_versions)
            paginated_versions = agent_versions[offset : offset + limit]

            # Get agent info
            agent = self.get_agent(agent_id)
            agent_info = None
            if agent:
                agent_info = {
                    "id": agent.get("id"),
                    "name": agent.get("name"),
                    "type": agent.get("type"),
                }

            return {
                "versions": [
                    {
                        "id": v["id"],
                        "number": v["number"],
                        "version_label": v.get("version_label"),
                        "notes": v.get("notes"),
                        "created_at": v["created_at"],
                        "created_by": v["created_by"],
                    }
                    for v in paginated_versions
                ],
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total_items": total_items,
                },
                "agent": agent_info,
            }
        except Exception as e:
            if self.verbose:
                print(f"Error loading versions: {e}")
            return {
                "versions": [],
                "pagination": {"limit": limit, "offset": offset, "total_items": 0},
                "agent": None,
            }

    def get_version(self, agent_id: str, version_id: str) -> dict[str, Any] | None:
        """Get specific version details from mock data."""
        try:
            # Load versions from JSON file
            data = self._load_json_file("versions.json")
            all_versions = data.get("versions", [])

            # Handle "latest" version request
            if version_id == "latest":
                agent_versions = [v for v in all_versions if v.get("agent_id") == agent_id]
                if not agent_versions:
                    return None
                # Sort by version number and get the latest
                agent_versions.sort(key=lambda v: v.get("number", 0), reverse=True)
                version_data = agent_versions[0]
            else:
                # Find specific version
                version_data = None
                for v in all_versions:
                    if v.get("id") == version_id and v.get("agent_id") == agent_id:
                        version_data = v
                        break

                if not version_data:
                    return None

            # Get agent info
            agent = self.get_agent(agent_id)
            agent_info = None
            if agent:
                agent_info = {
                    "id": agent.get("id"),
                    "name": agent.get("name"),
                    "type": agent.get("type"),
                }

            return {
                "version": version_data,
                "agent": agent_info,
            }
        except Exception as e:
            if self.verbose:
                print(f"Error loading version: {e}")
            return None
