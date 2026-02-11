# Phase 4: Agent Invocation Improvements

## Summary

This phase focuses on improving the agent invocation functionality by enhancing response handling, adding verbose output mode, and fixing issues found during testing with real-world API interactions.

## Motivation

During testing with the actual Agent Builder API, we discovered that the API returns responses in various formats depending on the agent type and API version. Our initial implementation was too rigid and expected a specific response format, which caused errors when interacting with certain agent types. Additionally, users needed a way to see the raw API response for debugging purposes.

## Changes

### Response Model Enhancements

1. **Flexible Response Parsing**
   - Updated `InvokeResponse` model to handle multiple response formats:
     - Direct `response` field at the top level
     - Response nested within an `answer` field (either as a string or object)
     - Response in a `text` field

2. **Support for API-specific Fields**
   - Added support for additional fields returned by the API:
     - `createdAt` → `created_at`
     - `ragMode` → `rag_mode`
     - And other arbitrary fields through the use of a dynamic attribute access system

3. **Dynamic Field Access**
   - Implemented `__getattr__` method to allow access to extra fields not defined in the model
   - Store extra fields in a private `_extra_data` dictionary
   - This approach allows for forward compatibility with API changes

### CLI Improvements

1. **Verbose Output Mode**
   - Added `--verbose` / `-v` option to both `chat` and `task` commands
   - When enabled, displays the complete raw API response in JSON format
   - Useful for debugging and understanding the full API response structure

2. **Bug Fixes**
   - Fixed redundant API calls in task command implementation
   - Fixed streaming mode to properly handle special cases
   - Improved error handling and reporting

3. **Test Suite Improvements**
   - Enhanced model tests to verify handling of various response formats
   - Updated CLI tests for better isolation and maintainability

## Usage Examples

### Basic Agent Invocation

```bash
ab invoke chat <agent_id> -m "Hello"
```

### Verbose Output Mode

```bash
ab invoke chat <agent_id> -m "Hello" --verbose
```

### Task Invocation with Structured Input

```bash
ab invoke task <agent_id> --input input.json --verbose
```

### Interactive Mode

```bash
ab invoke interactive <agent_id>
```

## Implementation Notes

1. The response model now uses Pydantic's `populate_by_name=True` and `extra="allow"` config to maximize compatibility.
2. Dynamic attribute access through `__getattr__` enables forward compatibility with API changes.
3. The verbose output mode uses Rich's JSON formatting capabilities for readable display of complex nested structures.

## Next Steps

1. **More Comprehensive Response Type Support**
   - Support additional response formats that might appear in future API versions
   - Add specific handling for specialized agent types (e.g., RAG, function calling)

2. **Response Post-Processing**
   - Add options to format or transform responses (e.g., Markdown rendering)
   - Implement filtering of responses based on content types

3. **Session Management**
   - Add support for saving and loading conversation sessions
   - Implement history management for interactive mode

4. **Client-side Caching**
   - Implement caching of agent responses to reduce API calls
   - Add local storage of conversation history

These improvements will continue to enhance the flexibility and utility of the Agent Builder CLI, making it more robust when interacting with different agent types and API versions.