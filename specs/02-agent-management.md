# Phase 2: Agent Management

**Status:** Complete  
**Spec Reference:** `specs/00-draft-spec.md`  
**Previous Phase:** Phase 1 - Foundation (Complete)

---

## 1. Overview

This phase implements agent and version management commands for the Agent Builder CLI (`ab-cli`). It enables users to list, create, get, update, and delete AI agents, as well as manage their versions.

### 1.1 Goals

- Implement agent data models
- Create API client methods for agent operations
- Implement agent CLI commands (list, create, get, update, delete)
- Implement version CLI commands (list, create, get)
- Support multiple output formats (table, JSON, YAML)

---

## 2. API Endpoints

Based on the Agent Builder API specification:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/agents` | List all agents (with pagination & filters) |
| `POST` | `/v1/agents` | Create a new agent |
| `GET` | `/v1/agents/types` | List available agent types |
| `GET` | `/v1/agents/{agent_id}/versions` | List all versions of an agent |
| `POST` | `/v1/agents/{agent_id}/versions` | Create a new version of an agent |
| `GET` | `/v1/agents/{agent_id}/versions/{version_id}` | Get specific version details |
| `PATCH` | `/v1/agents/{agent_id}` | Update agent name/description |
| `DELETE` | `/v1/agents/{agent_id}` | Delete an agent |

---

## 3. Data Models

### 3.1 Agent Models (`ab_cli/models/agent.py`)

```python
def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class CamelModel(BaseModel):
    """Base model with camelCase serialization."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class Pagination(CamelModel):
    """Pagination information for list responses."""

    limit: int
    offset: int
    total_items: int  # Maps to totalItems
    has_more: bool = False  # Maps to hasMore


class Agent(CamelModel):
    """Agent response model."""

    id: UUID
    type: str
    name: str
    description: str
    status: str = "CREATED"
    is_global_agent: bool = False
    current_version_id: UUID | None = None
    created_at: str
    created_by: str
    modified_at: str
    modified_by: str | None = None


class AgentList(CamelModel):
    """List of agents with pagination."""

    agents: list[Agent]
    pagination: Pagination


class AgentCreate(CamelModel):
    """Model for creating a new agent."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=200)
    agent_type: str
    version_label: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=255)
    config: dict[str, Any]


class AgentUpdate(CamelModel):
    """Model for updating an agent (creates new version)."""

    version_label: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=255)
    config: dict[str, Any] | None = None


