# Resource Listing for Agent Builder CLI

This specification describes the implementation of resource listing capabilities in the Agent Builder CLI, specifically for listing LLM models and guardrails.

## Overview

Agent Builder agents depend on various resources such as LLM models and guardrails. The CLI now provides commands to list these resources to help users:

1. Discover which LLM models are available for different agent types
2. View model capabilities and metadata 
3. See which guardrails are available for content moderation

## API Endpoints

The CLI uses the following API endpoints:

- **GET /v1/models** - List supported LLM models
- **GET /v1/guardrails** - List supported guardrails

## Data Models

### LLM Models

```python
class DeprecationStatus(CamelModel):
    """Deprecation status for LLM models."""
    
    deprecated: bool = False
    deprecation_date: str = ""
    replacement_model_name: str = ""


class LLMModel(CamelModel):
    """LLM model information."""
    
    id: str
    name: str
    description: str
    badge: str
    metadata: str
    agent_types: list[str]
    capabilities: dict
    regions: list[str]
    deprecation_status: DeprecationStatus = Field(default_factory=DeprecationStatus)


class LLMModelList(CamelModel):
    """List of LLM models with pagination."""
    
    models: list[LLMModel]
    pagination: Pagination
```

### Guardrails

```python
class GuardrailModel(CamelModel):
    """Guardrail information."""
    
    name: str
    description: str = ""


class GuardrailList(CamelModel):
    """List of guardrails with pagination."""
    
    guardrails: list[GuardrailModel]
    pagination: Pagination
```

## CLI Commands

### List Models

```
ab resources models [OPTIONS]
```

Options:
- `--agent-type`, `-t`: Filter by agent type (tool, rag, task)
- `--limit`, `-l`: Maximum number of models to return (default: 50)
- `--offset`, `-o`: Offset for pagination (default: 0)
- `--format`, `-f`: Output format (table, json, yaml; default: table)

Example:
```bash
# List all models
ab resources models

# List models for RAG agents
ab resources models --agent-type rag

# Get full details in JSON format
ab resources models --format json
```

### List Guardrails

```
ab resources guardrails [OPTIONS]
```

Options:
- `--limit`, `-l`: Maximum number of guardrails to return (default: 50)
- `--offset`, `-o`: Offset for pagination (default: 0)
- `--format`, `-f`: Output format (table, json, yaml; default: table)

Example:
```bash
# List all guardrails
ab resources guardrails

# Get full details in JSON format
ab resources guardrails --format json
```

## Implementation Details

1. Added model classes in `ab_cli/models/resources.py`
2. Added API client methods in `ab_cli/api/client.py`:
   - `list_models()`
   - `list_guardrails()`
3. Created CLI commands in `ab_cli/cli/resources.py`
4. Registered command group in `ab_cli/cli/main.py`

## Output Format

For table output (default), the CLI provides:

### Models Table
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

### Guardrails Table
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

For JSON/YAML output, complete model data is provided including all fields.