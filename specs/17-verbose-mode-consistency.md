
# Spec 17: Verbose Mode Consistency

## Problem Statement

The verbose mode can be defined at various levels and we have inconsistencies:

### Expected Behavior
Both command-level and global-level verbose should work:

```bash
# Both of these should show verbose output including raw API response:
ab --verbose invoke chat <agent-id> -m "hello"
ab invoke chat <agent-id> -m "hello" --verbose
```

### Actual Behavior (Before Fix)
- `ab invoke chat <agent-id> -m "hello" --verbose` ✅ Works - shows raw API response
- `ab --verbose invoke chat <agent-id> -m "hello"` ❌ Does NOT show raw API response

### Root Cause
Subcommands (`invoke chat`, `invoke task`) defined their own `--verbose` option that shadowed the global one. The commands only checked their local `verbose` parameter, not the parent context's global `verbose`.

## Solution: Hierarchical Verbose Mode (Option A)

### Approach
Implement hierarchical verbose combining global and command-level flags with OR logic:
- Keep both global and command-level `--verbose` options
- Combine with OR logic: `effective_verbose = global_verbose OR command_verbose`
- Backward compatible - existing usage patterns continue to work
- Flexible - users can set verbose at any level

### Implementation

**Files Modified:**
1. `ab_cli/cli/invoke.py` - Updated `chat()` and `task()` commands

**Changes:**
```python
def chat(..., verbose: bool) -> None:
    # Combine global and command-level verbose (hierarchical)
    global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False
    verbose = global_verbose or verbose
    # ... rest of function
```

### Testing
- All 24 invoke-related tests pass
- Backward compatible - command-level `--verbose` still works
- Global `--verbose` now properly propagates to subcommands

## Usage Examples

All of these now work correctly:

```bash
# Global verbose (affects all commands)
ab --verbose invoke chat <agent-id> -m "hello"

# Command-level verbose
ab invoke chat <agent-id> -m "hello" --verbose

# Both combined (redundant but works)
ab --verbose invoke chat <agent-id> -m "hello" --verbose

# Task agents also support hierarchical verbose
ab --verbose invoke task <agent-id> -t '{"query": "test"}'
ab invoke task <agent-id> -t '{"query": "test"}' --verbose
```

## Benefits
1. **Consistency**: Verbose works at both global and command level
2. **Flexibility**: Users can choose their preferred level of granularity
3. **Backward Compatible**: No breaking changes to existing usage
4. **Future-proof**: Pattern can be extended to other commands if needed