class AgentPatch(CamelModel):
    """Model for patching agent name/description without new version."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=200)


class Version(CamelModel):
    """Version summary model (without config)."""

    id: UUID
    number: int
    version_label: str | None = None
    notes: str | None = None
    created_at: str
    created_by: str


class VersionConfig(Version):
    """Version model with full configuration."""

    config: dict[str, Any]


class VersionCreate(CamelModel):
    """Model for creating a new version."""

    version_label: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=255)
    config: dict[str, Any]


class VersionList(CamelModel):
    """List of versions with associated agent and pagination."""

    agent: Agent
    versions: list[Version]
    pagination: Pagination


class AgentVersion(CamelModel):
    """Agent with its current version configuration."""

    agent: Agent
    version: VersionConfig


class AgentType(CamelModel):
    """Agent type information."""

    type: str
    description: str


class AgentTypeList(CamelModel):
    """List of available agent types."""

    agent_types: list[AgentType]
    pagination: Pagination
```

---

## 4. API Client Methods

Add the following methods to `AgentBuilderClient` in `ab_cli/api/client.py`:

### 4.1 Agent Operations

```python
def list_agents(
    self,
    limit: int = 50,
    offset: int = 0,
) -> AgentList:
    """List all agents.

    Args:
        limit: Maximum number of agents to return.
        offset: Offset for pagination.

    Returns:
        List of agents with pagination info.
    """
    data = self._request(
        "GET",
        "/agents",
        params={"limit": limit, "offset": offset},
    )
    return AgentList.model_validate(data)

def get_agent(self, agent_id: str | UUID, version_id: str | UUID | None = None) -> AgentVersion:
    """Get an agent by ID with a specific version or latest.

    Args:
        agent_id: The agent ID.
        version_id: The version ID or 'latest' (default: 'latest').

    Returns:
        Agent with version configuration.
    """
    version = version_id or "latest"
    data = self._request("GET", f"/agents/{agent_id}/versions/{version}")
    return AgentVersion.model_validate(data)

def create_agent(self, agent: AgentCreate) -> AgentVersion:
    """Create a new agent.

    Args:
        agent: Agent creation data.

    Returns:
        Created agent with version.
    """
    data = self._request(
        "POST",
        "/agents",
        json=agent.model_dump(by_alias=True, exclude_none=True),
    )
    return AgentVersion.model_validate(data)

def update_agent(self, agent_id: str | UUID, update: AgentUpdate) -> AgentVersion:
    """Update an agent (creates a new version).

    Args:
        agent_id: The agent ID.
        update: Update data.

    Returns:
        Updated agent with new version.
    """
    data = self._request(
        "PUT",
        f"/agents/{agent_id}",
        json=update.model_dump(by_alias=True, exclude_none=True),
    )
    return AgentVersion.model_validate(data)

def patch_agent(self, agent_id: str | UUID, patch: AgentPatch) -> Agent:
    """Patch an agent's name/description without creating a new version.

    Args:
        agent_id: The agent ID.
        patch: Patch data.

    Returns:
        Updated agent.
    """
    data = self._request(
        "PATCH",
        f"/agents/{agent_id}",
        json=patch.model_dump(by_alias=True, exclude_none=True),
    )
    return Agent.model_validate(data)

def delete_agent(self, agent_id: str | UUID) -> None:
    """Delete an agent.

    Args:
        agent_id: The agent ID.
    """
    self._request("DELETE", f"/agents/{agent_id}")

def list_agent_types(
    self,
    limit: int = 50,
    offset: int = 0,
) -> AgentTypeList:
    """List available agent types.

    Args:
        limit: Maximum number of types to return.
        offset: Offset for pagination.

    Returns:
        List of agent types.
    """
    data = self._request(
        "GET",
        "/agents/types",
        params={"limit": limit, "offset": offset},
    )
    return AgentTypeList.model_validate(data)
```

### 4.2 Version Operations

```python
def list_versions(
    self,
    agent_id: str | UUID,
    limit: int = 50,
    offset: int = 0,
) -> VersionList:
    """List all versions of an agent.

    Args:
        agent_id: The agent ID.
        limit: Maximum number of versions to return.
        offset: Offset for pagination.

    Returns:
        List of versions with pagination info.
    """
    data = self._request(
        "GET",
        f"/agents/{agent_id}/versions",
        params={"limit": limit, "offset": offset},
    )
    return VersionList.model_validate(data)

def get_version(self, agent_id: str | UUID, version_id: str | UUID) -> AgentVersion:
    """Get a specific version of an agent.

    Args:
        agent_id: The agent ID.
        version_id: The version ID.

    Returns:
        Agent with the specified version configuration.
    """
    data = self._request("GET", f"/agents/{agent_id}/versions/{version_id}")
    return AgentVersion.model_validate(data)

def create_version(
    self,
    agent_id: str | UUID,
    version: VersionCreate,
) -> AgentVersion:
    """Create a new version of an agent.

    Args:
        agent_id: The agent ID.
        version: Version creation data.

    Returns:
        Agent with the new version.
    """
    data = self._request(
        "POST",
        f"/agents/{agent_id}/versions",
        json=version.model_dump(by_alias=True, exclude_none=True),
    )
    return AgentVersion.model_validate(data)
```

---

## 5. CLI Commands

### 5.1 Agent Command Group (`ab_cli/cli/agents.py`)

```python
@click.group()
def agents() -> None:
    """Manage agents (list, create, update, delete)."""
    pass


@agents.command("list")
@click.option("--limit", "-l", default=50, help="Maximum number of agents to return")
@click.option("--offset", "-o", default=0, help="Offset for pagination")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json", "yaml"]), 
              default="table", help="Output format")
@click.pass_context
def list_agents(ctx: click.Context, limit: int, offset: int, output_format: str) -> None:
    """List all agents in the environment."""
    # Implementation


@agents.command("get")
@click.argument("agent_id")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json", "yaml"]), 
              default="table", help="Output format")
@click.pass_context
def get_agent(ctx: click.Context, agent_id: str, output_format: str) -> None:
    """Get details of a specific agent."""
    # Implementation


@agents.command("create")
@click.option("--name", "-n", required=True, help="Agent name")
@click.option("--description", "-d", required=True, help="Agent description")
@click.option("--type", "-t", "agent_type", required=True, help="Agent type (base, tool, rag, task)")
@click.option("--config", "-c", "config_file", required=True, type=click.Path(exists=True),
              help="Path to JSON config file")
@click.option("--version-label", "-v", help="Version label (e.g., v1.0)")
@click.option("--notes", help="Version notes")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json", "yaml"]), 
              default="table", help="Output format")
@click.pass_context
def create_agent(
    ctx: click.Context,
    name: str,
    description: str,
    agent_type: str,
    config_file: str,
    version_label: str | None,
    notes: str | None,
    output_format: str,
) -> None:
    """Create a new agent."""
    # Implementation


@agents.command("update")
@click.argument("agent_id")
@click.option("--config", "-c", "config_file", type=click.Path(exists=True),
              help="Path to JSON config file")
@click.option("--version-label", "-v", help="Version label (e.g., v2.0)")
@click.option("--notes", help="Version notes")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json", "yaml"]), 
              default="table", help="Output format")
@click.pass_context
def update_agent(
    ctx: click.Context,
    agent_id: str,
    config_file: str | None,
    version_label: str | None,
    notes: str | None,
    output_format: str,
) -> None:
    """Update an agent (creates a new version)."""
    # Implementation


@agents.command("patch")
@click.argument("agent_id")
@click.option("--name", "-n", help="New agent name")
@click.option("--description", "-d", help="New agent description")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json", "yaml"]), 
              default="table", help="Output format")
@click.pass_context
def patch_agent(
    ctx: click.Context,
    agent_id: str,
    name: str | None,
    description: str | None,
    output_format: str,
) -> None:
    """Patch an agent's name/description (no new version)."""
    # Implementation


