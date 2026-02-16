# Spec 18: Interactive Mode Debugging and Fixes

## Problem Statement

The interactive mode (`ab invoke interactive`) has critical issues that make it unusable:

### Observed Symptoms
```bash
$ ab invoke interactive <agent-id> --verbose
You: what is 4*8
Agent                    # ← No response appears, just hangs
You: ^C                  # User has to interrupt
```

### Issues Preventing Diagnosis
1. **No response from agent** - Stream appears to produce no output
2. **Verbose mode provides no debugging info** - Cannot diagnose the problem
3. **Silent failures** - No error messages or warnings

## Root Cause Analysis

After code review of `ab_cli/cli/invoke.py::interactive()`, identified these issues:

### Issue 1: Verbose Parameter Never Used ❌
```python
# Line 372: Set but never referenced
verbose = global_verbose or verbose

# Rest of function: verbose is NEVER used for logging
# No request logging, no event logging, no debugging output
```

### Issue 2: Silent Event Dropping ❌
```python
for event in client.invoke_agent_stream(...):
    if event.event == "text" and event.data:
        # Handle text
    elif event.event == "error" and event.data:
        # Handle error
    # ALL OTHER EVENT TYPES ARE SILENTLY IGNORED
    # No logging to know what events are received
```

### Issue 3: No Request Visibility ❌
- Cannot see what request is sent to API
- Cannot verify message history structure
- Cannot debug request formation issues

### Issue 4: No Stream Debugging ❌
- Cannot see which events are received
- Cannot see event data (or lack thereof)
- Cannot identify why output doesn't appear

### Issue 5: Exception Handling Too Broad ❌
```python
except Exception as e:
    error_console.print(f"\n[red]Error:[/red] {e}")
    # No stack trace, even in verbose mode
    # Makes debugging nearly impossible
```

### Issue 6: No Empty Response Detection ❌
- If stream produces no text, user sees "Agent" with no explanation
- No warning or indication of what went wrong

## Solution: Comprehensive Verbose Debugging

### Phase 1: Add Verbose Logging (CRITICAL)

#### 1.1 Session Initialization Logging
```python
if verbose:
    console.print(f"\n[dim]═══ Interactive Session Debug Info ═══[/dim]")
    console.print(f"[dim]Agent ID: {agent_id}[/dim]")
    console.print(f"[dim]Version: {version_id}[/dim]")
    console.print(f"[dim]Agent Name: {agent.agent.name}[/dim]")
    if hxql_query:
        console.print(f"[dim]HXQL Query: {hxql_query}[/dim]")
    if hybrid_search:
        console.print(f"[dim]Hybrid Search: Enabled[/dim]")
    if deep_search:
        console.print(f"[dim]Deep Search: Enabled[/dim]")
    if guardrails:
        console.print(f"[dim]Guardrails: {', '.join(guardrails)}[/dim]")
    console.print(f"[dim]═══════════════════════════════════[/dim]\n")
```

#### 1.2 Request Logging (Per Message)
```python
if verbose:
    console.print(f"\n[dim]─── Sending Request ───[/dim]")
    console.print(f"[dim]Message count: {len(messages)}[/dim]")
    console.print(f"[dim]Latest message: {user_input[:50]}{'...' if len(user_input) > 50 else ''}[/dim]")
    console.print(f"[dim]Full request payload:[/dim]")
    console.print_json(request.model_dump_json())
```

#### 1.3 Stream Event Logging (Detailed)
```python
event_count = 0
for event in client.invoke_agent_stream(agent_id, version_id, request):
    event_count += 1
    
    if verbose:
        data_preview = ""
        if event.data:
            preview_len = min(len(event.data), 50)
            data_preview = f": {event.data[:preview_len]}{'...' if len(event.data) > preview_len else ''}"
        console.print(f"\n[dim]Event #{event_count}: {event.event} (length: {len(event.data) if event.data else 0}){data_preview}[/dim]")
    
    if event.event == "text" and event.data:
        console.print(event.data, end="")
        full_response += event.data
    elif event.event == "error" and event.data:
        console.print(f"\n[red]Error: {event.data}[/red]")
        if verbose:
            console.print(f"[dim]Error received after {event_count} events[/dim]")
        break
    else:
        # Log unhandled event types
        if verbose:
            console.print(f"[yellow]Unhandled event type: {event.event}[/yellow]")
```

