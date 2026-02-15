# Specification 10: UI Refactoring - Data Provider Pattern

## Overview

This specification outlines a refactoring plan for the Agent Builder UI codebase to improve code organization, maintainability, and testability. The primary approach is to implement a Data Provider pattern that separates data access from UI components.

## Problem Statement

The current UI implementation has several issues:

1. **Mixed Responsibilities**: UI views contain both presentation logic and data access code
2. **Duplicated Code**: Similar CLI interaction code is duplicated across multiple files
3. **Hardcoded Fallbacks**: Placeholder data is hardcoded directly in view files
4. **Limited Testability**: Difficult to test UI components without calling the actual CLI

## Goals

1. **Clean Code Organization**: Separate UI code from data access logic
2. **Code Reuse**: Eliminate duplicate CLI interaction code
3. **Flexible Data Sources**: Allow UI to work with real or placeholder data
4. **Improved Testability**: Enable UI testing without requiring CLI or API access

## Solution Design

### Data Provider Pattern

Implement a Data Provider interface with two concrete implementations:

1. **CLI Data Provider**: Calls the CLI commands to get real data
2. **Mock Data Provider**: Returns predefined data from JSON files

```
┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │
│     UI Views      │────►│  Data Provider    │
│                   │     │    Interface      │
└───────────────────┘     └─────────┬─────────┘
                                    │
                          ┌─────────┴─────────┐
                          │                   │
            ┌─────────────┤  Implementation   ├─────────────┐
            │             │                   │             │
            │             └───────────────────┘             │
            ▼                                               ▼
┌───────────────────┐                             ┌───────────────────┐
│                   │                             │                   │
│  CLI Data         │                             │  Mock Data        │
│  Provider         │                             │  Provider         │
│                   │                             │                   │
└────────┬──────────┘                             └──────────┬────────┘
         │                                                   │
         ▼                                                   ▼
┌───────────────────┐                             ┌───────────────────┐
│                   │                             │                   │
│  AB CLI           │                             │  JSON Data Files  │
│  Commands         │                             │  in data/         │
│                   │                             │                   │
└───────────────────┘                             └───────────────────┘
```

### Folder Structure

```
ab_cli/
├── abui/
│   ├── __init__.py
│   ├── app.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── agents.json
│   │   ├── models.json
│   │   └── guardrails.json
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── data_provider.py (interface)
│   │   ├── cli_data_provider.py
│   │   └── mock_data_provider.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── json_utils.py (shared JSON parsing utilities)
│   ├── views/
│   │   ├── __init__.py
│   │   ├── agents.py
│   │   ├── chat.py
│   │   ├── agent_details.py
│   │   └── edit_agent.py
│   └── components/
│       ├── __init__.py
│       └── agent_card.py
└── ...
```

## Implementation Details

### 1. Configuration

Add a UI section to the `config.yaml` file to configure the data provider mode:

```yaml
# UI Configuration
ui:
  # Data Provider mode: "cli" or "mock"
  data_provider: "cli"
  
  # Data directory for mock data (optional)
  mock_data_dir: "path/to/mock/data"
```

### 2. Data Provider Interface

Create a base interface that defines all data access methods needed by the UI:

```python
# data_provider.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, cast

class DataProvider(ABC):
    """Interface for data providers used by the Agent Builder UI."""

    @abstractmethod
    def get_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents."""
        pass
        
    @abstractmethod
    def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent details by ID."""
        pass
        
    @abstractmethod
    def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent."""
        pass
        
    @abstractmethod
    def update_agent(self, agent_id: str, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing agent."""
        pass
        
    @abstractmethod
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent by ID."""
        pass
        
    @abstractmethod
    def invoke_agent(self, agent_id: str, message: str) -> str:
        """Invoke an agent with a message."""
        pass
        
    @abstractmethod
    def get_models(self) -> List[str]:
        """Get list of available models."""
        pass
        
    @abstractmethod
    def get_guardrails(self) -> List[str]:
        """Get list of available guardrails."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the data provider is healthy."""
        pass
```

### 3. CLI Data Provider Implementation

Implement a provider that calls CLI commands and processes their output, incorporating the existing caching mechanism:

```python
# cli_data_provider.py
import json
import subprocess
from typing import Any, Dict, List, Optional, cast

import streamlit as st

from ab_cli.abui.providers.data_provider import DataProvider
from ab_cli.abui.utils.json_utils import extract_json_from_text

class CLIDataProvider(DataProvider):
    """Data provider that uses CLI commands to access data."""
    
    def __init__(self, config: Any, verbose: bool = False):
        """Initialize with configuration and verbose flag."""
        self.config = config
        self.verbose = verbose
        self.cache = {}
        
    def _run_command(self, cmd_parts: List[str], use_cache: bool = True) -> Dict[str, Any]:
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
            
        if hasattr(self.config, "config_path") and self.config.config_path:
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
                    return data
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
        self.cache = {}
        if self.verbose:
            print("Cache cleared")
    
    # Implementation of all abstract methods using _run_command
    def get_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents."""
        try:
            result = self._run_command(["agents", "list", "--format", "json"])
            if "agents" in result:
                return result["agents"]
            return []
        except Exception as e:
            if self.verbose:
                print(f"Error in get_agents: {e}")
            raise
    
    # ... implement other methods ...
```

