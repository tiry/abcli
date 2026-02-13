"""Chat page for the Agent Builder UI."""

import json
import subprocess
from typing import Any, cast

import streamlit as st


def show_chat_page() -> None:
    """Display the chat page with agent conversation interface."""
    st.title("Chat with Agent")

    # Get the configuration from the session state
    config = st.session_state.get("config")
    if not config:
        st.error("Configuration not loaded. Please check your settings.")
        return

    # Check if an agent is selected
    selected_agent = st.session_state.get("selected_agent")

    # If no agent is selected, show a selection dropdown
    if not selected_agent:
        agent_selection()
    else:
        chat_interface(selected_agent)


def agent_selection() -> None:
    """Display agent selection interface."""
    st.subheader("Select an Agent to Chat With")

    try:
        # Get list of agents
        agents = get_agents()

        if not agents:
            st.info("No agents found. Create an agent first.")
            if st.button("Go to Agent Management"):
                st.session_state.nav_intent = "Agents"
                st.rerun()
            return

        # Create a selectbox with agent names
        agent_names = [agent["name"] for agent in agents]
        selected_name = st.selectbox("Choose an agent", agent_names)

        # Find the selected agent
        selected_agent = next((a for a in agents if a["name"] == selected_name), None)

        if selected_agent and st.button("Start Chat"):
            st.session_state.selected_agent = selected_agent

            # Initialize chat history for this agent
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = {}

            agent_id = selected_agent["id"]
            if agent_id not in st.session_state.chat_history:
                st.session_state.chat_history[agent_id] = []

            st.rerun()

    except Exception as e:
        st.error(f"Error loading agents: {e}")


