
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
1. `ab_cli/cli/invoke.py` - Updated `chat()`, `task()`, and `interactive()` commands

**Changes:**
```python
def chat(..., verbose: bool) -> None:
    # Combine global and command-level verbose (hierarchical)
    global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False
    verbose = global_verbose or verbose
    # ... rest of function

def task(..., verbose: bool) -> None:
    # Combine global and command-level verbose (hierarchical)
    global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False
    verbose = global_verbose or verbose
    # ... rest of function

def interactive(..., verbose: bool) -> None:
    # Combine global and command-level verbose (hierarchical)
    global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False
    verbose = global_verbose or verbose
    # ... rest of function
```

### Testing
- ✅ All 15 invoke tests pass (chat, task, interactive)
- ✅ All linting and type checks pass
- ✅ Backward compatible - command-level `--verbose` still works
- ✅ Global `--verbose` now properly propagates to all subcommands

## Usage Examples

All of these now work correctly:

```bash
# Chat command - Global verbose
ab --verbose invoke chat <agent-id> -m "hello"

# Chat command - Command-level verbose
ab invoke chat <agent-id> -m "hello" --verbose

# Task command - Global verbose
ab --verbose invoke task <agent-id> -t '{"query": "test"}'

# Task command - Command-level verbose
ab invoke task <agent-id> -t '{"query": "test"}' --verbose

# Interactive command - Global verbose (NEW!)
ab --verbose invoke interactive <agent-id>

# Interactive command - Command-level verbose (NEW!)
ab invoke interactive <agent-id> --verbose

# Both combined (redundant but works)
ab --verbose invoke chat <agent-id> -m "hello" --verbose
```

## Benefits
1. **Consistency**: Verbose works at both global and command level
2. **Flexibility**: Users can choose their preferred level of granularity
3. **Backward Compatible**: No breaking changes to existing usage
4. **Future-proof**: Pattern can be extended to other commands if needed