@agents.command("delete")
@click.argument("agent_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_agent(ctx: click.Context, agent_id: str, yes: bool) -> None:
    """Delete an agent."""
    # Implementation


@agents.command("types")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json", "yaml"]), 
              default="table", help="Output format")
@click.pass_context
def list_agent_types(ctx: click.Context, output_format: str) -> None:
    """List available agent types."""
    # Implementation
```

### 5.2 Version Command Group (`ab_cli/cli/versions.py`)

```python
@click.group()
def versions() -> None:
    """Manage agent versions (list, get, create)."""
    pass


@versions.command("list")
@click.argument("agent_id")
@click.option("--limit", "-l", default=50, help="Maximum number of versions to return")
@click.option("--offset", "-o", default=0, help="Offset for pagination")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json", "yaml"]), 
              default="table", help="Output format")
@click.pass_context
def list_versions(
    ctx: click.Context, 
    agent_id: str, 
    limit: int, 
    offset: int, 
    output_format: str
) -> None:
    """List all versions of an agent."""
    # Implementation


@versions.command("get")
@click.argument("agent_id")
@click.argument("version_id")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json", "yaml"]), 
              default="table", help="Output format")
@click.pass_context
def get_version(
    ctx: click.Context, 
    agent_id: str, 
    version_id: str, 
    output_format: str
) -> None:
    """Get details of a specific version."""
    # Implementation