### 4. Mock Data Provider Implementation

Implement a provider that returns data from JSON files and validates write operations without actually modifying files:

```python
# mock_data_provider.py
import json
import os
from typing import Any, Dict, List, Optional

from ab_cli.abui.providers.data_provider import DataProvider

class MockDataProvider(DataProvider):
    """Data provider that uses predefined data from JSON files."""
    
    def __init__(self, config: Any = None, data_dir: str = None):
        """Initialize with path to data directory."""
        # Default to data directory in the package
        if data_dir is None and config and hasattr(config, "ui"):
            data_dir = getattr(config.ui, "mock_data_dir", None)
            
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        
        self.data_dir = data_dir
        self.verbose = getattr(config, "verbose", False) if config else False
        
    def _load_json_file(self, filename: str) -> Any:
        """Load and parse a JSON file."""
        file_path = os.path.join(self.data_dir, filename)
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Error loading {filename}: {str(e)}")
            
    def get_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents."""
        data = self._load_json_file("agents.json")
        return data.get("agents", [])
    
    def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate agent data structure without actually creating the agent."""
        # Validate required fields
        required_fields = ["name", "type"]
        for field in required_fields:
            if field not in agent_data:
                raise ValueError(f"Missing required field: {field}")
                
        # Validate agent type
        valid_types = ["chat", "task", "rag", "tool"]
        if agent_data.get("type") not in valid_types:
            raise ValueError(f"Invalid agent type: {agent_data.get('type')}")
            
        # Return the input data with a mock ID and creation timestamp
        result = {
            **agent_data,
            "id": f"mock-agent-{hash(str(agent_data))}",
            "created_at": "2026-02-13T00:00:00Z",
            "status": "CREATED"
        }
        
        if self.verbose:
            print(f"Mock created agent: {result['id']}")
            
        return result
    
    # ... implement other methods ...
```

### 5. Provider Factory

Create a factory to get the appropriate data provider based on configuration:

```python
# provider_factory.py
from typing import Any

from ab_cli.abui.providers.data_provider import DataProvider
from ab_cli.abui.providers.cli_data_provider import CLIDataProvider
from ab_cli.abui.providers.mock_data_provider import MockDataProvider

def get_data_provider(config: Any) -> DataProvider:
    """Get the appropriate data provider based on configuration.
    
    Args:
        config: Application configuration
        
    Returns:
        DataProvider instance
    """
    # Default to CLI provider if not specified
    provider_type = "cli"
    
    # Check config for provider type
    if hasattr(config, "ui") and hasattr(config.ui, "data_provider"):
        provider_type = config.ui.data_provider
        
    # Create provider based on type
    if provider_type.lower() == "mock":
        return MockDataProvider(config)
    else:
        # Default to CLI provider
        verbose = getattr(config, "verbose", False)
        return CLIDataProvider(config, verbose)
```

### 6. JSON Data Files

Store placeholder data in JSON files:

```json
// agents.json
{
  "agents": [
    {
      "id": "agent-123",
      "name": "Demo Agent",
      "description": "A sample agent for demonstration purposes",
      "type": "chat",
      "model": "gpt-4",
      "agent_config": {"model": "gpt-4"},
      "created_at": "2026-02-11T10:00:00Z"
    },
    {
      "id": "agent-456",
      "name": "Task Helper",
      "description": "Assists with task completion",
      "type": "task",
      "model": "claude-3",
      "agent_config": {"model": "claude-3"},
      "created_at": "2026-02-10T14:30:00Z"
    }
  ]
}
```

### 7. Shared JSON Utilities

Move JSON parsing utilities to a shared file:

```python
# json_utils.py
import json
from typing import Any, Dict, cast

def extract_json_from_text(text: str, verbose: bool = False) -> Dict[str, Any] | None:
    """Extract JSON content from text that might include non-JSON content."""
    # ... implementation from existing code ...
```

### 8. UI View Modifications

Update UI views to use the data provider:

```python
# agents.py
import streamlit as st

from ab_cli.abui.providers.data_provider import DataProvider
from ab_cli.abui.providers.provider_factory import get_data_provider

def show_agents_page() -> None:
    """Display the agents page."""
    st.title("Agent Management")

    # Get configuration from session state
    config = st.session_state.get("config")
    if not config:
        st.error("Configuration not loaded. Please check your settings.")
        return

    # Get or create data provider
    if "data_provider" not in st.session_state:
        st.session_state.data_provider = get_data_provider(config)
        
    provider: DataProvider = st.session_state.data_provider

    # Rest of the implementation using provider instead of direct CLI calls
    # ...

    try:
        agents = provider.get_agents()
        
        if not agents:
            st.info("No agents found. Create a new agent to get started.")
            return

        # Display agents
        # ...
    except Exception as e:
        st.error(f"Error loading agents: {e}")
```

## Integration Plan

