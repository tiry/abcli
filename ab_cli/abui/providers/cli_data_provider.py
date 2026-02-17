"""CLI data provider implementation for the Agent Builder UI."""

import contextlib
import json
import os
import shlex
import subprocess
import tempfile
from typing import Any, cast

from ab_cli.abui.providers.data_provider import DataProvider
from ab_cli.abui.utils.json_utils import extract_json_from_text, extract_text_from_object
from ab_cli.api.pagination import PaginatedResult


class CLIDataProvider(DataProvider):
    """Data provider that uses CLI commands to access data."""

    def __init__(self, config: Any = None, verbose: bool = False):
        """Initialize with configuration and verbose flag.

        Args:
            config: Configuration object with necessary settings
            verbose: Whether to print verbose debugging output
        """
        self.config = config
        self.verbose = verbose if verbose is not None else False
        self.cache: dict[str, Any] = {
            "agents": None,
            "models": None,
            "guardrails": None,
        }

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
        cmd_str = " ".join(cmd)
        if self.verbose:
            print(f"Executing shell command: {cmd_str}")

        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True,
            text=True,
        )

        # Process results
        if result.returncode == 0:
            try:
                if self.verbose:
                    data = extract_json_from_text(result.stdout, self.verbose)
                else:
                    try:
                        data = json.loads(result.stdout)
                    except json.JSONDecodeError:
                        data = extract_json_from_text(result.stdout, self.verbose)

                if data:
                    # Update cache
                    if use_cache:
                        self.cache[cache_key] = data
                    # Ensure we return a dict
                    result_dict: dict[str, Any] = data if isinstance(data, dict) else {}
                    return result_dict
                else:
                    raise ValueError("Command returned empty or invalid JSON")
            except Exception as e:
                if self.verbose:
                    print(f"Error parsing command output: {e}")
                raise

        # Handle errors
        error_msg = f"Command failed with code {result.returncode}: {result.stderr}"
        if self.verbose:
            print(error_msg)
        raise RuntimeError(error_msg)

    def _run_module_command(self, cmd_parts: list[str], use_cache: bool = True) -> dict[str, Any]:
        """Run a command using Python module for more reliable execution.

        Args:
            cmd_parts: Command parts to add after the base CLI module command
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

        # Create module command (python -m ab_cli.cli.main ...)
        module_cmd = ["python", "-m", "ab_cli.cli.main"]

        if self.verbose:
            module_cmd.append("--verbose")

        if self.config and hasattr(self.config, "config_path") and self.config.config_path:
            module_cmd.extend(["--config", str(self.config.config_path)])

        module_cmd.extend(cmd_parts)

        # Execute command
        if self.verbose:
            print(f"Executing module command: {' '.join(module_cmd)}")

        result = subprocess.run(
            module_cmd,
            capture_output=True,
            text=True,
            cwd=os.path.join(
                os.path.dirname(__file__), "../../../"
            ),  # Run from the ab-cli directory
        )

        # Process results
        if result.returncode == 0:
            try:
                if self.verbose:
                    data = extract_json_from_text(result.stdout, self.verbose)
                else:
                    try:
                        data = json.loads(result.stdout)
                    except json.JSONDecodeError:
                        data = extract_json_from_text(result.stdout, self.verbose)

                if data:
                    # Update cache
                    if use_cache:
                        self.cache[cache_key] = data
                    # Ensure we return a dict
                    result_dict: dict[str, Any] = data if isinstance(data, dict) else {}
                    return result_dict
                else:
                    raise ValueError("Command returned empty or invalid JSON")
            except Exception as e:
                if self.verbose:
                    print(f"Error parsing command output: {e}")
                raise

        # Handle errors
        error_msg = f"Command failed with code {result.returncode}: {result.stderr}"
        if self.verbose:
            print(error_msg)
        raise RuntimeError(error_msg)

    def clear_cache(self) -> None:
        """Clear the command cache."""
        self.cache = {
            "agents": None,
            "models": None,
            "guardrails": None,
        }
        if self.verbose:
            print("Cache cleared")

    def get_agents(self) -> list[dict[str, Any]]:
        """Get list of available agents.

        Returns:
            List of agent dictionaries
        """
        try:
            # Check cache first
            if self.cache["agents"] is not None:
                return cast(list[dict[str, Any]], self.cache["agents"])

            # Run CLI command to get agents
            result = self._run_command(["agents", "list", "--format", "json"])

            # Extract agents from result
            if "agents" in result:
                agents = result["agents"]
                self.cache["agents"] = agents
                return cast(list[dict[str, Any]], agents)
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
            # Use CLI command with pagination parameters (server-side pagination)
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

            # Don't use cache for paginated requests
            result = self._run_command(cmd, use_cache=False)

            # Extract agents and pagination info
            agents = result.get("agents", [])
            pagination_info = result.get("pagination", {})
            total_count = pagination_info.get("total_items", len(agents))

            # Return paginated result
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
            # Return empty result on error
            return PaginatedResult(
                agents=[],
                offset=offset,
                limit=limit,
                total_count=0,
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
        try:
            # Run CLI command to get agent
            result = self._run_command(["agents", "get", agent_id, "--format", "json"])

            # Extract agent from result
            if "agent" in result:
                agent = result["agent"]

                # Extract config from version if available
                if "version" in result and "config" in result["version"]:
                    agent["agent_config"] = result["version"]["config"]

                return agent
            else:
                return None

        except Exception as e:
            if self.verbose:
                print(f"Error in get_agent: {e}")
            return None

    def create_agent(self, agent_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new agent.

        Args:
            agent_data: Dictionary containing agent data

        Returns:
            Created agent dictionary
        """
        try:
            # Extract required fields
            name = agent_data.get("name")
            agent_type = agent_data.get("type", "chat")
            description = agent_data.get("description", "")

            # Extract config
            agent_config = agent_data.get("agent_config", {})

            # Create a temporary file for the config
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_config:
                json.dump(agent_config, tmp_config, indent=2)
                tmp_config_path = tmp_config.name

            try:
                # Run CLI command to create agent
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
                    "v1.0",
                    "--notes",
                    "Initial version",
                    "--format",
                    "json",
                ]

                result = self._run_command(cmd, use_cache=False)

                # Clear agents cache after creating a new agent
                if "agents" in self.cache:
                    self.cache["agents"] = None

                # Extract agent from result
                if "agent" in result:
                    return result["agent"]
                else:
                    return result
            finally:
                # Clean up temporary file
                with contextlib.suppress(FileNotFoundError, PermissionError):
                    os.unlink(tmp_config_path)

        except Exception as e:
            if self.verbose:
                print(f"Error in create_agent: {e}")
            raise

    def update_agent(self, agent_id: str, agent_data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing agent.

        Args:
            agent_id: The ID of the agent to update
            agent_data: Dictionary containing agent data

        Returns:
            Updated agent dictionary
        """
        try:
            # Extract config
            agent_config = agent_data.get("agent_config", {})

            # Create a temporary file for the config
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp_config:
                json.dump(agent_config, tmp_config, indent=2)
                tmp_config_path = tmp_config.name

            try:
                # Run CLI command to update agent
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

                # Clear agents cache after updating an agent
                if "agents" in self.cache:
                    self.cache["agents"] = None

                # Extract agent from result
                if "agent" in result:
                    return result["agent"]
                else:
                    return result
            finally:
                # Clean up temporary file
                with contextlib.suppress(FileNotFoundError, PermissionError):
                    os.unlink(tmp_config_path)

        except Exception as e:
            if self.verbose:
                print(f"Error in update_agent: {e}")
            raise

    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent by ID.

        Args:
            agent_id: The ID of the agent to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Run CLI command to delete agent
            cmd = ["agents", "delete", agent_id, "--format", "json"]

            result = self._run_command(cmd, use_cache=False)

            # Clear agents cache after deleting an agent
            if "agents" in self.cache:
                self.cache["agents"] = None

            # Check result
            return "success" in result and result["success"]

        except Exception as e:
            if self.verbose:
                print(f"Error in delete_agent: {e}")
            return False

    def invoke_agent(self, agent_id: str, message: str, agent_type: str = "chat") -> str:
        """Invoke an agent with a message.

        Args:
            agent_id: The ID of the agent to invoke
            message: The message to send (for chat) or task data JSON (for task)
            agent_type: Type of agent ("chat", "rag", "tool", "task")

        Returns:
            Agent response as text
        """
        try:
            # Quote the message to handle special characters
            quoted_message = shlex.quote(message)

            # Build command based on agent type
            if agent_type == "task":
                # Use invoke task with --task parameter
                cmd = ["invoke", "task", agent_id, "--task", quoted_message, "--format", "json"]
            else:
                # Use invoke chat with --message parameter (for chat, rag, tool)
                cmd = ["invoke", "chat", agent_id, "--message", quoted_message, "--format", "json"]

            result = self._run_command(cmd, use_cache=False)

            if self.verbose:
                print(f"[DEBUG] invoke_agent result keys: {list(result.keys())}")
                if "response" in result:
                    print(f"[DEBUG] response field type: {type(result['response'])}")

            # Extract response from result - check "response" field first
            if "response" in result:
                response_value = result["response"]
                # Ensure we return a string
                if isinstance(response_value, str):
                    if self.verbose:
                        print(f"[DEBUG] Returning response text (length: {len(response_value)})")
                    return response_value
                else:
                    # If it's not a string, convert it
                    if self.verbose:
                        print(f"[DEBUG] Converting response from {type(response_value)} to string")
                    return str(response_value)

            # Try to extract response from output array
            if "output" in result:
                output = result["output"]

                if isinstance(output, list):
                    # Look for message type outputs
                    for item in output:
                        if item.get("type") == "message" and item.get("role") == "assistant":
                            content = item.get("content", [])
                            # Extract text from content array
                            if isinstance(content, list):
                                texts = []
                                for content_item in content:
                                    if (
                                        content_item.get("type") == "output_text"
                                        and "text" in content_item
                                    ):
                                        texts.append(content_item["text"])
                                if texts:
                                    response_text = " ".join(texts)
                                    if self.verbose:
                                        print(
                                            f"[DEBUG] Extracted from output array (length: {len(response_text)})"
                                        )
                                    return response_text

            # Try to extract text from nested structures
            extracted_text = extract_text_from_object(result)
            if extracted_text and extracted_text != "No response text found":
                if self.verbose:
                    print("[DEBUG] Extracted via extract_text_from_object")
                return extracted_text

            # Fallback - log the issue
            if self.verbose:
                print("[DEBUG] No response extracted, returning error message")
            return f"No response found in agent output: {result}"

        except Exception as e:
            if self.verbose:
                print(f"Error in invoke_agent: {e}")
            return f"Error invoking agent: {str(e)}"

    def get_models(self) -> list[str]:
        """Get list of available models.

        Returns:
            List of model names
        """
        try:
            # Check cache first
            if self.cache["models"] is not None:
                return cast(list[str], self.cache["models"])

            # Run CLI command to get models
            result = self._run_command(["resources", "models", "--format", "json"])

            # Extract models from result
            if "models" in result:
                models = [model["id"] for model in result["models"]]
                self.cache["models"] = models
                return models
            else:
                # Fallback to default models
                fallback_models = [
                    "gpt-4",
                    "gpt-3.5-turbo",
                    "claude-3",
                    "claude-2",
                    "mistral-large",
                ]
                self.cache["models"] = fallback_models
                return fallback_models

        except Exception as e:
            if self.verbose:
                print(f"Error in get_models: {e}")
            # Fallback to default models
            fallback_models = ["gpt-4", "gpt-3.5-turbo", "claude-3", "claude-2", "mistral-large"]
            return fallback_models

    def get_guardrails(self) -> list[str]:
        """Get list of available guardrails.

        Returns:
            List of guardrail names
        """
        try:
            # Check cache first
            if self.cache["guardrails"] is not None:
                return cast(list[str], self.cache["guardrails"])

            # Run CLI command to get guardrails
            result = self._run_command(["resources", "guardrails", "--format", "json"])

            # Extract guardrails from result
            if "guardrails" in result:
                guardrails = [guardrail["name"] for guardrail in result["guardrails"]]
                self.cache["guardrails"] = guardrails
                return guardrails
            else:
                # Fallback to default guardrails
                fallback_guardrails = [
                    "moderation",
                    "pii-detection",
                    "sensitive-topics",
                    "custom-policy-1",
                ]
                self.cache["guardrails"] = fallback_guardrails
                return fallback_guardrails

        except Exception as e:
            if self.verbose:
                print(f"Error in get_guardrails: {e}")
            # Fallback to default guardrails
            fallback_guardrails = [
                "moderation",
                "pii-detection",
                "sensitive-topics",
                "custom-policy-1",
            ]
            return fallback_guardrails

    def get_versions(self, agent_id: str, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """Get list of versions for an agent.

        Args:
            agent_id: The ID of the agent
            limit: Maximum number of versions to return
            offset: Offset for pagination

        Returns:
            Dictionary containing versions, pagination, and agent info
        """
        try:
            # Run CLI command to get versions
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

            # Extract versions and pagination
            versions_list = result.get("versions", [])
            pagination_info = result.get("pagination", {})
            agent_info = result.get("agent", {})

            return {
                "versions": [
                    {
                        "id": str(v.get("id")),
                        "number": v.get("number"),
                        "version_label": v.get("version_label"),
                        "notes": v.get("notes"),
                        "created_at": v.get("created_at"),
                        "created_by": v.get("created_by"),
                    }
                    for v in versions_list
                ],
                "pagination": {
                    "limit": pagination_info.get("limit", limit),
                    "offset": pagination_info.get("offset", offset),
                    "total_items": pagination_info.get("total_items", len(versions_list)),
                },
                "agent": {
                    "id": str(agent_info.get("id")),
                    "name": agent_info.get("name"),
                    "type": agent_info.get("type"),
                }
                if agent_info
                else None,
            }

        except Exception as e:
            if self.verbose:
                print(f"Error fetching versions: {e}")
            return {
                "versions": [],
                "pagination": {"limit": limit, "offset": offset, "total_items": 0},
                "agent": None,
            }

    def get_version(self, agent_id: str, version_id: str) -> dict[str, Any] | None:
        """Get details of a specific version.

        Args:
            agent_id: The ID of the agent
            version_id: The ID of the version (or "latest")

        Returns:
            Dictionary containing version details and agent info
        """
        try:
            # Run CLI command to get version
            cmd = ["versions", "get", agent_id, version_id, "--format", "json"]

            result = self._run_command(cmd, use_cache=False)

            # Extract version and agent info
            version_info = result.get("version", {})
            agent_info = result.get("agent", {})

            if not version_info:
                return None

            return {
                "version": {
                    "id": str(version_info.get("id")),
                    "number": version_info.get("number"),
                    "version_label": version_info.get("version_label"),
                    "notes": version_info.get("notes"),
                    "created_at": version_info.get("created_at"),
                    "created_by": version_info.get("created_by"),
                    "config": version_info.get("config", {}),
                },
                "agent": {
                    "id": str(agent_info.get("id")),
                    "name": agent_info.get("name"),
                    "type": agent_info.get("type"),
                }
                if agent_info
                else None,
            }

        except Exception as e:
            if self.verbose:
                print(f"Error fetching version: {e}")
            return None

    def health_check(self) -> bool:
        """Check if the data provider is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Run CLI command to get version
            self._run_command(["--version"], use_cache=False)
            return True
        except Exception:
            return False
