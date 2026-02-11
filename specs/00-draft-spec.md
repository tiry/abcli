# Agent Builder CLI (ab-cli) - Draft Specification

## 1. Overview

### 1.1 Purpose

The Agent Builder CLI (`ab-cli`) is a command-line interface for interacting with the Agent Builder Platform API. It provides a convenient way to:

- **Manage Agents**: Create, list, update, and delete AI agents
- **Manage Versions**: Create new agent versions, list versions, retrieve version configurations
- **Invoke Agents**: Execute agents with messages or structured inputs
- **Validate Connectivity**: Test authentication and API connectivity

### 1.2 Design Principles

Following the patterns established in `ingest-cli`:

- **Click-based CLI** with command groups for intuitive navigation
- **Pydantic-based configuration** for type-safe settings management
- **OAuth2 client credentials** authentication (reusable pattern)
- **YAML configuration file** for persistent settings
- **Environment variable overrides** for sensitive values
- **httpx-based async HTTP client** for API communication
- **Comprehensive error handling** with retries for transient failures

---

## 2. Target API Endpoints

Based on the `agent-builder-platform` API structure:

### 2.1 Agent Management (`/v1/agents`)

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
| `POST` | `/v1/agents/lookup` | Lookup agent by name and version label |
| `POST` | `/v1/agents/versions/batch-get` | Batch get agent versions |

### 2.2 Agent Invocation (`/v1`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/agents/{agent_id}/versions/{version_id}/invoke` | Invoke agent (chat) |
| `POST` | `/v1/agents/{agent_id}/versions/{version_id}/invoke-stream` | Invoke agent with streaming |
| `POST` | `/v1/agents/{agent_id}/versions/{version_id}/invoke-task` | Invoke task agent |
| `POST` | `/v1/agents/{agent_id}/versions/{version_id}/invoke-task-stream` | Invoke task agent with streaming |

### 2.3 MCP Servers (Optional, feature-flagged)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/mcp-servers` | List MCP servers |
| `POST` | `/v1/mcp-servers` | Register MCP server |
| `DELETE` | `/v1/mcp-servers/{server_id}` | Delete MCP server |

---

## 3. Proposed CLI Structure

### 3.1 Main Entry Point

```
ab-cli [OPTIONS] COMMAND [ARGS]...

Options:
  -v, --verbose          Enable verbose output
  -c, --config PATH      Path to configuration file
  --version              Show version info
  --help                 Show help
```

### 3.2 Command Groups

#### `ab agents` - Agent Management
```
ab agents list [--limit N] [--offset N] [--global-only]
ab agents create --name NAME --type TYPE --description DESC --config CONFIG_FILE
ab agents get AGENT_ID
ab agents update AGENT_ID [--name NAME] [--description DESC]
ab agents delete AGENT_ID
ab agents lookup --name NAME [--version-label LABEL]
ab agents types
```

#### `ab versions` - Version Management
```
ab versions list AGENT_ID [--limit N] [--offset N]
ab versions create AGENT_ID --config CONFIG_FILE [--label LABEL] [--notes NOTES]
ab versions get AGENT_ID VERSION_ID
ab versions get AGENT_ID latest
```

#### `ab invoke` - Agent Invocation
```
ab invoke chat AGENT_ID [VERSION_ID] --message MESSAGE [--stream]
ab invoke chat AGENT_ID [VERSION_ID] --message-file PROMPT_FILE [--stream]
ab invoke task AGENT_ID [VERSION_ID] --input INPUT_FILE [--stream]
ab invoke interactive AGENT_ID [VERSION_ID]
```

#### `ab check` - API Connectivity Check
```
ab check [--auth-only] [--skip-invoke]
```

#### `ab validate` - Configuration Validation
```
ab validate [--config PATH] [--show-config]
```

### 3.3 Output Formats

Following CLI best practices:
- **Default**: Human-readable formatted output
- **`--json`**: JSON output for scripting/automation
- **`--quiet`**: Minimal output for scripts
- **`--verbose`**: Detailed operation logs

---

## 4. Configuration

### 4.1 Settings Model (`ABSettings`)