@versions.command("create")
@click.argument("agent_id")
@click.option("--config", "-c", "config_file", required=True, type=click.Path(exists=True),
              help="Path to JSON config file")
@click.option("--version-label", "-v", help="Version label (e.g., v2.0)")
@click.option("--notes", help="Version notes")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json", "yaml"]), 
              default="table", help="Output format")
@click.pass_context
def create_version(
    ctx: click.Context,
    agent_id: str,
    config_file: str,
    version_label: str | None,
    notes: str | None,
    output_format: str,
) -> None:
    """Create a new version for an agent."""
    # Implementation
```

### 5.3 Main CLI Integration

Add command groups to `ab_cli/cli/main.py`:

```python
# Import command groups
from ab_cli.cli.agents import agents
from ab_cli.cli.versions import versions

# Register command groups
main.add_command(agents)
main.add_command(versions)
```

---

## 6. Output Formatting

Implement output formatters for different formats:

### 6.1 Table Format (using Rich)

```python
def output_table(data: Any) -> None:
    """Output data as formatted table."""
    # Implementation using Rich tables
```

### 6.2 JSON Format

```python
def output_json(data: dict) -> None:
    """Output data as JSON."""
    console.print_json(json.dumps(data, default=str))
```

### 6.3 YAML Format

```python
def output_yaml(data: dict) -> None:
    """Output data as YAML."""
    console.print(yaml.dump(data, default_flow_style=False))
```

---

## 7. Files to Create/Modify

### New Files

| File | Description |
|------|-------------|
| `ab_cli/models/agent.py` | Agent and version data models |
| `ab_cli/cli/agents.py` | Agent management commands |
| `ab_cli/cli/versions.py` | Version management commands |
| `tests/test_models/test_agent.py` | Tests for agent models |
| `tests/test_api/test_client.py` | Tests for API client |

### Files to Modify

| File | Description | Changes |
|------|-------------|---------|
| `ab_cli/api/client.py` | API client | Add agent/version methods |
| `ab_cli/cli/main.py` | CLI entry point | Register command groups |
| `ab_cli/models/__init__.py` | Models package | Export agent models |

---

## 8. Testing Strategy

### 8.1 Unit Tests

- Test data models for validation and serialization
- Test API client methods with mocked responses
- Test CLI commands with test runner

### 8.2 Integration Tests

- Test agent creation and retrieval
- Test version management
- Test output formatting

---

## 9. Example Usage

### 9.1 Agent Management

```bash
# List all agents
ab agents list

# List agent types
ab agents types

# Create a new agent
ab agents create \
  --name "My RAG Agent" \
  --type "rag" \
  --description "Knowledge assistant" \
  --config agent-config.json

# Get agent details
ab agents get 123e4567-e89b-12d3-a456-426614174000

# Update agent (create new version)
ab agents update 123e4567-e89b-12d3-a456-426614174000 \
  --config updated-config.json \
  --version-label "v2.0"

# Patch agent metadata
ab agents patch 123e4567-e89b-12d3-a456-426614174000 \
  --name "Updated Agent Name"

# Delete agent
ab agents delete 123e4567-e89b-12d3-a456-426614174000
```

### 9.2 Version Management

```bash
# List versions
ab versions list 123e4567-e89b-12d3-a456-426614174000

# Create new version
ab versions create 123e4567-e89b-12d3-a456-426614174000 \
  --config updated-config.json \
  --version-label "v2.0" \
  --notes "Updated prompts"

# Get latest version
ab versions get 123e4567-e89b-12d3-a456-426614174000 latest

# Get specific version
ab versions get 123e4567-e89b-12d3-a456-426614174000 VERSION_ID
```

---

*Document created: 2026-02-10*  
*Status: Complete*