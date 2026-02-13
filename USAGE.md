# Agent Builder CLI Usage Guide

This document provides comprehensive documentation of all commands available in the Agent Builder CLI.

## Table of Contents

- [Configuration](#configuration)
- [Agent Management](#agent-management)
- [Version Management](#version-management)
- [Agent Invocation](#agent-invocation)
- [Resource Management](#resource-management)
- [Utility Commands](#utility-commands)
- [Output Formats](#output-formats)

## Configuration

The CLI requires configuration to connect to the Agent Builder API. Configuration can be provided through:

1. **Config File**: `config.yaml` or `ab-cli.yaml` in the current directory
2. **Environment Variables**: Prefixed with `AB_` (e.g., `AB_CLIENT_SECRET`)

### Config File Format

```yaml
# Agent Builder API Configuration
api_endpoint: https://api.example.com/
auth_endpoint: https://auth.example.com/oauth2/token
environment_id: your-environment-id
client_id: your-client-id
client_secret: your-client-secret
```

### Required Settings

| Setting | Environment Variable | Description |
|---------|---------------------|-------------|
| `environment_id` | `AB_ENVIRONMENT_ID` | HxP environment ID |
| `client_id` | `AB_CLIENT_ID` | OAuth2 client ID |
| `client_secret` | `AB_CLIENT_SECRET` | OAuth2 client secret |

### Validating Configuration

```bash
# Validate configuration file
ab validate

# Show loaded configuration values
ab validate --show-config
```

**Example Output:**

```
Validating: config.yaml

✅ Configuration is valid

Configuration values:
  API endpoint:     https://api.example.com/
  Auth endpoint:    https://auth.example.com/oauth2/token
  Environment ID:   your-environment-id
  Client ID:        your-cli...cret
  Client secret:    ********************
```

### Testing Connectivity

```bash
# Test API connectivity
ab check

# Test authentication only
ab check --auth-only
```

**Example Output:**

```
=== Agent Builder API Connectivity Check ===

Step 1/3: Loading configuration
  Config file: config.yaml
  ✓ Configuration loaded successfully

  Configuration Summary:
    API endpoint:     https://api.example.com/
    Auth endpoint:    https://auth.example.com/oauth2/token
    Environment ID:   your-environment-id
    Client ID:        your-cli...cret
    Client secret:    ********************

Step 2/3: Testing authentication
  Creating auth client...
    Token endpoint: https://auth.example.com/oauth2/token
  ✓ Auth client created
  Fetching OAuth2 token from auth server...
  ✓ Valid OAuth2 token received!

  Token Details:
    Token prefix:   eyJhbGciOiJIUzI1NiIs...
    Token length:   943 characters
    Request time:   0.756s

  Authentication: SUCCESS

Step 3/3: Testing API connectivity
  Creating Agent Builder API client...
    API endpoint:    https://api.example.com/
    Environment ID:  your-environment-id
  ✓ API client created

  Pinging Agent Builder API (GET /health)...
  ✓ API responded successfully!

  Health Check Response:
    Status: up
    Request time: 0.234s

  API Connectivity: SUCCESS

=== Check Complete ===
  Steps completed: 3/3

  All API endpoints are working correctly!
```

## Agent Management

### List Agents

```bash
# List all agents
ab agents list

# Paginate results
ab agents list --limit 10 --offset 20

# Get output in JSON format
ab agents list --format json
```

**Example Output (Table Format):**

```
                            Agents (35 total)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┓
┃ ID                              ┃ Name         ┃ Type ┃ Status  ┃ Created   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━┩
│ 8f6c2178-4f0a-43fb-88d7-f3d8... │ Calculator   │ tool │ CREATED │ 2026-02-… │
│ d9ce3525-0899-48b1-869f-ff9a... │ Document RAG │ rag  │ CREATED │ 2026-02-… │
│ 10238ef8-1882-430c-8cbb-3498... │ Insurance    │ task │ CREATED │ 2026-02-… │
└───────────────────────────────┴──────────────┴──────┴─────────┴───────────┘
```

**Example Output (JSON Format):**

```json
{
  "agents": [
    {
      "id": "8f6c2178-4f0a-43fb-88d7-f3d84c5e2e3b",
      "type": "tool",
      "name": "Calculator",
      "description": "Math assistant",
      "status": "CREATED",
      "isGlobalAgent": false,
      "currentVersionId": "3373b147-ef28-46a8-bc25-ebc9d573b3a6",
      "createdAt": "2026-02-10T15:59:12.346368+00:00",
      "createdBy": "cin-agent-platform-api-admin",
      "modifiedAt": "2026-02-10T15:59:12.369053+00:00",
      "modifiedBy": "cin-agent-platform-api-admin"
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "totalItems": 35,
    "hasMore": false
  }
}
```

### Get Agent

```bash
# Get agent details
ab agents get <agent-id>

# Get agent in JSON format
ab agents get <agent-id> --format json
```

**Example Output:**

```
Agent: Calculator
  ID: 8f6c2178-4f0a-43fb-88d7-f3d84c5e2e3b
  Type: tool
  Description: Math assistant
  Status: CREATED
  Created: 2026-02-10T15:59:12.346368+00:00
  Modified: 2026-02-10T15:59:12.369053+00:00

Current Version:
  Version ID: 3373b147-ef28-46a8-bc25-ebc9d573b3a6
  Number: 1
  Label: v1.0
  Notes: Initial version

Configuration:
{
  "tools": [
    {
      "toolType": "function",
      "name": "multiply",
      "description": "Multiplies two numbers",
      "funcName": "multiply",
      "parameters": {
        "type": "object",
        "properties": {
          "a": {
            "type": "number",
            "description": "First number to multiply"
          },
          "b": {
            "type": "number",
            "description": "Second number to multiply"
          }
        },
        "required": [
          "a",
          "b"
        ]
      }
    }
  ],
  "llmModelId": "anthropic.claude-3-haiku-20240307-v1:0",
  "systemPrompt": "You are a calculator assistant that can perform basic math operations."
}
```

### Create Agent

```bash
# Create a new agent
ab agents create \
  --name "Calculator" \
  --description "Math assistant" \
  --type tool \
  --agent-config agent-config.json \
  --version-label "v1.0" \
  --notes "Initial version"
```

**Example agent-config.json:**

```json
{
  "tools": [
    {
      "toolType": "function",
      "name": "multiply",
      "description": "Multiplies two numbers",
      "funcName": "multiply",
      "parameters": {
        "type": "object",
        "properties": {
          "a": {
            "type": "number",
            "description": "First number to multiply"
          },
          "b": {
            "type": "number",
            "description": "Second number to multiply"
          }
        },
        "required": [
          "a",
          "b"
        ]
      },
      "mcpServerReferences": []
    }
  ],
  "llmModelId": "anthropic.claude-3-haiku-20240307-v1:0",
  "systemPrompt": "You are a calculator assistant that can perform basic math operations.",
  "inferenceConfig": {
    "temperature": 0.0,
    "maxRetries": 10,
    "timeout": 3600,
    "maxTokens": 4000
  }
}
```

**Example Output:**

```
✓ Agent created successfully!
  ID: 8f6c2178-4f0a-43fb-88d7-f3d84c5e2e3b
  Name: Calculator
  Type: tool
  Version: 1
```

### Update Agent

```bash
# Update an agent (creates a new version)
ab agents update <agent-id> \
  --agent-config updated-config.json \
  --version-label "v2.0" \
  --notes "Improved version"
```

**Example Output:**

```
✓ Agent updated successfully!
  New Version: 2
  Label: v2.0
```

### Patch Agent

```bash
# Patch an agent's metadata (no new version)
ab agents patch <agent-id> \
  --name "New Name" \
  --description "Updated description"
```

**Example Output:**

```
✓ Agent patched successfully!
  Name: New Name
  Description: Updated description
```

### Delete Agent

```bash
# Delete an agent
ab agents delete <agent-id>

# Skip confirmation
ab agents delete <agent-id> --yes
```

**Example Output:**

```
Are you sure you want to delete agent 8f6c2178-4f0a-43fb-88d7-f3d84c5e2e3b? [y/N]: y
✓ Agent deleted: 8f6c2178-4f0a-43fb-88d7-f3d84c5e2e3b
```

### List Agent Types

```bash
# List available agent types
ab agents types
```

**Example Output:**

```
                                   Agent Types
┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Type ┃ Description                                                            ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ rag  │ RAG combines the power of retrieval-based systems with generative AI   │
│      │ models to provide accurate, context-aware responses.                   │
│ tool │ Tool Agents can perform operations using predefined tools. They can    │
│      │ produce structured JSON output and support multimodal inputs.          │
│ task │ Task Agents process structured inputs validated against JSON schemas   │
│      │ and use template variables in system prompts.                          │
└──────┴────────────────────────────────────────────────────────────────────────┘
```

## Version Management

### List Versions

```bash
# List versions of an agent
ab versions list <agent-id>

# Paginate results
ab versions list <agent-id> --limit 10 --offset 0
```

**Example Output:**

```
Agent: Calculator (ID: 8f6c2178-4f0a-43fb-88d7-f3d84c5e2e3b)

                               Versions (2 total)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Version ID                           ┃ Number ┃ Label ┃ Notes      ┃ Created  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩
│ 3373b147-ef28-46a8-bc25-ebc9d573b3a6 │ 1     │ v1.0  │ Initial    │ 2026-02  │
│ 9b24f825-7a19-4d2c-8e67-c12d2d8c6abc │ 2     │ v2.0  │ Improved   │ 2026-02  │
└──────────────────────────────────────┴───────┴───────┴────────────┴──────────┘
```

### Get Version

```bash
# Get a specific version
ab versions get <agent-id> <version-id>

# Get in JSON format
ab versions get <agent-id> <version-id> --format json
```

**Example Output:**

```
Agent: Calculator
  ID: 8f6c2178-4f0a-43fb-88d7-f3d84c5e2e3b
  Type: tool
  Description: Math assistant
  Status: CREATED

Version:
  Version ID: 3373b147-ef28-46a8-bc25-ebc9d573b3a6
  Number: 1
  Label: v1.0
  Notes: Initial version
  Created: 2026-02-10T15:59:12.353105+00:00

Configuration:
{
  "tools": [
    {
      "toolType": "function",
      "name": "multiply",
      "description": "Multiplies two numbers",
      "funcName": "multiply",
      "parameters": {
        "type": "object",
        "properties": {
          "a": { "type": "number", "description": "First number" },
          "b": { "type": "number", "description": "Second number" }
        },
        "required": ["a", "b"]
      }
    }
  ],
  "llmModelId": "anthropic.claude-3-haiku-20240307-v1:0",
  "systemPrompt": "You are a calculator assistant."
}
```

## Agent Invocation

The Agent Builder CLI supports several advanced features for agent invocation:

| Option | Description |
|--------|-------------|
| `--hxql-query` | HXQL query string for document retrieval |
| `--hybrid-search` | Enable hybrid search (combines semantic and keyword search) |
| `--deep-search` | Enable deep search for more thorough document analysis |
| `--guardrails` | Apply content moderation guardrails (can specify multiple) |

### Chat Invocation

```bash
# Chat with an agent
ab invoke chat <agent-id> --message "What is 5 * 7?"

# Chat with JSON output format
ab invoke chat <agent-id> --message "What is 5 * 7?" --format json

# Chat with streaming responses
ab invoke chat <agent-id> --message "What is 5 * 7?" --stream

# Use HXQL query for document retrieval
ab invoke chat <agent-id> --message "Summarize document ACME-001" --hxql-query "SELECT * FROM documents WHERE id='ACME-001'"

# Enable hybrid search for better document retrieval
ab invoke chat <agent-id> --message "What do we know about solar panels?" --hybrid-search

# Apply guardrails for content moderation
ab invoke chat <agent-id> --message "Tell me about cybersecurity" --guardrails "HAIP-Insults-Low" --guardrails "HAIP-Hate-High"

# Combine multiple options
ab invoke chat <agent-id> --message "Analyze our financial report" --hybrid-search --deep-search --guardrails "PII-Detection"
```

**Example Output:**

```
User: What is 5 * 7?

AI: 5 multiplied by 7 equals 35.

To calculate this:
5 × 7 = 35

Is there anything else you'd like me to calculate?
```

### Task Invocation

```bash
# Invoke a task agent
ab invoke task <agent-id> --input '{"key1": "value1", "key2": "value2"}'

# Invoke with JSON format output
ab invoke task <agent-id> --input '{"key1": "value1"}' --format json

# Invoke with input from file
ab invoke task <agent-id> --input-file input.json
```

### Interactive Mode

```bash
# Start interactive chat session
ab invoke interactive <agent-id>

# Interactive session with HXQL query
ab invoke interactive <agent-id> --hxql-query "SELECT * FROM documents WHERE category='financial'"

# Interactive session with hybrid search enabled
ab invoke interactive <agent-id> --hybrid-search

# Interactive session with guardrails
ab invoke interactive <agent-id> --guardrails "HAIP-Insults-Low" --guardrails "PII-Detection"
```

**Example Session:**

```
Starting interactive chat with Agent: Calculator
Type 'exit', 'quit', or Ctrl+C to end the session.

> What is 8 * 9?
8 multiplied by 9 equals 72.

> What about 15 / 3?
15 divided by 3 equals 5.

> exit
Ending chat session.
```

## Resource Management

### List LLM Models

```bash
# List all available LLM models
ab resources models

# Filter by agent type
ab resources models --agent-type rag

# Paginate results
ab resources models --limit 10 --offset 0

# Get JSON output
ab resources models --format json
```

**Example Output:**

```
                              LLM Models (10 total)                             
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ ID                         ┃ Name           ┃ Badge  ┃ Agent Types  ┃ Regions ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━╇━━━━━━━━━┩
│ anthropic.claude-3-haiku   │ Claude 3 Haiku │ Claude │ tool,rag,task│ us-east,│
│                            │                │        │              │ eu-west │
│ anthropic.claude-3-sonnet  │ Claude 3 Sonnet│ Claude │ tool,rag,task│ us-east,│
│                            │                │        │              │ eu-west │
└────────────────────────────┴────────────────┴────────┴──────────────┴─────────┘

Capabilities:
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┓
┃ Capability      ┃ Value    ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━━━┩
│ multimodal      │ True     │
│ streaming       │ True     │
│ function_calling│ True     │
└────────────────┴───────────┘
```

### List Guardrails

```bash
# List all available guardrails
ab resources guardrails

# Paginate results
ab resources guardrails --limit 10 --offset 0

# Get JSON output
ab resources guardrails --format json
```

**Example Output:**

```
                      Guardrails (8 total)                     
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name                              ┃ Description                ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ HAIP-Insults-Low                  │ Blocks strongly insulting  │
│                                   │ content                    │
│ HAIP-Hate-High                    │ Blocks extreme hate speech │
└───────────────────────────────────┴──────────────────────────┘
```

## Output Formats

All commands support multiple output formats using the `--format` or `-f` flag:

```bash
# Table format (default)
ab agents list

# JSON format
ab agents list --format json
# OR
ab agents list -f json

# YAML format
ab agents list --format yaml
# OR
ab agents list -f yaml
```

## Common Options

These options are available for most commands:

```bash
# Specify config file
ab --config custom-config.yaml agents list

# Enable verbose output
ab --verbose agents list

# Show help
ab --help
ab agents --help
ab agents create --help