```python
class ABSettings(BaseSettings):
    """Agent Builder CLI configuration settings."""
    
    model_config = SettingsConfigDict(
        env_prefix="AB_",
        env_file=".env",
        extra="ignore",
    )
    
    # Required identifiers (HxP tenant info)
    environment_id: str
    account_id: str       # Optional, derived from environment
    
    # Authentication
    client_id: str
    client_secret: str
    
    # API Endpoints
    api_endpoint: str = "https://api.agentbuilder.experience.hyland.com/"
    auth_endpoint: str = "https://auth.hyland.com/connect/token"
    auth_scope: list[str] = ["hxp"]
    
    # Processing settings
    timeout: float = 30.0
    retry_backoff: float = 2.0
    max_retries: int = 3
    
    # Output preferences
    default_output_format: str = "table"  # table, json, yaml
```

### 4.2 Configuration File (`config.yaml`)

```yaml
# Agent Builder CLI Configuration

# HxP Environment
environment_id: "your-environment-id"

# Authentication (OAuth2 client credentials)
client_id: "your-client-id"
client_secret: "your-client-secret"  # Or use AB_CLIENT_SECRET env var

# API Endpoints
api_endpoint: "https://api.agentbuilder.dev.experience.hyland.com/"
auth_endpoint: "https://auth.iam.dev.experience.hyland.com/idp/connect/token"
auth_scope:
  - "hxp"

# Optional settings
timeout: 30.0
max_retries: 3
```

### 4.3 Environment Variable Override

Sensitive values can be overridden via environment variables:

| Environment Variable | Description |
|---------------------|-------------|
| `AB_CLIENT_ID` | OAuth2 client ID |
| `AB_CLIENT_SECRET` | OAuth2 client secret |
| `AB_ENVIRONMENT_ID` | Target environment ID |
| `AB_API_ENDPOINT` | API base URL |
| `AB_AUTH_ENDPOINT` | OAuth2 token endpoint |
| `AB_CONFIG` | Path to configuration file |
| `AB_VERBOSE` | Enable verbose logging |

---

## 5. Project Structure

```
ab-cli/
├── ab_cli/
│   ├── __init__.py
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py              # Main CLI entry point
│   │   ├── agents.py            # Agent management commands
│   │   ├── versions.py          # Version management commands
│   │   ├── invoke.py            # Agent invocation commands
│   │   └── output.py            # Output formatting utilities
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py              # OAuth2 authentication (reuse from ingest-cli)
│   │   ├── client.py            # Agent Builder API client
│   │   └── exceptions.py        # API exceptions
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py          # Pydantic settings model
│   │   ├── loader.py            # YAML config loader
│   │   └── exceptions.py        # Configuration exceptions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── agent.py             # Agent data models
│   │   ├── version.py           # Version data models
│   │   └── invocation.py        # Invocation request/response models
│   └── utils/
│       ├── __init__.py
│       ├── retry.py             # Retry utilities (reuse from ingest-cli)
│       └── logging.py           # Logging configuration
├── tests/
│   ├── __init__.py
│   ├── test_cli/
│   ├── test_api/
│   ├── test_config/
│   └── test_models/
├── specs/
│   └── 00-draft-spec.md         # This file
├── config.example.yaml
├── pyproject.toml
├── README.md
├── Usage.md
└── .gitignore
```

---

## 6. Implementation Plan

### Phase 1: Foundation
1. **Project Setup** - pyproject.toml, package structure, CI workflow
2. **Configuration** - Settings model, YAML loader, validation
3. **Authentication** - OAuth2 client (adapt from ingest-cli)
4. **Base API Client** - HTTP client with auth, error handling, retries

### Phase 2: Agent Management
5. **Agent Commands** - list, create, get, update, delete agents
6. **Version Commands** - list, create, get versions
7. **Output Formatting** - Table, JSON, YAML output

### Phase 3: Agent Invocation
8. **Chat Invocation** - invoke command with message input
9. **Task Invocation** - invoke-task with structured input
10. **Streaming Support** - Real-time streaming output

### Phase 4: Polish & Testing
11. **Check Command** - API connectivity verification
12. **Comprehensive Tests** - Unit and integration tests
13. **Documentation** - README, Usage guide, examples

---

## 7. Design Decisions (Confirmed)

### 7.1 Confirmed Choices

| Decision | Choice | Notes |
|----------|--------|-------|
| Command naming | Plural (`ab agents`) | Follows RESTful conventions |
| File-based message input | ✅ Yes | `--message-file prompt.txt` option |
| Config format | YAML | Reuse loader from ingest-cli |
| MCP Server support | ❌ Deferred | Skip in initial release |
| Batch operations | ❌ Deferred | Not priority for MVP |
| Interactive mode | ✅ Yes | REPL for conversations |

