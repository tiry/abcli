# Specification 24: OpenAPI 1.1 Migration

## Overview

This specification outlines the changes required to support the new RAG (Retrieval Augmented Generation) parameters introduced in OpenAPI specification v1.1. The new API version adds enhanced retrieval configuration options for fine-grained control over RAG agent behavior.

**Note**: Some endpoints appear to be temporarily unavailable in v1.1 (MCP servers, permissions, file uploads), but these are expected to return. We will NOT remove any related code.

## Problem Statement

The Agent Builder CLI was built against OpenAPI specification v1.0 (`specs/openapi.json`). Version v1.1 (`specs/openapi_1.1.json`) introduces new RAG configuration parameters that provide enhanced control over document retrieval and processing.

Key objectives:
1. Add support for new RAG configuration parameters in agent invocation
2. Expose these parameters through CLI commands
3. Update the UI agent detail view to support these parameters
4. Maintain full backwards compatibility

## Analysis of Changes

### 1. New RAG Configuration Parameters

The API v1.1 introduces several new parameters for enhanced RAG (Retrieval Augmented Generation) control:

#### Added to `AgentConfig` Schema:
```json
{
  "adjacentEmbeddingRange": {
    "type": "integer",
    "description": "Number of adjacent embedding chunks to fetch in each direction around each result. Falls back to app config if not specified."
  },
  "adjacentEmbeddingMerge": {
    "type": "boolean", 
    "description": "When true, merge adjacent chunk text into the parent chunk instead of separate nodes. Falls back to app config if not specified."
  },
  "rerankerEnabled": {
    "type": "boolean",
    "description": "Enable/disable the reranker post-processing step. Falls back to app config if not specified."
  },
  "rerankerTopN": {
    "type": "integer",
    "description": "Number of top results to keep after reranking. Falls back to app config if not specified."
  }
}
```

#### Added to `ChatRequestBaseSchema` (Invocation):
The same four parameters plus one additional:
```json
{
  "adjacentEmbeddingRange": {...},
  "adjacentEmbeddingMerge": {...},
  "limit": {
    "type": "integer",
    "description": "Maximum number of embedding chunks to retrieve. Falls back to config default if not specified."
  },
  "rerankerEnabled": {...},
  "rerankerTopN": {...}
}
```

**Impact**: These parameters enable fine-grained control over RAG retrieval behavior. They should be:
1. Added to the `InvokeRequest` model in `ab_cli/models/invocation.py`
2. Exposed as CLI options in `ab_cli/cli/invoke.py` for both `chat` and `interactive` commands
3. Documented in `USAGE.md`

### 2. Additional Changes (Informational Only)

#### AgentModel Status Field
- **v1.0**: `status` field had a default value of `"CREATED"`
- **v1.1**: `status` field is required without a default

**Impact**: The `Agent` model in `ab_cli/models/agent.py` should be updated to reflect that status is always present.

#### Agent Deletion Behavior
- **v1.0**: "Delete an agent and corresponding versions and permissions"
- **v1.1**: "Soft delete a agent and log the delete action for the current tenant"

**Impact**: This is primarily a documentation change. The deletion is now explicitly "soft delete" meaning agents may be marked as deleted rather than permanently removed. CLI behavior should remain the same from user perspective.

#### MessageModel Content Validation
- **v1.0**: Highly structured with discriminated unions for `InputTextContent`, `InputImageContent`, `InputDocumentContent`
- **v1.1**: Simplified to generic object array: `items: { additionalProperties: true, type: "object" }`

**Impact**: The message validation is now more permissive. The CLI's `ChatMessage` model should remain flexible to handle various content types.

#### Stream Response Documentation
- **v1.0**: Basic response documentation
- **v1.1**: Explicit status codes documented (200, 500, 503) with content types

**Impact**: Better error handling can be implemented for streaming responses.

### 3. Note on Temporarily Unavailable Endpoints

Some endpoints appear to be absent from v1.1 but are expected to return in future releases:
- MCP Server management endpoints
- Agent permissions endpoints
- File upload endpoints

**Action**: We will NOT remove any existing code or models related to these features. They remain in the codebase for when the endpoints are restored.

## Implementation Plan

### Phase 1: Model Updates

