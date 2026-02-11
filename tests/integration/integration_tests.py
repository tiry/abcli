#!/usr/bin/env python
"""
Integration tests for the Agent Builder CLI.

These tests require a real API endpoint and proper configuration.
They are not run by default as part of the normal test suite.

To run these tests:
    python -m tests.integration.integration_tests

Prerequisites:
    1. Valid config.yaml file with API credentials
    2. Access to Agent Builder API endpoint
    3. Existence of "Calculator_Test_3" agent or similar calculator agent

Note: This script will create and then delete a new agent. Make sure you have
the necessary permissions in your environment.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid

# Add parent directory to path so we can import from ab_cli
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.append(parent_dir)



# Constants
DEFAULT_CONFIG = "./config.yaml"
SUCCESS_COLOR = "\033[92m"  # Green
FAILURE_COLOR = "\033[91m"  # Red
INFO_COLOR = "\033[94m"     # Blue
RESET_COLOR = "\033[0m"     # Reset


def print_header(message: str) -> None:
    """Print a section header."""
    print(f"\n{INFO_COLOR}{'=' * 80}")
    print(f" {message}")
    print(f"{'=' * 80}{RESET_COLOR}")


def print_result(success: bool, message: str, exit_code: int = None) -> None:
    """Print the result of a test."""
    color = SUCCESS_COLOR if success else FAILURE_COLOR
    status = "✅ PASS" if success else "❌ FAIL"

    # If exit code is provided, include it in the message
    if exit_code is not None:
        exit_status = f"[Exit code: {exit_code}]"
        print(f"{color}{status}: {message} {exit_status}{RESET_COLOR}")
    else:
        print(f"{color}{status}: {message}{RESET_COLOR}")


def run_command(cmd: list[str], capture_output: bool = True, verbose: bool = False) -> tuple[int, str]:
    """Run a CLI command and return the exit code and output."""
    try:
        if verbose:
            print(f"{INFO_COLOR}Executing command: {' '.join(cmd)}{RESET_COLOR}")

        result = subprocess.run(
            cmd,
            check=False,
            capture_output=capture_output,
            text=True
        )
        output = result.stdout if capture_output else ""

        if verbose:
            if capture_output and output:
                print(f"{INFO_COLOR}Command output (stdout):{RESET_COLOR}")
                # Print the output, but limit it if it's very long
                if len(output) > 2000:
                    print(f"{output[:1000]}\n...\n{output[-1000:]}")
                else:
                    print(output)

            # Also print stderr if there's any error output
            if result.stderr and len(result.stderr.strip()) > 0:
                print(f"{FAILURE_COLOR}Command error output (stderr):{RESET_COLOR}")
                print(result.stderr)

            if result.returncode != 0:
                print(f"{FAILURE_COLOR}Command returned non-zero exit code: {result.returncode}{RESET_COLOR}")

            print()

        return result.returncode, output
    except subprocess.SubprocessError as e:
        if verbose:
            print(f"{FAILURE_COLOR}Command failed: {str(e)}{RESET_COLOR}")
        return 1, str(e)


def extract_json_from_output(output: str) -> str:
    """Extract the JSON part from command output that may contain other text.
    
    This handles cases where the output includes informational messages
    before the actual JSON content.
    """
    # Try to find the start of JSON content (typically starts with '{')
    json_start = output.find('{')
    if json_start >= 0:
        return output[json_start:]
    return output


def find_agent_by_name(agents_output: str, name: str) -> dict | None:
    """Find an agent by name in the JSON output of the list agents command."""
    try:
        # Extract just the JSON part from the output
        json_content = extract_json_from_output(agents_output)
        data = json.loads(json_content)
        for agent in data.get("agents", []):
            if agent.get("name") == name:
                return agent
        return None
    except json.JSONDecodeError:
        print(f"{FAILURE_COLOR}Error: Could not parse JSON output{RESET_COLOR}")
        return None


class IntegrationTests:
    """Integration tests for the Agent Builder CLI."""

    def __init__(self, config_path: str = DEFAULT_CONFIG, verbose: bool = False) -> None:
        """Initialize the tests."""
        self.config_path = config_path
        self.verbose = verbose
        self.test_agent_id = None
        self.calculator_agent_id = None
        self.results = []
        self.base_cmd = ["ab", "--config", self.config_path]

        if verbose:
            print(f"{INFO_COLOR}Running in verbose mode. All commands and responses will be displayed.{RESET_COLOR}")

    def run_all_tests(self) -> bool:
        """Run all integration tests."""
        try:
            # First tests - listing resources and agent types
            self.test_list_agents()
            self.test_list_agent_types()
            self.test_list_models()
            self.test_list_guardrails()

            # Tests that create and manipulate a new agent
            self.test_create_agent()
            self.test_get_agent_json()
            self.test_list_versions()
            self.test_get_version()
            self.test_call_new_agent()
            self.test_call_agent_json()
            self.test_patch_agent()
            self.test_update_agent()

            # Clean up - delete the test agent
            self.test_delete_agent()

            # Print summary
            self.print_summary()

            # Return True if all tests passed
            return all(result[0] for result in self.results)

        except Exception as e:
            print(f"{FAILURE_COLOR}Test suite failed with exception: {str(e)}{RESET_COLOR}")
            return False

    def test_list_agents(self) -> bool:
        """Test listing all agents."""
        print_header("Testing: List Agents")

        cmd = self.base_cmd + ["agents", "list"]
        exit_code, output = run_command(cmd, verbose=self.verbose)

        # Check if command executed successfully
        success = exit_code == 0
        self.results.append((success, "List agents"))
        print_result(success, "List agents", exit_code)

        # Try to parse as JSON to get agent information - use -f json (format) instead of --json
        cmd = self.base_cmd + ["agents", "list", "-f", "json"]
        exit_code, output = run_command(cmd, verbose=self.verbose)

        # Add this test result as well
        json_success = exit_code == 0
        self.results.append((json_success, "List agents (JSON format)"))
        print_result(json_success, "List agents (JSON format)", exit_code)

        if exit_code == 0:
            try:
                # Extract just the JSON part from the output
                json_content = extract_json_from_output(output)
                data = json.loads(json_content)
                if data.get("agents") and len(data["agents"]) > 0:
                    # Find Calculator_Test_3 agent
                    for agent in data["agents"]:
                        if "Calculator" in agent.get("name", ""):
                            self.calculator_agent_id = agent["id"]
                            print(f"{INFO_COLOR}Found calculator agent: {agent['name']} (ID: {agent['id']}){RESET_COLOR}")
                            break
            except json.JSONDecodeError as e:
                print(f"{FAILURE_COLOR}Error: Could not parse JSON output: {str(e)}{RESET_COLOR}")
                if self.verbose and output:
                    print(f"{FAILURE_COLOR}Raw output:{RESET_COLOR}")
                    print(output[:500])  # Print the first part of the output to help debug

        return success

    def test_list_agent_types(self) -> bool:
        """Test listing agent types."""
        print_header("Testing: List Agent Types")

        cmd = self.base_cmd + ["agents", "types"]
        exit_code, output = run_command(cmd, verbose=self.verbose)

        success = exit_code == 0
        self.results.append((success, "List agent types"))
        print_result(success, "List agent types", exit_code)

        return success

    def test_get_agent_json(self) -> bool:
        """Test getting agent details in JSON format."""
        print_header("Testing: Get Agent (JSON format)")

        if not self.calculator_agent_id:
            print(f"{FAILURE_COLOR}Cannot test get_agent - no calculator agent found{RESET_COLOR}")
            self.results.append((False, "Get agent JSON format"))
            return False

        cmd = self.base_cmd + ["agents", "get", self.calculator_agent_id, "--format", "json"]
        exit_code, output = run_command(cmd, verbose=self.verbose)

        success = exit_code == 0
        if success:
            try:
                # Extract just the JSON part from the output
                json_content = extract_json_from_output(output)
                data = json.loads(json_content)
                # Check if the output contains agent and version data
                if "agent" in data and "version" in data:
                    print(f"{INFO_COLOR}Successfully retrieved agent: {data['agent'].get('name')}{RESET_COLOR}")
                else:
                    success = False
            except json.JSONDecodeError:
                success = False
                print(f"{FAILURE_COLOR}Error: Could not parse JSON output{RESET_COLOR}")
                if self.verbose and output:
                    print(f"{FAILURE_COLOR}Raw output:{RESET_COLOR}")
                    print(output[:500])  # Print the first part of the output to help debug

        self.results.append((success, "Get agent JSON format"))
        print_result(success, "Get agent JSON format", exit_code)

        return success

    def test_list_versions(self) -> bool:
        """Test listing versions for an agent."""
        print_header("Testing: List Versions")

        if not self.calculator_agent_id:
            print(f"{FAILURE_COLOR}Cannot test list_versions - no calculator agent found{RESET_COLOR}")
            self.results.append((False, "List versions"))
            return False

        cmd = self.base_cmd + ["versions", "list", self.calculator_agent_id]
        exit_code, output = run_command(cmd, verbose=self.verbose)

        success = exit_code == 0
        self.results.append((success, "List versions"))
        print_result(success, "List versions", exit_code)

        # Try to get version ID for later use
        cmd = self.base_cmd + ["versions", "list", self.calculator_agent_id, "-f", "json"]
        exit_code, json_output = run_command(cmd, verbose=self.verbose)

        # Add this test result as well
        json_versions_success = exit_code == 0
        self.results.append((json_versions_success, "List versions (JSON format)"))
        print_result(json_versions_success, "List versions (JSON format)", exit_code)

        try:
            if exit_code == 0:
                # Extract just the JSON part from the output
                json_content = extract_json_from_output(json_output)
                data = json.loads(json_content)
                if data.get("versions") and len(data["versions"]) > 0:
                    self.calculator_version_id = data["versions"][0]["id"]
                    print(f"{INFO_COLOR}Found version: {self.calculator_version_id}{RESET_COLOR}")
            else:
                print(f"{FAILURE_COLOR}Failed to get versions in JSON format{RESET_COLOR}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"{FAILURE_COLOR}Could not extract version ID from output: {str(e)}{RESET_COLOR}")
            if self.verbose and json_output:
                print(f"{FAILURE_COLOR}Raw output:{RESET_COLOR}")
                print(json_output[:500])  # Print the first part of the output to help debug

        return success

    def test_get_version(self) -> bool:
        """Test getting a specific version."""
        print_header("Testing: Get Version")

        if not self.calculator_agent_id or not hasattr(self, "calculator_version_id"):
            print(f"{FAILURE_COLOR}Cannot test get_version - missing agent or version ID{RESET_COLOR}")
            self.results.append((False, "Get version"))
            return False

        cmd = self.base_cmd + ["versions", "get", self.calculator_agent_id, self.calculator_version_id]
        exit_code, output = run_command(cmd, verbose=self.verbose)

        success = exit_code == 0
        self.results.append((success, "Get version"))
        print_result(success, "Get version", exit_code)

        return success

    def test_list_models(self) -> bool:
        """Test listing available LLM models."""
        print_header("Testing: List LLM Models")

        cmd = self.base_cmd + ["resources", "models"]
        exit_code, output = run_command(cmd, verbose=self.verbose)

        success = exit_code == 0
        self.results.append((success, "List models"))
        print_result(success, "List models", exit_code)

        # Try to parse as JSON
        cmd = self.base_cmd + ["resources", "models", "-f", "json"]
        json_exit_code, json_output = run_command(cmd, verbose=self.verbose)

        json_success = json_exit_code == 0
        self.results.append((json_success, "List models (JSON format)"))
        print_result(json_success, "List models (JSON format)", json_exit_code)

        # Try filtering by agent type
        cmd = self.base_cmd + ["resources", "models", "--agent-type", "tool"]
        filter_exit_code, filter_output = run_command(cmd, verbose=self.verbose)

        filter_success = filter_exit_code == 0
        self.results.append((filter_success, "List models filtered by agent type"))
        print_result(filter_success, "List models filtered by agent type", filter_exit_code)

        return success and json_success and filter_success

    def test_list_guardrails(self) -> bool:
        """Test listing available guardrails."""
        print_header("Testing: List Guardrails")

        cmd = self.base_cmd + ["resources", "guardrails"]
        exit_code, output = run_command(cmd, verbose=self.verbose)

        success = exit_code == 0
        self.results.append((success, "List guardrails"))
        print_result(success, "List guardrails", exit_code)

        # Try to parse as JSON
        cmd = self.base_cmd + ["resources", "guardrails", "-f", "json"]
        json_exit_code, json_output = run_command(cmd, verbose=self.verbose)

        json_success = json_exit_code == 0
        self.results.append((json_success, "List guardrails (JSON format)"))
        print_result(json_success, "List guardrails (JSON format)", json_exit_code)

        return success and json_success

    def test_call_agent_json(self) -> bool:
        """Test invoking an agent with JSON output format."""
        print_header("Testing: Invoke Agent (JSON format)")

        if not self.test_agent_id:
            print(f"{FAILURE_COLOR}Cannot test agent JSON invocation - no test agent created{RESET_COLOR}")
            self.results.append((False, "Call agent with JSON format"))
            return False

        # Test with JSON output format
        cmd = self.base_cmd + ["invoke", "chat", self.test_agent_id, "--message", "What is 7 * 8?", "-f", "json"]
        exit_code, output = run_command(cmd, verbose=self.verbose)

        # Verify we get a successful response and can parse the JSON
        success = exit_code == 0
        json_data = None

        try:
            if success:
                json_content = extract_json_from_output(output)
                json_data = json.loads(json_content)

                # Print the actual structure for debugging
                if self.verbose:
                    print(f"{INFO_COLOR}Parsed JSON response structure:{RESET_COLOR}")
                    print(f"Keys at root level: {list(json_data.keys()) if isinstance(json_data, dict) else 'Not a dictionary'}")

                # Just check if it's a valid JSON dictionary - don't validate specific structure
                if not isinstance(json_data, dict):
                    print(f"{FAILURE_COLOR}JSON response is not a dictionary{RESET_COLOR}")
                    success = False
                else:
                    # Check if the answer (7*8=56) appears anywhere in the JSON response
                    response_text = json.dumps(json_data)
                    found_answer = "56" in response_text

                    if not found_answer:
                        print(f"{FAILURE_COLOR}Answer '56' not found in JSON response{RESET_COLOR}")
                        success = False
                    else:
                        print(f"{SUCCESS_COLOR}Answer '56' found in JSON response{RESET_COLOR}")
        except json.JSONDecodeError as e:
            print(f"{FAILURE_COLOR}Could not parse JSON output: {str(e)}{RESET_COLOR}")
            success = False

        self.results.append((success, "Call agent with JSON format"))
        print_result(success, "Call agent with JSON format", exit_code)

        return success

    def test_call_calculator(self) -> bool:
        """Test calling the Calculator_Test_3 agent."""
        print_header("Testing: Call Calculator Agent")

        if not self.calculator_agent_id:
            print(f"{FAILURE_COLOR}Cannot test calculator - no calculator agent found{RESET_COLOR}")
            self.results.append((False, "Call calculator agent"))
            return False

        # Use chat interface for tool agent, with a message asking to multiply 6 and 7
        cmd = self.base_cmd + ["invoke", "chat", self.calculator_agent_id, "--message", "multiply 6 and 7"]
        exit_code, output = run_command(cmd, verbose=self.verbose)

        # Check if output contains the result (6 * 7 = 42)
        success = exit_code == 0 and "42" in output
        self.results.append((success, "Call calculator agent"))
        print_result(success, "Call calculator agent", exit_code)

        # Also test with JSON output
        cmd = self.base_cmd + ["invoke", "chat", self.calculator_agent_id, "--message", "multiply 6 and 7", "-f", "json"]
        json_exit_code, json_output = run_command(cmd, verbose=self.verbose)

        # Add this test result as well
        json_chat_success = json_exit_code == 0
        self.results.append((json_chat_success, "Call calculator agent (JSON format)"))
        print_result(json_chat_success, "Call calculator agent (JSON format)", json_exit_code)

        # Just for debugging - can be removed after the issue is resolved
        if self.verbose:
            print(f"{INFO_COLOR}Analyzing JSON output:{RESET_COLOR}")
            print(f"Length: {len(json_output)}")
            print(f"First JSON bracket at: {json_output.find('{')}")
            print(f"First 100 chars: {json_output[:100]}")

        try:
            if json_exit_code == 0:
                # Extract just the JSON part from the output
                json_content = extract_json_from_output(json_output)
                json_result = json.loads(json_content)
                print(f"{INFO_COLOR}Calculator JSON result: {json.dumps(json_result, indent=2)}{RESET_COLOR}")
        except json.JSONDecodeError as e:
            print(f"{FAILURE_COLOR}Could not parse calculator JSON output: {str(e)}{RESET_COLOR}")
            if self.verbose and json_output:
                print(f"{FAILURE_COLOR}Raw output:{RESET_COLOR}")
                print(json_output[:500])  # Print the first part of the output to help debug

        return success

    def test_create_agent(self) -> bool:
        """Test creating a new agent."""
        print_header("Testing: Create Agent")

        # Create a unique name for the test agent
        test_agent_name = f"Test_Calculator_{str(uuid.uuid4())[:8]}"

        # Use static configuration file from tests/data
        config_path = os.path.join(os.path.dirname(__file__), "..", "data", "test_agent_config.json")

        # Check if the config file exists
        if not os.path.exists(config_path):
            print(f"{FAILURE_COLOR}Error: Agent config file not found at {config_path}{RESET_COLOR}")
            self.results.append((False, "Create agent - config file missing"))
            return False

        # Verify the configuration file is valid JSON
        try:
            with open(config_path) as f:
                config = json.load(f)
                print(f"{INFO_COLOR}Using agent configuration:{RESET_COLOR}")
                print(json.dumps(config, indent=2))
        except json.JSONDecodeError as e:
            print(f"{FAILURE_COLOR}Error: Invalid JSON in config file: {str(e)}{RESET_COLOR}")
            self.results.append((False, "Create agent - invalid config JSON"))
            return False
        except Exception as e:
            print(f"{FAILURE_COLOR}Error reading config file: {str(e)}{RESET_COLOR}")
            self.results.append((False, "Create agent - config file error"))
            return False

        # Construct the create agent command
        cmd = self.base_cmd + [
            "agents", "create",
            "--name", test_agent_name,
            "--description", "Test calculator agent for integration tests",
            "--type", "tool",  # Using tool type as we're creating a tool agent with functions
            "--config", config_path,
            "--version-label", "v1.0",
            "--notes", "Initial version for testing"
        ]

        if self.verbose:
            print(f"{INFO_COLOR}Agent configuration loaded from: {config_path}{RESET_COLOR}")
            with open(config_path) as f:
                print(f"{INFO_COLOR}Raw config content:{RESET_COLOR}")
                print(json.dumps(json.load(f), indent=2))

            # For better debugging, let's also print what the CLI will send to the API
            print(f"{INFO_COLOR}Command arguments:{RESET_COLOR}")
            print(f"  Name: {test_agent_name}")
            print("  Description: Test calculator agent for integration tests")
            print("  Type: tool")
            print("  Version Label: v1.0")
            print("  Notes: Initial version for testing")

        # Execute command and capture detailed output
        exit_code, output = run_command(cmd, verbose=self.verbose)
        create_success = exit_code == 0

        # Add more detailed error reporting
        if not create_success:
            print(f"{FAILURE_COLOR}Agent creation failed with exit code: {exit_code}{RESET_COLOR}")
            if "Invalid value" in output:
                print(f"{FAILURE_COLOR}Parameter validation error detected{RESET_COLOR}")
            if "already exists" in output:
                print(f"{FAILURE_COLOR}Agent with similar name might already exist{RESET_COLOR}")
            if "requires authentication" in output:
                print(f"{FAILURE_COLOR}Authentication error detected - check API credentials{RESET_COLOR}")
            if "Config validation failed" in output:
                print(f"{FAILURE_COLOR}The agent configuration format may be incorrect{RESET_COLOR}")

            # Add specific error snippets
            error_lines = [line for line in output.split("\n") if "Error" in line]
            if error_lines:
                print(f"{FAILURE_COLOR}Error details:{RESET_COLOR}")
                for line in error_lines:
                    print(f"  {line.strip()}")
        else:
            print(f"{SUCCESS_COLOR}Agent created successfully!{RESET_COLOR}")
            if "created successfully" not in output:
                print(f"{FAILURE_COLOR}Warning: Success response not found in output{RESET_COLOR}")

        # Get the agent ID if creation was successful
        if create_success:
            # Try to extract the agent ID directly from the output first
            agent_id_match = re.search(r"ID:\s+([a-zA-Z0-9-]+)", output)
            if agent_id_match:
                self.test_agent_id = agent_id_match.group(1)
                print(f"{INFO_COLOR}Extracted agent ID directly: {self.test_agent_id}{RESET_COLOR}")
            else:
                # If we can't extract from output, list agents and find by name
                print(f"{INFO_COLOR}Attempting to retrieve agent ID from agent list...{RESET_COLOR}")
                cmd = self.base_cmd + ["agents", "list", "-f", "json"]
                list_exit_code, json_output = run_command(cmd, verbose=self.verbose)

                if list_exit_code != 0:
                    print(f"{FAILURE_COLOR}Failed to list agents (exit code: {list_exit_code}){RESET_COLOR}")
                    create_success = False
                else:
                    try:
                        # Extract just the JSON part from the output
                        json_content = extract_json_from_output(json_output)
                        agents_data = json.loads(json_content)

                        # Debug - show all agent names to help identify matching issues
                        if self.verbose:
                            print(f"{INFO_COLOR}Available agents:{RESET_COLOR}")
                            for agent in agents_data.get("agents", []):
                                print(f"  {agent.get('name')} (ID: {agent.get('id')})")

                        # Try to find our agent by name
                        agent = find_agent_by_name(json_output, test_agent_name)
                        if agent:
                            self.test_agent_id = agent["id"]
                            print(f"{INFO_COLOR}Found agent in list: {test_agent_name} (ID: {self.test_agent_id}){RESET_COLOR}")
                        else:
                            print(f"{FAILURE_COLOR}Agent '{test_agent_name}' not found in agent list{RESET_COLOR}")
                            create_success = False
                    except Exception as e:
                        print(f"{FAILURE_COLOR}Error finding agent: {str(e)}{RESET_COLOR}")
                        create_success = False

        self.results.append((create_success, "Create agent"))
        print_result(create_success, "Create agent", exit_code)
        return create_success

    def test_call_new_agent(self) -> bool:
        """Test calling the newly created agent."""
        print_header("Testing: Call New Agent")

        if not self.test_agent_id:
            print(f"{FAILURE_COLOR}Cannot test new agent - no test agent created{RESET_COLOR}")
            self.results.append((False, "Call new agent"))
            return False

        # Test with chat command (simple question)
        cmd = self.base_cmd + ["invoke", "chat", self.test_agent_id, "--message", "What is 5 + 7?"]
        exit_code, output = run_command(cmd, verbose=self.verbose)

        chat_success = exit_code == 0 and "12" in output  # Check that it returns the correct answer
        chat_exit_code = exit_code

        # Test with chat command and JSON format
        cmd = self.base_cmd + ["invoke", "chat", self.test_agent_id, "--message", "What is 6 * 3?", "-f", "json"]
        task_exit_code, task_output = run_command(cmd, verbose=self.verbose)

        try:
            # For JSON output, just verify we got a successful response
            if task_exit_code == 0:
                # Extract just the JSON part from the output
                json_content = extract_json_from_output(task_output)
                json_data = json.loads(json_content)
                task_success = json_data is not None
            else:
                task_success = False
        except json.JSONDecodeError as e:
            print(f"{FAILURE_COLOR}Could not parse JSON output: {str(e)}{RESET_COLOR}")
            if self.verbose and task_output:
                print(f"{FAILURE_COLOR}Raw output:{RESET_COLOR}")
                print(task_output[:500])  # Print the first part of the output to help debug
            task_success = False

        success = chat_success and task_success
        self.results.append((success, "Call new agent"))
        print_result(chat_success, "Call new agent (chat)", chat_exit_code)
        print_result(task_success, "Call new agent (JSON format)", task_exit_code)

        return success

    def test_patch_agent(self) -> bool:
        """Test patching an agent's name/description."""
        print_header("Testing: Patch Agent")

        if not self.test_agent_id:
            print(f"{FAILURE_COLOR}Cannot test patch - no test agent created{RESET_COLOR}")
            self.results.append((False, "Patch agent"))
            return False

        # Get initial version information
        cmd = self.base_cmd + ["agents", "get", self.test_agent_id, "-f", "json"]
        get_exit_code, initial_output = run_command(cmd, verbose=self.verbose)

        if get_exit_code != 0:
            print(f"{FAILURE_COLOR}Failed to get agent details before patch (exit code: {get_exit_code}){RESET_COLOR}")

        try:
            # Extract just the JSON part from the output
            json_content = extract_json_from_output(initial_output)
            initial_data = json.loads(json_content)
            initial_version = initial_data.get("version", {}).get("number")
            print(f"{INFO_COLOR}Initial version: {initial_version}{RESET_COLOR}")
        except (json.JSONDecodeError, KeyError) as e:
            print(f"{FAILURE_COLOR}Could not determine initial version number: {str(e)}{RESET_COLOR}")
            if self.verbose and initial_output:
                print(f"{FAILURE_COLOR}Raw output:{RESET_COLOR}")
                print(initial_output[:500])
            initial_version = None

        # Patch the agent (update name and description)
        new_name = f"Patched_Calculator_{str(uuid.uuid4())[:8]}"
        cmd = self.base_cmd + [
            "agents", "patch",
            self.test_agent_id,
            "--name", new_name,
            "--description", "Updated description via patch"
        ]
        exit_code, output = run_command(cmd, verbose=self.verbose)

        patch_success = exit_code == 0 and "patched successfully" in output
        patch_exit_code = exit_code

        # Check that version number did not change
        cmd = self.base_cmd + ["agents", "get", self.test_agent_id, "-f", "json"]
        after_exit_code, after_output = run_command(cmd, verbose=self.verbose)

        if after_exit_code != 0:
            print(f"{FAILURE_COLOR}Failed to get agent details after patch (exit code: {after_exit_code}){RESET_COLOR}")
            version_unchanged = False
            name_updated = False

        try:
            # Extract just the JSON part from the output
            json_content = extract_json_from_output(after_output)
            after_data = json.loads(json_content)
            after_version = after_data.get("version", {}).get("number")
            print(f"{INFO_COLOR}Version after patch: {after_version}{RESET_COLOR}")

            version_unchanged = initial_version is not None and after_version == initial_version

            # Also verify name was updated
            name_updated = after_data.get("agent", {}).get("name") == new_name
        except (json.JSONDecodeError, KeyError) as e:
            print(f"{FAILURE_COLOR}Could not parse JSON after patch: {str(e)}{RESET_COLOR}")
            if self.verbose and after_output:
                print(f"{FAILURE_COLOR}Raw output:{RESET_COLOR}")
                print(after_output[:500])
            version_unchanged = False
            name_updated = False

        success = patch_success and version_unchanged and name_updated
        self.results.append((success, "Patch agent"))
        print_result(patch_success, "Patch operation successful", patch_exit_code)
        print_result(version_unchanged, "Version number unchanged")
        print_result(name_updated, "Name updated correctly")

        return success

    def test_update_agent(self) -> bool:
        """Test updating an agent (creating new version)."""
        print_header("Testing: Update Agent (New Version)")

        if not self.test_agent_id:
            print(f"{FAILURE_COLOR}Cannot test update - no test agent created{RESET_COLOR}")
            self.results.append((False, "Update agent"))
            return False

        # Get initial version information
        cmd = self.base_cmd + ["agents", "get", self.test_agent_id, "-f", "json"]
        get_exit_code, initial_output = run_command(cmd, verbose=self.verbose)

        if get_exit_code != 0:
            print(f"{FAILURE_COLOR}Failed to get agent details before update (exit code: {get_exit_code}){RESET_COLOR}")

        try:
            # Extract just the JSON part from the output
            json_content = extract_json_from_output(initial_output)
            initial_data = json.loads(json_content)
            initial_version = initial_data.get("version", {}).get("number")
            print(f"{INFO_COLOR}Initial version: {initial_version}{RESET_COLOR}")
            config = initial_data.get("version", {}).get("config", {})
        except (json.JSONDecodeError, KeyError) as e:
            print(f"{FAILURE_COLOR}Could not determine initial version number: {str(e)}{RESET_COLOR}")
            if self.verbose and initial_output:
                print(f"{FAILURE_COLOR}Raw output:{RESET_COLOR}")
                print(initial_output[:500])
            initial_version = None
            config = None

        # Create a temporary file with updated configuration
        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json', delete=False) as temp:
            # Use the existing config but update a parameter
            try:
                if config is not None:
                    # Modify the config
                    if isinstance(config, dict):
                        if "inference_config" in config:
                            config["inference_config"]["temperature"] = 0.2
                        else:
                            config["inference_config"] = {"temperature": 0.2}

                        # Add a new parameter
                        config["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        config = {
                            "llm_model_id": "anthropic.claude-3-haiku-20240307-v1:0",
                            "system_prompt": "You are an updated calculator assistant.",
                            "inference_config": {
                                "temperature": 0.2,
                                "max_tokens": 1000
                            },
                            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
            except (KeyError, AttributeError):
                # Default config if we couldn't read the existing one
                config = {
                    "llm_model_id": "anthropic.claude-3-haiku-20240307-v1:0",
                    "system_prompt": "You are an updated calculator assistant.",
                    "inference_config": {
                        "temperature": 0.2,
                        "max_tokens": 1000
                    },
                    "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }

            json.dump(config, temp)
            temp_path = temp.name

        try:
            # Update the agent (creates new version)
            cmd = self.base_cmd + [
                "agents", "update",
                self.test_agent_id,
                "--config", temp_path,
                "--version-label", "v1.1",
                "--notes", "Updated version with modified configuration"
            ]
            exit_code, output = run_command(cmd, verbose=self.verbose)

            update_success = exit_code == 0 and "updated successfully" in output
            update_exit_code = exit_code

            # Check that version number increased
            cmd = self.base_cmd + ["agents", "get", self.test_agent_id, "-f", "json"]
            after_exit_code, after_output = run_command(cmd, verbose=self.verbose)

            if after_exit_code != 0:
                print(f"{FAILURE_COLOR}Failed to get agent details after update (exit code: {after_exit_code}){RESET_COLOR}")
                version_increased = False

            try:
                # Extract just the JSON part from the output
                json_content = extract_json_from_output(after_output)
                after_data = json.loads(json_content)
                after_version = after_data.get("version", {}).get("number")
                print(f"{INFO_COLOR}Version after update: {after_version}{RESET_COLOR}")

                version_increased = (initial_version is not None and
                                    after_version is not None and
                                    int(after_version) > int(initial_version))
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"{FAILURE_COLOR}Could not parse JSON after update: {str(e)}{RESET_COLOR}")
                if self.verbose and after_output:
                    print(f"{FAILURE_COLOR}Raw output:{RESET_COLOR}")
                    print(after_output[:500])
                version_increased = False

            success = update_success and version_increased
            self.results.append((success, "Update agent"))
            print_result(update_success, "Update operation successful", update_exit_code)
            print_result(version_increased, "Version number increased")

            return success
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_delete_agent(self) -> bool:
        """Test deleting the test agent."""
        print_header("Testing: Delete Agent")

        if not self.test_agent_id:
            print(f"{FAILURE_COLOR}Cannot test delete - no test agent created{RESET_COLOR}")
            self.results.append((False, "Delete agent"))
            return False

        cmd = self.base_cmd + ["agents", "delete", self.test_agent_id, "--yes"]
        exit_code, output = run_command(cmd, verbose=self.verbose)

        delete_success = exit_code == 0 and "deleted" in output
        delete_exit_code = exit_code

        # Verify agent is gone by trying to get it
        cmd = self.base_cmd + ["agents", "get", self.test_agent_id]
        verify_exit_code, _ = run_command(cmd, verbose=self.verbose)

        verify_success = verify_exit_code != 0  # Should fail because agent is deleted

        success = delete_success and verify_success
        self.results.append((success, "Delete agent"))
        print_result(delete_success, "Delete operation successful", delete_exit_code)
        print_result(verify_success, "Agent no longer accessible", verify_exit_code)

        return success

    def print_summary(self) -> None:
        """Print a summary of all test results."""
        print_header("Test Results Summary")

        passed = sum(1 for result in self.results if result[0])
        total = len(self.results)

        for success, name in self.results:
            print_result(success, name)

        # Also provide a more detailed breakdown of any failures
        failures = [(name, i) for i, (success, name) in enumerate(self.results) if not success]
        if failures:
            print(f"\n{FAILURE_COLOR}Failed tests:{RESET_COLOR}")
            for name, i in failures:
                print(f"{FAILURE_COLOR}  - {name}{RESET_COLOR}")

        color = SUCCESS_COLOR if passed == total else FAILURE_COLOR
        print(f"\n{color}Passed {passed}/{total} tests ({passed/total*100:.1f}%){RESET_COLOR}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run integration tests for AB CLI")
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG,
        help=f"Path to config file (default: {DEFAULT_CONFIG})"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Display verbose output including all API commands and responses"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"{FAILURE_COLOR}Config file not found: {args.config}{RESET_COLOR}")
        print(f"{INFO_COLOR}Please create a config file or specify its location with --config{RESET_COLOR}")
        sys.exit(1)

    # Run all tests
    tests = IntegrationTests(config_path=args.config, verbose=args.verbose)
    success = tests.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)