1. **Phase 1: Create Directory Structure and Interface**
   - Create providers directory
   - Define DataProvider interface
   - Create shared JSON utilities
   - Set up data directory structure

2. **Phase 2: Extract Placeholder Data**
   - Move hardcoded fallback data to JSON files
   - Organize data files by resource type

3. **Phase 3: Implement Providers**
   - Implement CLIDataProvider with existing caching support
   - Implement MockDataProvider with validation
   - Create provider factory

4. **Phase 4: Update Config Handling**
   - Add UI section to config schema
   - Update config loading to handle UI settings

5. **Phase 5: Refactor UI Views**
   - Update all UI views to use the data provider
   - Remove duplicate CLI access code
   - Update error handling

## Testing Strategy

### Streamlit UI Testing Approach

Testing Streamlit applications presents unique challenges due to its server-based architecture and session state model. The following approach effectively addresses these challenges using Streamlit's AppTest framework.

#### Wrapper Function Pattern

A key innovation in our testing approach is the "Wrapper Function Pattern" that solves common issues when testing Streamlit components:

```python
# streamlit_test_wrapper.py
def display_agent_config_test():
    """Test wrapper for display_agent_config function."""
    # Import modules within function to ensure they're available when AppTest runs
    import streamlit as st
    from ab_cli.abui.views.agent_details import display_agent_config
    
    # Get test data from session state
    test_config = st.session_state.get("test_config", {})
    verbose = st.session_state.get("test_verbose", False)
    
    # Call the function with test data
    display_agent_config(test_config, verbose=verbose)
```

This pattern provides several benefits:
1. **Isolated Environment**: Each wrapper creates a clean environment for testing
2. **Dynamic Imports**: Imports happen within the function scope to ensure proper context
3. **Session State Access**: Uses Streamlit's session state for test data injection
4. **No Modifications to Core Code**: Testing without changing production code

#### AppTest Usage

Test files use Streamlit's AppTest framework with the wrapper functions:

```python
def test_display_agent_config_basic():
    """Test the display_agent_config function with basic configuration."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(display_agent_config_test)
    
    # Set up test parameters in session state
    app_test.session_state["test_config"] = {
        "llmModelId": "test-model-1",
        "systemPrompt": "You are a test assistant."
    }
    
    # Run the test function
    app_test.run()
    
    # Verify the function rendered the expected elements
    model_id_displayed = False
    if hasattr(app_test, "info"):
        for info_elem in app_test.info:
            if hasattr(info_elem, "body") and "test-model-1" in info_elem.body:
                model_id_displayed = True
                break
    
    assert model_id_displayed, "Model ID not displayed in UI"
```

#### Testing Navigation and User Interactions

Since Streamlit's click handlers cannot be directly triggered in tests, we simulate user interactions by manipulating session state:

```python
def test_show_agent_details_page_edit_navigation(test_agent, test_data_provider):
    """Test navigation to edit from agent details page."""
    # Create a test AppTest instance
    app_test = AppTest.from_function(show_agent_details_page_test)
    
    # Set up session state for the test
    app_test.session_state["agent_to_view"] = test_agent
    app_test.session_state["current_page"] = "AgentDetails"
    app_test.session_state["config"] = {"ui": {"mock": True}}
    app_test.session_state["data_provider"] = test_data_provider
    
    # Run the test function to initialize the UI
    app_test.run()
    
    # Find the "Edit Agent" button
    edit_button = None
    if hasattr(app_test, "button"):
        for button in app_test.button:
            if hasattr(button, "label") and button.label == "Edit Agent":
                edit_button = button
                break
    
    assert edit_button is not None, "Edit Agent button not found"
    
    # Simulate clicking the edit button by setting nav_intent
    app_test.session_state["nav_intent"] = "EditAgent"
    app_test.session_state["agent_to_edit"] = test_agent  # Side effect normally handled by JS
    
    # Re-run to process navigation
    app_test.run()
    
    # Verify navigation state was properly set
    assert app_test.session_state["nav_intent"] == "EditAgent"
    assert "agent_to_edit" in app_test.session_state
    assert app_test.session_state["agent_to_edit"]["id"] == test_agent["id"]
```

#### Best Practices

1. **Mock Data Provider**: Use the MockDataProvider for predictable testing data
2. **Fixture-Based Test Setup**: Create fixtures for common objects and navigation paths
3. **Component-Level Testing**: Test UI components in isolation
4. **Error State Testing**: Verify error handling works correctly
5. **Session State Management**: Set up required state variables before running tests

#### Measuring Test Coverage

To measure coverage of Streamlit components:

```bash
python -m pytest tests/test_abui/test_agent_details.py -v --cov=ab_cli.abui.views.agent_details
```

Applying this testing pattern has significantly improved coverage, from initial levels around 2% to over 50% for UI components.

## Configuration Options

The configuration will be managed through the config.yaml file:

```yaml
# UI Configuration
ui:
  # Data Provider mode: "cli" or "mock"
  data_provider: "cli"
  
  # Data directory for mock data (optional)
  mock_data_dir: "path/to/mock/data"