def chat_interface(agent: dict[str, Any]) -> None:
    """Display the chat interface for a selected agent.

    Args:
        agent: Dictionary containing agent information
    """
    st.subheader(f"Chat with {agent['name']}")

    # Show agent information
    with st.expander("Agent Details", expanded=False):
        st.markdown(f"**ID:** {agent['id']}")
        st.markdown(f"**Type:** {agent['type']}")

        # Get model information - check different possible locations
        model = None
        # Try to get from direct model field
        if "model" in agent:
            model = agent["model"]
        # Try to get from agent_config if available
        elif "agent_config" in agent and "llmModelId" in agent["agent_config"]:
            model = agent["agent_config"]["llmModelId"]
        # Fallback to type
        else:
            model = agent.get("type", "unknown")

        st.markdown(f"**Model:** {model}")

        if agent.get("description"):
            st.markdown(f"**Description:** {agent['description']}")

    # Get or initialize chat history for this agent
    agent_id = agent["id"]
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = {}
    if agent_id not in st.session_state.chat_history:
        st.session_state.chat_history[agent_id] = []

    # Display chat history
    chat_history = st.session_state.chat_history[agent_id]

    # Chat container with fixed height and scrolling
    chat_container = st.container()
    with chat_container:
        for message in chat_history:
            role = message["role"]
            content = message["content"]

            # Style based on role
            if role == "user":
                st.markdown(f"**You**: {content}")
            else:
                st.markdown(f"**{agent['name']}**: {content}")

            # Add a separator
            st.markdown("---")

    # Input area for new message
    with st.form("chat_input_form"):
        user_input = st.text_area("Your message:", height=100)
        submitted = st.form_submit_button("Send")

        if submitted and user_input:
            # Add user message to history
            chat_history.append({"role": "user", "content": user_input})

            # Get agent response through CLI with a loading spinner
            with st.spinner(f"Invoking agent {agent['name']}..."):
                try:
                    response = invoke_agent(agent, user_input)

                    # Add agent response to history with agent name for clarity
                    display_response = f"{response}"
                    chat_history.append({"role": "assistant", "content": display_response})

                    # Update session state
                    st.session_state.chat_history[agent_id] = chat_history

                    # Rerun to update the UI
                    st.rerun()

                except Exception as e:
                    st.error(f"Error getting response: {e}")

    # Button to clear chat history
    if st.button("Clear Chat History"):
        st.session_state.chat_history[agent_id] = []
        st.rerun()

    # Button to go back to agent selection
    if st.button("Change Agent"):
        st.session_state.selected_agent = None
        st.rerun()


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

    Uses the CLI directly to fetch the list of agents.

    Returns:
        List of agent dictionaries
    """
    try:
        # Get config from session state
        config = st.session_state.get("config")
        verbose = st.session_state.get("verbose", False)

        if not config:
            st.error("Configuration not loaded. Please check your settings.")
            raise ValueError("No configuration available")

        # Use the CLI directly
        import json

        # Run the CLI command to get agents with config at the top level
        cmd = ["ab"]

        # Add verbose flag if enabled
        if verbose:
            cmd.append("--verbose")

        if hasattr(config, "config_path") and config.config_path:
            cmd.extend(["--config", str(config.config_path)])
        cmd.extend(["agents", "list", "--format", "json"])

        try:
            # Show the command in verbose mode
            if verbose:
                print(f"Executing command: {' '.join(cmd)}")

            cmd_str = " ".join(cmd)

            # Use a spinner while executing the command
            with st.spinner("Loading agents..."):
                result = subprocess.run(
                    cmd_str, shell=True, capture_output=True, text=True, check=True
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
                    agents_data = json.loads(result.stdout)
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
                    # Try to get the model from agent_config if it exists
                    if "agent_config" in agent and "llmModelId" in agent["agent_config"]:
                        agent["model"] = agent["agent_config"]["llmModelId"]
                    # Otherwise use type as fallback
                    elif "model" not in agent:
                        agent["model"] = agent.get("type", "unknown")

                    agents.append(agent)

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
            "model": "gpt-4",
            "created_at": "2026-02-11T10:00:00Z",
        },
        {
            "id": "agent-456",
            "name": "Task Helper",
            "description": "Assists with task completion",
            "type": "task",
            "model": "claude-3",
            "created_at": "2026-02-10T14:30:00Z",
        },
    ]


def invoke_agent(agent: dict[str, Any], message: str) -> str:
    """Invoke an agent with a message using the CLI.

    Uses the CLI to invoke the agent with the given message.

    Args:
        agent: Dictionary containing agent information
        message: Message to send to the agent

    Returns:
        Agent's response
    """
    # Get config and verbose flag from session state
    config = st.session_state.get("config")
    verbose = st.session_state.get("verbose", False)

    # Use the CLI to invoke the agent
    try:
        import json
        import shlex
        import subprocess

        # Build the command to invoke the agent
        cmd = ["ab"]

        # Add verbose flag if enabled - this needs to be at the top level
        if verbose:
            cmd.append("--verbose")

        # Add config path if available
        if config and hasattr(config, "config_path") and config.config_path:
            cmd.extend(["--config", str(config.config_path)])

        # Add invoke command and parameters (quote the message to handle special characters)
        quoted_message = shlex.quote(message)
        cmd.extend(["invoke", "chat", agent["id"], "--message", quoted_message, "--format", "json"])

        if verbose:
            print(f"Executing command: {' '.join(cmd)}")

        # Execute the command
        cmd_str = " ".join(cmd)
        if verbose:
            print(f"Executing shell command: {cmd_str}")

        result = subprocess.run(
            cmd_str,
            shell=True,  # Use shell to properly handle quoting
            capture_output=True,
            text=True,
        )

        # Log command output in verbose mode
        if verbose:
            if result.stdout:
                print(f"Command stdout length: {len(result.stdout)} characters")
            if result.stderr:
                print(f"Command stderr:\n{result.stderr}")

        # Check if command was successful
        if result.returncode == 0:
            try:
                # Get the stdout and try to extract the JSON
                stdout = result.stdout

                # Parse the JSON output
                # In verbose mode, there might be debug output before the JSON
                response_data = None
                if verbose:
                    response_data = extract_json_from_text(stdout, verbose)
                    if not response_data:
                        print("Could not parse JSON from output")
                        return f"Could not parse agent response. Raw output: {stdout[:100]}..."
                else:
                    try:
                        response_data = cast(dict[str, Any], json.loads(stdout))
                    except json.JSONDecodeError:
                        # If we can't parse the JSON directly, try to extract it
                        response_data = extract_json_from_text(stdout, verbose)
                        if not response_data:
                            print("Could not parse JSON from output")
                            return f"Could not parse agent response. Raw output: {stdout[:100]}..."

                # Extract the response based on the response structure
                if response_data and "response" in response_data and response_data["response"]:
                    # Direct response field - this is the most straightforward case
                    if verbose:
                        print(
                            f"Found response in direct 'response' field: {response_data['response']}"
                        )
                    response_text: str = cast(str, response_data["response"])
                    return response_text
                elif response_data and "output" in response_data:
                    # Try to find response in output array
                    output = response_data["output"]
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
                                        if verbose:
                                            print(
                                                f"Found response in output.content.text: {response_text}"
                                            )
                                        return response_text

                # If we couldn't extract a response using the structured approach,
                # try to find any text field that looks like a response
                if verbose:
                    print(
                        "Couldn't extract response using standard structure, looking for any response field"
                    )

                # Check for common response fields
                if response_data:
                    for field in ["response", "answer", "text", "message"]:
                        if field in response_data and isinstance(response_data[field], str):
                            if verbose:
                                print(f"Found response in field '{field}': {response_data[field]}")
                            return cast(str, response_data[field])

                    # Try to find any message content in the response
                    extracted_text = extract_text_from_object(response_data)
                    if extracted_text:
                        if verbose:
                            print(f"Found text through deep extraction: {extracted_text}")
                        return extracted_text

                # Fallback to raw output if we couldn't parse the structure
                return stdout
            except Exception as e:
                if verbose:
                    print(f"Error processing response: {e}")
                return f"Error processing agent response: {e}"
        else:
            # Command failed
            error_msg = f"Error invoking agent: {result.stderr}"
            if verbose:
                print(error_msg)

            # Fallback to a generic response for demo purposes
            agent_name = agent.get("name", "Unknown")
            return (
                f"[Demo Mode] This is a placeholder response from {agent_name}. You said: {message}"
            )

    except Exception as e:
        # Log the exception in verbose mode
        if verbose:
            import traceback

            print(f"Exception invoking agent: {e}")
            print(traceback.format_exc())

        # Fallback to a generic response
        agent_name = agent.get("name", "Unknown")
        return f"[Demo Mode] This is a placeholder response from {agent_name}. You said: {message}"


def extract_text_from_object(obj: Any) -> str:
    """Recursively extract text from nested objects."""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        if "text" in obj:
            return cast(str, obj["text"])
        if "content" in obj:
            content_text = extract_text_from_object(obj["content"])
            if content_text:
                return content_text
        for k, v in obj.items():
            if k.lower() in ["message", "response", "answer", "text"]:
                result = extract_text_from_object(v)
                if result:
                    return result
    if isinstance(obj, list):
        for item in obj:
            result = extract_text_from_object(item)
            if result:
                return result
    # Default to empty string if no text could be found
    return "No response text found"