1. **Update `invocation.py`**: Add new RAG parameters to `InvokeRequest`
   ```python
   class InvokeRequest(BaseModel):
       """Request to invoke a chat agent."""
       
       messages: list[ChatMessage]
       hxql_query: str | None = Field(None, alias="hxqlQuery")
       hybrid_search: bool | None = Field(None, alias="hybridSearch")
       enable_deep_search: bool = Field(False, alias="enableDeepSearch")
       guardrails: list[str] | None = None
       
       # New RAG configuration parameters
       adjacent_embedding_range: int | None = Field(None, alias="adjacentEmbeddingRange")
       adjacent_embedding_merge: bool | None = Field(None, alias="adjacentEmbeddingMerge")
       limit: int | None = None
       reranker_enabled: bool | None = Field(None, alias="rerankerEnabled")
       reranker_top_n: int | None = Field(None, alias="rerankerTopN")
   ```

### Phase 2: CLI Command Updates

1. **Update `invoke.py`**: Add new CLI options for RAG parameters
   ```python
   @invoke.command("chat")
   @click.argument("agent_id")
   @click.argument("version_id", required=False, default="latest")
   @click.option("--message", "-m", help="Message to send")
   # ... existing options ...
   @click.option("--hxql-query", help="HXQL query for document retrieval")
   @click.option("--hybrid-search", is_flag=True, help="Enable hybrid search")
   @click.option("--deep-search", is_flag=True, help="Enable deep search")
   @click.option("--guardrails", multiple=True, help="Apply guardrails")
   # NEW OPTIONS:
   @click.option("--adjacent-range", type=int, help="Number of adjacent chunks to fetch")
   @click.option("--adjacent-merge", is_flag=True, help="Merge adjacent chunks")
   @click.option("--limit", "-l", type=int, help="Maximum chunks to retrieve")
   @click.option("--reranker", is_flag=True, help="Enable reranker")
   @click.option("--reranker-top-n", type=int, help="Top N results after reranking")
   ```

2. **Update request creation**: Pass new parameters to `InvokeRequest`
   ```python
   request = InvokeRequest(
       messages=messages,
       hxqlQuery=hxql_query,
       hybridSearch=hybrid_search,
       enableDeepSearch=deep_search,
       guardrails=list(guardrails) if guardrails else None,
       adjacentEmbeddingRange=adjacent_range,
       adjacentEmbeddingMerge=adjacent_merge,
       limit=limit,
       rerankerEnabled=reranker,
       rerankerTopN=reranker_top_n,
   )
   ```

3. **Update `interactive` command**: Apply same parameter additions

### Phase 3: UI Updates (ab_cli/abui/)

1. **Update agent detail view** (`ab_cli/abui/views/agent_details.py`):
   - Display new RAG parameters if present in agent configuration
   - Add explanatory tooltips for each parameter

2. **Update agent edit view** (`ab_cli/abui/views/edit_agent.py`):
   - Add input fields for new RAG parameters
   - Provide validation and help text
   - Make fields optional with proper defaults

3. **Update chat view** (`ab_cli/abui/views/chat.py`):
   - Add advanced options section for RAG parameters
   - Allow users to override agent-level settings per invocation

### Phase 4: Documentation Updates

1. **Update `USAGE.md`**: Document new RAG parameters
   ```markdown
   ### Advanced RAG Configuration
   
   For RAG agents, you can fine-tune the retrieval behavior:
   
   | Option | Description |
   |--------|-------------|
   | `--adjacent-range` | Number of adjacent embedding chunks to fetch around each result |
   | `--adjacent-merge` | Merge adjacent chunks into parent chunk instead of separate nodes |
   | `--limit` | Maximum number of embedding chunks to retrieve |
   | `--reranker` | Enable reranker post-processing step |
   | `--reranker-top-n` | Number of top results to keep after reranking |
   
   Example:
   ```bash
   ab invoke chat <agent-id> \
     --message "Find relevant documents" \
     --adjacent-range 2 \
     --adjacent-merge \
     --limit 10 \
     --reranker \
     --reranker-top-n 5
   ```
   ```

2. **Update `README.md`**: Update version references if needed

3. **Create migration notes**: Document any breaking changes for users