#### 1.4 Response Summary
```python
console.print()  # New line after response

if verbose:
    console.print(f"[dim]─── Response Complete ───[/dim]")
    console.print(f"[dim]Total events received: {event_count}[/dim]")
    console.print(f"[dim]Response length: {len(full_response)} characters[/dim]")
    console.print(f"[dim]Messages in history: {len(messages)}[/dim]")

# Detect empty responses
if not full_response:
    if verbose:
        console.print(f"[yellow]⚠ Warning: Empty response received (no text events)[/yellow]")
    else:
        console.print(f"[yellow](No response)[/yellow]")
```

#### 1.5 Enhanced Exception Logging
```python
except APIError as e:
    error_console.print(f"\n[red]API Error:[/red] {e}")
    if verbose:
        import traceback
        error_console.print("\n[dim]Full traceback:[/dim]")
        error_console.print(traceback.format_exc())
except Exception as e:
    error_console.print(f"\n[red]Unexpected error:[/red] {e}")
    if verbose:
        import traceback
        error_console.print("\n[dim]Full traceback:[/dim]")
        error_console.print(traceback.format_exc())
```

### Phase 2: Status Indicators (MEDIUM)

#### 2.1 Waiting Indicator
```python
console.print("[bold cyan]Agent[/bold cyan] ", end="")
if not verbose:
    # Only show in non-verbose to avoid clutter
    console.print("[dim](thinking...)[/dim]", end="")
    sys.stdout.flush()
```

#### 2.2 Clear Waiting Indicator
```python
# After first event received
if event_count == 1 and not verbose:
    console.print("\r[bold cyan]Agent[/bold cyan] ", end="")  # Clear "thinking..."
```

### Phase 3: Enhanced Error Messages (LOW)

#### 3.1 Connection Issues
```python
except ConnectionError as e:
    error_console.print(f"\n[red]Connection Error:[/red] Unable to reach API")
    if verbose:
        error_console.print(f"[dim]Details: {e}[/dim]")
```

#### 3.2 Timeout Detection
```python
# Could add timeout warning if no events for N seconds
# Future enhancement
```

## Implementation Changes

### Files to Modify
1. `ab_cli/cli/invoke.py` - Update `interactive()` function

### Key Changes
- Add `event_count` variable to track stream events
- Add verbose logging at 5 key points (init, request, events, response, errors)
- Add empty response detection
- Import `traceback` for verbose error reporting
- Add status indicators for better UX

### Backward Compatibility
- ✅ No breaking changes
- ✅ Non-verbose mode stays clean
- ✅ Verbose mode adds comprehensive logging

## Testing Plan

### Test 1: Verbose Mode with Working Agent
```bash
ab --verbose invoke interactive <working-agent-id>
```
**Expected**: See all debug logs, request details, events, response

### Test 2: Verbose Mode with Broken Agent
```bash
ab --verbose invoke interactive <broken-agent-id>
```
**Expected**: See error details, stack trace, event logs showing failure point

### Test 3: Non-Verbose Mode
```bash
ab invoke interactive <agent-id>
```
**Expected**: Clean output, no debug logs, just "Agent (thinking...)" then response

### Test 4: Empty Response Scenario
If agent produces no output:
- **Verbose**: See all events, warning about empty response
- **Non-verbose**: See "(No response)" message

## Success Criteria

✅ User can diagnose issues using verbose mode  
✅ All stream events are visible in verbose mode  
✅ Request payload is logged in verbose mode  
✅ Exception stack traces appear in verbose mode  
✅ Empty responses are detected and reported  
✅ Non-verbose mode remains clean and user-friendly  
✅ All existing tests continue to pass

## Benefits

1. **Debuggability**: Users can now diagnose interactive mode issues
2. **Transparency**: See exactly what's being sent and received
3. **Better UX**: Status indicators improve user experience
4. **Maintainability**: Easier to debug reported issues
5. **No Breaking Changes**: Fully backward compatible