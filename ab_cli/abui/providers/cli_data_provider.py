"""CLI data provider implementation for the Agent Builder UI.

This provider calls CLI commands as subprocesses and converts JSON responses
to strongly-typed Pydantic models for compatibility with the DataProvider interface.
"""

import contextlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
from typing import Any

from ab_cli.abui.providers.data_provider import DataProvider
from ab_cli.abui.utils.json_utils import extract_json_from_text
from ab_cli.api.pagination import PaginatedResult
from ab_cli.models.agent import (
    Agent,
    AgentCreate,
    AgentUpdate,
    AgentVersion,
    Pagination,
    Version,
    VersionConfig,
    VersionList,
)
from ab_cli.models.invocation import InvokeResponse
from ab_cli.models.resources import (
    GuardrailList,
    GuardrailModel,
    LLMModel,
    LLMModelList,
)


class CLIDataProvider(DataProvider):
    """Data provider that uses CLI commands to access data via subprocess.

    This provider maintains backward compatibility by calling CLI commands
    as subprocesses, while converting responses to strongly-typed models.
    """

    def __init__(self, config: Any = None, verbose: bool = False):
        """Initialize with configuration and verbose flag.

        Args:
            config: Configuration object with necessary settings
            verbose: Whether to print verbose debugging output
        """
        self.config = config
        self.verbose = verbose if verbose is not None else False
        self.cache: dict[str, Any] = {}

    def _run_command(self, cmd_parts: list[str], use_cache: bool = True) -> dict[str, Any]:
        """Run a CLI command and parse its JSON output.

        Args:
            cmd_parts: Command parts to add after the base CLI command
            use_cache: Whether to use cache for this command

        Returns:
            Parsed JSON result as a dictionary
        """
        # Check cache first
        cache_key = " ".join(cmd_parts)
        if use_cache and cache_key in self.cache:
            if self.verbose:
                print(f"Using cached result for: {cache_key}")
            return self.cache[cache_key]

        # Add common options
        cmd = ["ab"]

        if self.verbose:
            cmd.append("--verbose")

        if self.config and hasattr(self.config, "config_path") and self.config.config_path:
            cmd.extend(["--config", str(self.config.config_path)])

        cmd.extend(cmd_parts)

        # Execute command
        cmd_str = " ".join(shlex.quote(str(part)) for part in cmd)

        if self.verbose:
            print(f"[CLI Provider] Command list: {cmd}", file=sys.stderr)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                stdin=subprocess.DEVNULL,
                check=False,
            )
            if self.verbose:
                print(
                    f"[CLI Provider] Completed with return code: {result.returncode}",
                    file=sys.stderr,
                )
        except subprocess.TimeoutExpired as e:
            error_msg = f"Command timed out after 30 seconds: {cmd_str}"
            print(f"[CLI Provider] TIMEOUT: {error_msg}", file=sys.stderr)
            raise RuntimeError(error_msg) from e
        except Exception as e:
            error_msg = f"Command execution failed: {cmd_str}"
            print(f"[CLI Provider] ERROR: {error_msg} - {str(e)}", file=sys.stderr)
            raise RuntimeError(error_msg) from e

        # Process results
        if result.returncode == 0:
            try:
                data = extract_json_from_text(result.stdout, self.verbose)

                if data:
                    if use_cache:
                        self.cache[cache_key] = data
                    result_dict: dict[str, Any] = data if isinstance(data, dict) else {}
                    return result_dict
                else:
                    raise ValueError("Command returned empty or invalid JSON")
            except Exception as e:
                print(f"[CLI Provider] Error parsing command output: {e}", file=sys.stderr)
                raise

        # Handle errors
        error_msg = f"Command failed with code {result.returncode}: {result.stderr}"
        if self.verbose:
            print(error_msg)
        raise RuntimeError(error_msg)

    def clear_cache(self) -> None:
        """Clear the command cache."""
        self.cache = {}
        if self.verbose:
            print("Cache cleared")

    def get_agents(self) -> list[Agent]:
        """Get list of available agents.

        Returns:
            List of Agent objects with basic metadata.
        """
        try:
            result = self._run_command(["agents", "list", "--format", "json"])

            if "agents" in result:
                agents_data = result["agents"]
                # Convert to Agent models
                return [Agent.model_validate(agent_data) for agent_data in agents_data]
            else:
                return []

        except Exception as e:
            if self.verbose:
                print(f"Error in get_agents: {e}")
            raise

    def get_agents_paginated(self, limit: int, offset: int) -> PaginatedResult:
        """Get paginated list of agents using CLI commands with server-side pagination.

        Args:
            limit: Maximum number of agents to return
            offset: Number of agents to skip

        Returns:
            PaginatedResult with agents list and metadata
        """
        try:
            cmd = [
                "agents",
                "list",
                "--limit",
                str(limit),
                "--offset",
                str(offset),
                "--format",
                "json",
            ]

            result = self._run_command(cmd, use_cache=True)

            agents_data = result.get("agents", [])
            pagination_info = result.get("pagination", {})
            total_count = pagination_info.get("total_items", len(agents_data))

            # Convert to Agent models
            agents = [Agent.model_validate(agent_data) for agent_data in agents_data]

            return PaginatedResult(
                agents=agents,
                offset=offset,
                limit=limit,
                total_count=total_count,
                has_filters=False,
                agent_type=None,
                name_pattern=None,
            )

        except Exception as e:
            if self.verbose:
                print(f"Error in get_agents_paginated: {e}")
            return PaginatedResult(
                agents=[],
                offset=offset,
                limit=limit,
                total_count=0,
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
        try:
            result = self._run_command(["agents", "get", agent_id, "--format", "json"])

            if "agent" in result and "version" in result:
                agent = Agent.model_validate(result["agent"])
                version_data = result["version"]
                # Convert Version to VersionConfig (which includes the config field)
                version_config = VersionConfig(
                    id=version_data["id"],
                    number=version_data["number"],
                    version_label=version_data.get("versionLabel", ""),
                    notes=version_data.get("notes", ""),
                    created_at=version_data["createdAt"],
                    created_by=version_data["createdBy"],
                    config=version_data.get("config", {}),
                )
                return AgentVersion(agent=agent, version=version_config)
            else:
                return None

        except Exception as e:
            if self.verbose:
                print(f"Error in get_agent: {e}")
            return None

    def create_agent(self, agent_create: AgentCreate) -> AgentVersion:
        """Create a new agent.

        Args:
            agent_create: AgentCreate model containing agent creation data.

        Returns:
            AgentVersion object for the newly created agent.
        """
        try:
            # Convert model to dict
            agent_data = agent_create.model_dump(by_alias=True)

            name = agent_data.get("name")
            agent_type = agent_data.get("agentType", "chat")
            description = agent_data.get("description", "")
            agent_config = agent_data.get("config", {})

            # Create temporary file for config
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_config:
                json.dump(agent_config, tmp_config, indent=2)
                tmp_config_path = tmp_config.name

            try:
                cmd = [
                    "agents",
                    "create",
                    "--name",
                    name,
                    "--description",
                    description,
                    "--type",
                    agent_type,
                    "--agent-config",
                    tmp_config_path,
                    "--version-label",
                    agent_data.get("version_label", "v1.0"),
                    "--notes",
                    agent_data.get("notes", "Initial version"),
                    "--format",
                    "json",
                ]

                result = self._run_command(cmd, use_cache=False)

                # Clear cache
                self.cache.clear()

                # Convert to AgentVersion
                if "agent" in result and "version" in result:
                    agent = Agent.model_validate(result["agent"])
                    version_data = result["version"]
                    # Convert Version to VersionConfig
                    version_config = VersionConfig(
                        id=version_data["id"],
                        number=version_data["number"],
                        version_label=version_data.get("versionLabel", ""),
                        notes=version_data.get("notes", ""),
                        created_at=version_data["createdAt"],
                        created_by=version_data["createdBy"],
                        config=version_data.get("config", {}),
                    )
                    return AgentVersion(agent=agent, version=version_config)
                else:
                    raise ValueError("Invalid response from create command")
            finally:
                with contextlib.suppress(FileNotFoundError, PermissionError):
                    os.unlink(tmp_config_path)

        except Exception as e:
            if self.verbose:
                print(f"Error in create_agent: {e}")
            raise

    def update_agent(self, agent_id: str, agent_update: AgentUpdate) -> AgentVersion:
        """Update an existing agent (creates a new version).

        Args:
            agent_id: The ID of the agent to update.
            agent_update: AgentUpdate model containing update data.

        Returns:
            AgentVersion object with the new version.
        """
        try:
            # Convert model to dict
            agent_data = agent_update.model_dump(by_alias=True)
            agent_config = agent_data.get("config", {})

            # Create temporary file for config
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_config:
                json.dump(agent_config, tmp_config, indent=2)
                tmp_config_path = tmp_config.name

            try:
                cmd = [
                    "agents",
                    "update",
                    agent_id,
                    "--agent-config",
                    tmp_config_path,
                    "--version-label",
                    agent_data.get("version_label", "v2.0"),
                    "--notes",
                    agent_data.get("notes", "Updated via UI"),
                    "--format",
                    "json",
                ]

                result = self._run_command(cmd, use_cache=False)

                # Clear cache
                self.cache.clear()

                # Convert to AgentVersion
                if "agent" in result and "version" in result:
                    agent = Agent.model_validate(result["agent"])
                    version_data = result["version"]
                    # Convert Version to VersionConfig
                    version_config = VersionConfig(
                        id=version_data["id"],
                        number=version_data["number"],
                        version_label=version_data.get("versionLabel", ""),
                        notes=version_data.get("notes", ""),
                        created_at=version_data["createdAt"],
                        created_by=version_data["createdBy"],
                        config=version_data.get("config", {}),
                    )
                    return AgentVersion(agent=agent, version=version_config)
                else:
                    raise ValueError("Invalid response from update command")
            finally:
                with contextlib.suppress(FileNotFoundError, PermissionError):
                    os.unlink(tmp_config_path)

        except Exception as e:
            if self.verbose:
                print(f"Error in update_agent: {e}")
            raise

    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent by ID.

        Args:
            agent_id: The ID of the agent to delete.

        Returns:
            True if deletion successful, False otherwise.
        """
        try:
            cmd = ["agents", "delete", agent_id, "--yes", "--format", "json"]
            result = self._run_command(cmd, use_cache=False)

            # Clear cache
            self.cache.clear()

            return result.get("success", False)

        except Exception as e:
            if self.verbose:
                print(f"Error in delete_agent: {e}")
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
        try:
            quoted_message = shlex.quote(message)

            if agent_type == "task":
                cmd = ["invoke", "task", agent_id, "--task", quoted_message, "--format", "json"]
            else:
                cmd = ["invoke", "chat", agent_id, "--message", quoted_message, "--format", "json"]

            result = self._run_command(cmd, use_cache=False)

            # Extract response text
            answer = result.get("response", "")
            if not answer and "output" in result:
                # Try to extract from output array
                output = result["output"]
                if isinstance(output, list):
                    for item in output:
                        if item.get("type") == "message" and item.get("role") == "assistant":
                            content = item.get("content", [])
                            if isinstance(content, list):
                                texts = []
                                for content_item in content:
                                    if content_item.get("type") == "output_text":
                                        texts.append(content_item.get("text", ""))
                                if texts:
                                    answer = "\n".join(texts)
                                    break

            # Build metadata
            metadata = {
                "model": result.get("model"),
                "created_at": result.get("created_at"),
                "usage": result.get("usage"),
                "finish_reason": result.get("finish_reason"),
            }

            # Add custom outputs if available
            if "custom_outputs" in result:
                metadata.update(result["custom_outputs"])

            return InvokeResponse(answer=answer, metadata=metadata)

        except Exception as e:
            if self.verbose:
                print(f"Error in invoke_agent: {e}")
            return InvokeResponse(
                answer=f"Error invoking agent: {str(e)}",
                metadata={},
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
            cmd = [
                "versions",
                "list",
                agent_id,
                "--limit",
                str(limit),
                "--offset",
                str(offset),
                "--format",
                "json",
            ]

            result = self._run_command(cmd, use_cache=False)

            versions_data = result.get("versions", [])
            pagination_info = result.get("pagination", {})
            agent_data = result.get("agent")

            # Convert to Version models
            versions = [Version.model_validate(v) for v in versions_data]

            # Create pagination
            pagination = Pagination(
                limit=pagination_info.get("limit", limit),
                offset=pagination_info.get("offset", offset),
                total_items=pagination_info.get("total_items", len(versions)),
            )

            # Parse agent if available
            agent = Agent.model_validate(agent_data) if agent_data else None
            if not agent:
                # If no agent in response, try to get it separately
                agent_version = self.get_agent(agent_id)
                agent = agent_version.agent if agent_version else None

            return VersionList(versions=versions, pagination=pagination, agent=agent)  # type: ignore[arg-type]

        except Exception as e:
            if self.verbose:
                print(f"Error fetching versions: {e}")
            # Try to get agent for error case
            try:
                agent_version = self.get_agent(agent_id)
                agent = agent_version.agent if agent_version else None
            except Exception:
                agent = None

            return VersionList(
                versions=[],
                pagination=Pagination(limit=limit, offset=offset, total_items=0),
                agent=agent,  # type: ignore[arg-type]
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
            cmd = ["versions", "get", agent_id, version_id, "--format", "json"]
            result = self._run_command(cmd, use_cache=False)

            version_data = result.get("version")
            if not version_data:
                return None

            return Version.model_validate(version_data)

        except Exception as e:
            if self.verbose:
                print(f"Error fetching version: {e}")
            return None

    def get_models(self, limit: int = 100, offset: int = 0) -> LLMModelList:
        """Get list of available LLM models.

        Args:
            limit: Maximum number of models to return.
            offset: Offset for pagination.

        Returns:
            LLMModelList containing available models.
        """
        try:
            cmd = [
                "resources",
                "models",
                "--limit",
                str(limit),
                "--offset",
                str(offset),
                "--format",
                "json",
            ]
            result = self._run_command(cmd)

            models_data = result.get("models", [])
            pagination_info = result.get("pagination", {})

            # Convert to LLMModel objects
            models = [LLMModel.model_validate(m) for m in models_data]

            # Create pagination
            pagination = Pagination(
                limit=pagination_info.get("limit", limit),
                offset=pagination_info.get("offset", offset),
                total_items=pagination_info.get("total_items", len(models)),
            )

            return LLMModelList(models=models, pagination=pagination)

        except Exception as e:
            if self.verbose:
                print(f"Error in get_models: {e}")
            # Fallback
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
        try:
            cmd = [
                "resources",
                "guardrails",
                "--limit",
                str(limit),
                "--offset",
                str(offset),
                "--format",
                "json",
            ]
            result = self._run_command(cmd)

            guardrails_data = result.get("guardrails", [])
            pagination_info = result.get("pagination", {})

            # Convert to GuardrailModel objects
            guardrails = [GuardrailModel.model_validate(g) for g in guardrails_data]

            # Create pagination
            pagination = Pagination(
                limit=pagination_info.get("limit", limit),
                offset=pagination_info.get("offset", offset),
                total_items=pagination_info.get("total_items", len(guardrails)),
            )

            return GuardrailList(guardrails=guardrails, pagination=pagination)

        except Exception as e:
            if self.verbose:
                print(f"Error in get_guardrails: {e}")
            # Fallback
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
        try:
            self._run_command(["--version"], use_cache=False)
            return True
        except Exception:
            return False
