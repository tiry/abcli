# Specification 09: Invoke Command Enhancements

## Overview

This specification outlines enhancements to the Agent Builder CLI's invoke command, focusing on adding support for additional parameters available in the Agent Builder API.

## Problem Statement

The current implementation of the `invoke` command is missing support for several parameters that are available in the Agent Builder API:

1. No support for `hxqlQuery` parameter for document retrieval
2. No support for `hybridSearch` parameter to enable hybrid search
3. No support for `deepSearch` parameter for more thorough document analysis 
4. No support for `guardrails` parameter to apply content moderation

These limitations restrict users from leveraging the full capabilities of the Agent Builder API through the command line interface.

## Solution

To provide full support for the Agent Builder API, the invoke command will be enhanced to:

1. **Add New Parameters**:
   - `--hxql-query` option for document retrieval
   - `--hybrid-search` flag to enable hybrid search
   - `--deep-search` flag to enable deep search
   - `--guardrails` option (with multiple values) for content moderation

2. **Update Model Classes**:
   - Update `InvokeRequest` model to properly handle parameter name conversions
   - Add configuration for parameter aliasing

3. **Update Documentation**:
   - Document new parameters in `USAGE.md`
   - Provide examples for each parameter

## Implementation Details

### CLI Command Parameters

Update `ab_cli/cli/invoke.py` to add new options to both the `chat` and `interactive` commands:

```python
@invoke.command("chat")
@click.argument("agent_id")
@click.argument("version_id", required=False, default="latest")
@click.option("--message", "-m", help="Message to send")
@click.option("--message-file", type=click.Path(exists=True), help="Read message from file")
@click.option("--stream", "-s", is_flag=True, help="Enable streaming")
@click.option("--hxql-query", help="HXQL query for document retrieval")
@click.option("--hybrid-search", is_flag=True, help="Enable hybrid search")
@click.option("--deep-search", is_flag=True, help="Enable deep search")
@click.option("--guardrails", multiple=True, help="Apply guardrails (can be specified multiple times)")
# ... existing options
```

Update the function signature to include the new parameters:

```python
def chat(
    ctx: click.Context,
    agent_id: str,
    version_id: str,
    message: str | None,
    message_file: str | None,
    stream: bool,
    hxql_query: str | None,
    hybrid_search: bool,
    deep_search: bool,
    guardrails: list[str],
    output_format: str,
    verbose: bool,
) -> None:
```

Similarly, update the `interactive` command to support the same parameters.

### Model Updates

Update `ab_cli/models/invocation.py` to handle parameter name conversions with proper aliases:

```python
class InvokeRequest(BaseModel):
    """Request to invoke a chat agent."""

    messages: list[ChatMessage]
    temperature: float | None = None
    max_tokens: int | None = None

    # Additional fields from API spec
    hxql_query: str | None = Field(None, alias="hxqlQuery")
    hybrid_search: bool | None = Field(None, alias="hybridSearch")
    enable_deep_search: bool = Field(False, alias="enableDeepSearch")
    guardrails: list[str] | None = None

    class Config:
        populate_by_name = True
```

The `populate_by_name = True` configuration ensures that parameters can be provided using both snake_case (in Python) and camelCase (for API calls).

### Request Creation

Update the request creation in `invoke.py` to use camelCase parameter names required by the API:

```python
request = InvokeRequest(
    messages=messages,
    hxqlQuery=hxql_query,
    hybridSearch=hybrid_search,
    enableDeepSearch=deep_search,
    guardrails=list(guardrails) if guardrails else None
)
```

## Documentation Updates

The `USAGE.md` file has been updated to document the new parameters:

```markdown
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
# Use HXQL query for document retrieval
ab invoke chat <agent-id> --message "Summarize document ACME-001" --hxql-query "SELECT * FROM documents WHERE id='ACME-001'"

# Enable hybrid search for better document retrieval
ab invoke chat <agent-id> --message "What do we know about solar panels?" --hybrid-search

# Apply guardrails for content moderation
ab invoke chat <agent-id> --message "Tell me about cybersecurity" --guardrails "HAIP-Insults-Low" --guardrails "HAIP-Hate-High"

# Combine multiple options
ab invoke chat <agent-id> --message "Analyze our financial report" --hybrid-search --deep-search --guardrails "PII-Detection"
```

### Interactive Mode

```bash
# Interactive session with HXQL query
ab invoke interactive <agent-id> --hxql-query "SELECT * FROM documents WHERE category='financial'"

# Interactive session with hybrid search enabled
ab invoke interactive <agent-id> --hybrid-search

# Interactive session with guardrails
ab invoke interactive <agent-id> --guardrails "HAIP-Insults-Low" --guardrails "PII-Detection"
```
```

## Testing

The changes have been tested with:

1. **Linting**: All modified files have been checked with ruff and passed linting tests
2. **Type Checking**: All code has been verified with mypy to ensure proper type usage
3. **Unit Tests**: The existing test suite continues to pass with the new changes

### Type Checking Considerations

During development, type checking initially failed with errors like:

```
ab_cli/cli/invoke.py:146: error: Unexpected keyword argument "hxql_query" for "InvokeRequest"; did you mean "hxqlQuery"?
```

This was resolved by:
1. Adding the `populate_by_name = True` configuration to the model
2. Updating the code to use camelCase parameter names when creating request objects

## Backwards Compatibility

These changes are fully backwards compatible:

1. New CLI parameters are optional and do not break existing usage patterns
2. Default behavior remains the same when new parameters are not provided

## Future Work

Potential future improvements include:

1. Adding tests specifically for the new parameters
2. Supporting additional API parameters as they become available
3. Adding parameter validation to ensure proper values are provided
4. Providing an interactive wizard to help users build complex queries
5. Supporting query templates for common use cases

## Conclusion

These enhancements bring the Agent Builder CLI up to date with the latest API capabilities, allowing users to leverage advanced features like HXQL queries, hybrid search, and content guardrails directly from the command line interface.