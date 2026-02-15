# CLI Improvements

This spec outlines two key improvements to the CLI functionality:

## 1. Enhanced Agent Listing with Filtering

**Current State:**
Currently, the `ab agents list` command shows all agents with pagination options only. There's no built-in way to filter the results by type or name.

**Proposed Changes:**
Add filtering capabilities to the `ab agents list` command:
1. Add a new `--type` (or `-t`) option to filter agents by type (e.g., chat, tool, rag, task)
2. Add a new `--name` (or `-n`) option to filter agents by name pattern

**Implementation Details:**
- Update the `list_agents` function in `ab_cli/cli/agents.py` to add the new options
- For name filtering, support simple substring matching (e.g., "myagent" should match any agent with "myagent" in its name)
- The name filter should be case-insensitive for better usability
- Users should not need to write valid regular expressions - simple wildcard patterns like "*myagent*" should work intuitively
- Implement the filtering in the CLI layer (not in the API client), as this allows us to filter on the client-side without requiring API changes
- Apply filters after retrieving the full list from the API
- Update help text and documentation to reflect the new options

**Example Usage:**
```bash
# Filter by type
ab agents list --type rag

# Filter by name (simple substring match)
ab agents list --name "calculator"  # Will match "Simple Calculator", "Calculator Pro", etc.

# Filter by name with wildcard pattern
ab agents list --name "*calc*"  # Will match any name containing "calc"

# Combine filters
ab agents list --type tool --name "calculator"
```

## 2. Default Version for Agent Definitions

**Current State:**
Currently, when using `ab versions get`, users must explicitly specify "latest" as the version:
```bash
ab versions get 93b97837-8eb3-42cf-9516-c21f264a0d3c latest
```

**Proposed Changes:**
Make "latest" the default version when not explicitly provided:
1. Update the `get_version` command in `ab_cli/cli/versions.py` to make the version_id parameter optional
2. When version_id is not provided, automatically use "latest" 
3. Display a message to make this behavior explicit

**Implementation Details:**
- Modify the `get_version` function in `ab_cli/cli/versions.py` to make `version_id` an optional parameter
- Add logic to use "latest" as the default when not provided
- Add a notification message when "latest" is assumed, to make the behavior clear to users

**Example Usage:**
Current behavior (will be preserved):
```bash
ab versions get <agent-id> <version-id>
```

New behavior:
```bash
ab versions get <agent-id>
# Will automatically use "latest" and print a notification
```

## Testing Plan

1. Update existing tests to ensure compatibility with new options
2. Add new test cases for:
   - Filtering agents by type
   - Filtering agents by name pattern
   - Using the default "latest" version when not specified

## Documentation Updates

- Update the CLI help text for each affected command
- Update USAGE.md to document the new features