### 7.2 Reusable Components from ingest-cli

The following can be adapted/reused:
- `api/auth.py` - OAuth2 client credentials flow
- `utils/retry.py` - Retry decorator with exponential backoff
- `config/loader.py` - YAML configuration loading
- `config/exceptions.py` - Configuration error classes

---

## 8. Example Usage

### 8.1 Initial Setup

```bash
# Install
pip install ab-cli

# Create config (or copy from example)
cp config.example.yaml config.yaml
# Edit config.yaml with your credentials

# Verify connectivity
ab check
```

### 8.2 Managing Agents

```bash
# List all agents
ab agents list

# List agent types
ab agents types

# Create a new RAG agent
ab agents create \
  --name "My RAG Agent" \
  --type "rag" \
  --description "Knowledge assistant" \
  --config agent-config.json

# Get agent details
ab agents get 123e4567-e89b-12d3-a456-426614174000

# Update agent
ab agents update 123e4567-e89b-12d3-a456-426614174000 \
  --name "Updated Agent Name"

# Delete agent
ab agents delete 123e4567-e89b-12d3-a456-426614174000
```

### 8.3 Managing Versions

```bash
# List versions
ab versions list 123e4567-e89b-12d3-a456-426614174000

# Create new version
ab versions create 123e4567-e89b-12d3-a456-426614174000 \
  --config updated-config.json \
  --label "v2.0" \
  --notes "Updated prompts"

# Get latest version
ab versions get 123e4567-e89b-12d3-a456-426614174000 latest

# Get specific version
ab versions get 123e4567-e89b-12d3-a456-426614174000 VERSION_ID
```

### 8.4 Invoking Agents

```bash
# Simple chat invocation
ab invoke chat 123e4567-e89b-12d3-a456-426614174000 \
  --message "What is the capital of France?"

# Chat with streaming
ab invoke chat 123e4567-e89b-12d3-a456-426614174000 \
  --message "Write a poem about AI" \
  --stream

# Chat from file (for longer prompts)
ab invoke chat 123e4567-e89b-12d3-a456-426614174000 \
  --message-file prompt.txt \
  --stream

# Invoke specific version
ab invoke chat 123e4567-e89b-12d3-a456-426614174000 VERSION_ID \
  --message "Hello"

# Task agent invocation
ab invoke task 123e4567-e89b-12d3-a456-426614174000 \
  --input task-input.json

# With JSON output
ab invoke chat 123e4567-e89b-12d3-a456-426614174000 \
  --message "Hello" \
  --json
```

### 8.5 Interactive Mode (REPL)

```bash
# Start interactive session with an agent
ab invoke interactive 123e4567-e89b-12d3-a456-426614174000

# Session example:
# ╭─────────────────────────────────────────────────────╮
# │ Interactive session with: My RAG Agent              │
# │ Type 'exit' or 'quit' to end, 'clear' to reset     │
# ╰─────────────────────────────────────────────────────╯
#
# You: What products do we offer?
#
# Agent: Based on our knowledge base, we offer three main
# product lines:
# 1. Content Services Platform
# 2. Intelligent Document Processing
# 3. Business Process Automation
#
# You: Tell me more about IDP
#
# Agent: Intelligent Document Processing (IDP) is...
#
# You: exit
# Session ended.
```

### 8.6 Scripting Examples

```bash
# Export all agents as JSON
ab agents list --json > agents.json

# Create agent from script
AGENT_ID=$(ab agents create --name "My Agent" --type rag \
  --config config.json --json | jq -r '.id')
echo "Created agent: $AGENT_ID"

# Check API before running batch
ab check && ab invoke chat $AGENT_ID --message "Test"
```

---

## 9. Dependencies

```toml
[project]
dependencies = [
    "click>=8.1",
    "httpx>=0.27",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "pyyaml>=6.0",
    "rich>=13.0",  # For pretty output formatting
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "ruff>=0.5",
    "mypy>=1.10",
]
```

---

## 10. Next Steps

1. **Review this specification** and provide feedback on design decisions
2. **Clarify authentication details** - Confirm auth endpoint scopes for Agent Builder API
3. **Obtain OpenAPI spec** - For accurate model definitions
4. **Approve implementation plan** - Prioritize features for MVP

---

*Document created: 2026-02-09*
*Status: DRAFT - Awaiting user review*