### Phase 5: Testing

1. **Update existing tests**: Ensure all tests pass with model changes

2. **Add new tests**: 
   - Test new RAG parameters in `tests/test_cli/test_invoke.py`
   - Test parameter serialization in `tests/test_models/test_invocation.py`
   - Test API client with new parameters in `tests/test_api/test_client.py`

3. **Integration tests**: Test against API v1.1 if available

### Phase 6: Backwards Compatibility

Since the new parameters are all optional (they fall back to config defaults), the changes are backwards compatible:

1. Existing CLI commands continue to work without new parameters
2. New parameters enhance functionality without breaking existing usage
3. Removed features (MCP servers, permissions, file uploads) were not implemented in CLI

## File Checklist

Files that need to be modified:

**Core Functionality:**
- [ ] `ab_cli/models/invocation.py` - Add new RAG parameters to InvokeRequest
- [ ] `ab_cli/cli/invoke.py` - Add CLI options for new RAG parameters (chat command)
- [ ] `ab_cli/cli/invoke.py` - Add CLI options for new RAG parameters (interactive command)
- [ ] `ab_cli/cli/invoke.py` - Update request creation to include new parameters

**UI Updates:**
- [ ] `ab_cli/abui/views/agent_details.py` - Display new RAG parameters
- [ ] `ab_cli/abui/views/edit_agent.py` - Add input fields for new RAG parameters
- [ ] `ab_cli/abui/views/chat.py` - Add advanced RAG options

**Documentation:**
- [ ] `USAGE.md` - Document new RAG parameters with examples
- [ ] `UI.md` - Document new UI fields for RAG parameters (if applicable)

**Testing:**
- [ ] `tests/test_models/test_invocation.py` - Add tests for new parameters
- [ ] `tests/test_cli/test_invoke.py` - Add tests for new CLI options
- [ ] `tests/test_abui/` - Add/update UI tests for new RAG parameters

## Implementation Strategy

**Recommended Approach: Incremental Addition**
1. Phase 1: Add new parameters to models (backwards compatible)
2. Phase 2: Expose parameters in CLI commands
3. Phase 3: Update UI views to support parameters
4. Phase 4: Update documentation
5. Phase 5: Add comprehensive tests
6. Phase 6: Validate with integration tests

## Risks and Mitigation

**Risk**: New parameters conflict with existing options
- **Mitigation**: Use descriptive names that don't clash with existing options

**Risk**: Breaking changes affect existing users
- **Mitigation**: All new parameters are optional; existing commands work unchanged

**Risk**: UI complexity increases
- **Mitigation**: Group advanced RAG options in collapsible/advanced sections

**Risk**: Test coverage gaps
- **Mitigation**: Add comprehensive tests for new parameters before deployment

## Success Criteria

1. ✅ All new RAG parameters are exposed via CLI
2. ✅ Existing CLI commands continue to work without changes
3. ✅ Documentation is complete and accurate
4. ✅ Test coverage includes new parameters
5. ✅ Type checking passes (mypy)
6. ✅ Linting passes (ruff)
7. ✅ All tests pass (pytest)

## Future Considerations

1. **API Versioning**: Consider adding explicit API version selection in configuration
2. **Advanced RAG Presets**: Create preset configurations for common use cases
3. **RAG Parameter Validation**: Add validation to ensure parameter combinations are valid
4. **Performance Monitoring**: Track impact of different RAG parameter settings

## References

- Original API spec: `specs/openapi.json` (v1.0)
- New API spec: `specs/openapi_1.1.json` (v1.1)
- Related specs:
  - Spec 09: Invoke Command Enhancements
  - Spec 05: Resource Listing
  - Spec 19: List and Pagination

## Conclusion

The OpenAPI v1.1 enhancement is purely additive from the CLI perspective. The main work involves:

1. **Adding 5 new RAG configuration parameters** to invocation commands and UI
2. **Exposing parameters** through CLI options and UI controls
3. **Enhanced documentation** for the new capabilities
4. **No breaking changes** - fully backwards compatible
5. **No code removal** - preserving code for temporarily unavailable endpoints

This maintains the CLI's principle of providing full access to API capabilities while ensuring backwards compatibility and ease of use.
