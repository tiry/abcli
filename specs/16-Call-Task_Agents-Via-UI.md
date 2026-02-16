# Spec 16: Fix Task Agent Invocation in UI

## Problem Statement

The UI chat/invoke view has two critical bugs when working with task agents:

1. **Missing Agent Details**: When navigating directly from the agent listing to the chat/invoke view, agent details (including inputSchema) are not loaded, causing errors
2. **Wrong CLI Command**: Task agents are being invoked using `ab invoke chat` instead of `ab invoke task`, which fails with a validation error

## Current Behavior

### Issue 1: Agent Details Not Loaded

**Navigation Path That Fails:**
```
Agent Listing → 💬 Chat button → Chat View
```
- Error: `inputSchema not defined`
- The inputSchema is needed to render the JSON input form for task agents

**Navigation Path That Works:**
```
Agent Listing → 👁️ View button → Agent Details → Chat → Chat View
```
- Works because Agent Details view loads full agent configuration into session state

### Issue 2: Wrong CLI Command

When invoking a task agent, the UI calls:
```bash
ab --verbose invoke chat 10238ef8-... --message '{"claim_id": "01", ...}' --format json
```

This fails with:
```
Error: Validation error: Agent type task not supported in /invoke or /invoke-stream endpoints.
```

**Should call:**
```bash
ab invoke task 10238ef8-... --task '{"claim_id": "01", ...}' --format json
```

## Root Causes

### 1. Missing On-Demand Loading in Chat View

File: `ab_cli/abui/views/chat.py`

The chat view assumes agent details are already loaded in `st.session_state` but doesn't load them if missing. It only checks basic agent info from the listing.

### 2. Hardcoded Chat Command

File: `ab_cli/abui/providers/cli_data_provider.py`

The `invoke_agent` method always uses `invoke chat` regardless of agent type:

```python
def invoke_agent(self, agent_id: str, message: str) -> dict:
    # Always uses "chat" - BUG!
    command = [
        "ab", "--verbose", "invoke", "chat", agent_id,
        "--message", message,
        "--format", "json"
    ]
```

## Proposed Solution

### 1. Load Agent Details On-Demand in Task Interface

**File:** `ab_cli/abui/views/chat.py`

The `show_task_agent_interface()` function needs to load full agent details if `agent_config` is missing:

```python
def show_task_agent_interface(agent: dict[str, Any]) -> None:
    """Show the task interface for task agents."""
    agent_id = agent["id"]
    st.subheader(f"Task Agent: {agent['name']}")

    # Check if agent has full configuration loaded
    agent_config = agent.get("agent_config", {})
    
    # If agent_config is missing or empty, load full agent details
    if not agent_config:
        config = st.session_state.get("config", {})
        data_provider = get_data_provider(config)
        
        try:
            with st.spinner("Loading agent configuration..."):
                full_agent = data_provider.get_agent(agent_id)
                if full_agent and "agent_config" in full_agent:
                    # Update session state with full agent details
                    st.session_state.selected_agent = full_agent
                    agent = full_agent
                    agent_config = full_agent.get("agent_config", {})
                else:
                    st.error("Failed to load agent configuration")
                    return
        except Exception as e:
            st.error(f"Error loading agent details: {e}")
            return
    
    input_schema = agent_config.get("inputSchema", {})
    
    if not input_schema:
        st.warning("This task agent doesn't have an input schema defined.")
        return
    
    # Continue with task input editor...
```

### 2. Use Agent Type to Determine CLI Command

**File:** `ab_cli/abui/providers/cli_data_provider.py`

Update the `invoke_agent` method signature and implementation:

```python
def invoke_agent(self, agent_id: str, message: str, agent_type: str = "chat") -> str:
    """Invoke an agent with a message.

    Args:
        agent_id: The ID of the agent to invoke
        message: The message to send (for chat) or task data JSON (for task)
        agent_type: Type of agent ("chat", "rag", "tool", "task")

    Returns:
        Agent response as text
    """
    try:
        # Quote the message to handle special characters
        quoted_message = shlex.quote(message)

        # Build command based on agent type
        if agent_type == "task":
            # Use invoke task with --task parameter
            cmd = ["invoke", "task", agent_id, "--task", quoted_message, "--format", "json"]
        else:
            # Use invoke chat with --message parameter (for chat, rag, tool)
            cmd = ["invoke", "chat", agent_id, "--message", quoted_message, "--format", "json"]

        result = self._run_command(cmd, use_cache=False)
        
        # Extract response from result...
        # (rest of response extraction logic remains the same)
```

### 3. Update Chat and Task Views to Pass Agent Type

**File:** `ab_cli/abui/views/chat.py`

Update both `show_chat_agent_interface()` and `show_task_agent_interface()`:

```python
def show_chat_agent_interface(agent: dict[str, Any]) -> None:
    """Show the chat interface for chat and RAG agents."""
    # ... existing code ...
    
    if user_message:
        # ... existing code ...
        try:
            agent_type = agent.get("type", "chat")
            response = data_provider.invoke_agent(
                agent_id, 
                user_message,
                agent_type=agent_type
            )
            # ... rest of code ...

def show_task_agent_interface(agent: dict[str, Any]) -> None:
    """Show the task interface for task agents."""
    # ... existing code ...
    
    if st.button("Submit Task"):
        if task_input:
            # ... existing code ...
            try:
                agent_type = agent.get("type", "task")
                response = data_provider.invoke_agent(
                    agent_id,
                    json.dumps(task_input),
                    agent_type=agent_type
                )
                # ... rest of code ...
```

## Implementation Plan

### Phase 1: Load Agent Details On-Demand

1. **Update `show_chat_page()` function**
   - Check if full agent details are loaded
   - Load from data provider if missing
   - Display loading spinner during fetch
   - Handle errors gracefully

2. **Ensure agent_to_view is synchronized**
   - When loading details, update both `agent_to_view` and `selected_agent`
   - This ensures consistency across the UI

### Phase 2: Fix CLI Command Generation

1. **Update `CLIDataProvider.invoke_agent()`**
   - Add `agent_type` parameter
   - Build command based on agent type
   - Use `--task` for task agents, `--message` for others

2. **Update method signature in `DataProvider` base class**
   - Add optional `agent_type` parameter with default value
   - Update MockDataProvider to match signature

3. **Update chat view invocation calls**
   - Extract agent type from agent data
   - Pass agent type to `invoke_agent` method

### Phase 3: Testing

1. **Manual Testing**
   - Test direct navigation: Listing → Chat (for both chat and task agents)
   - Test via details: Listing → Details → Chat
   - Verify task agents invoke correctly
   - Verify chat agents still work

2. **Unit Tests** (if time permits)
   - Test agent details loading logic
   - Test CLI command generation for different agent types

## Files to Modify

1. **`ab_cli/abui/views/chat.py`**
   - Add on-demand agent details loading
   - Pass agent type to invoke_agent

2. **`ab_cli/abui/providers/data_provider.py`**
   - Update base class method signature

3. **`ab_cli/abui/providers/cli_data_provider.py`**
   - Implement agent-type-aware command generation
   - Update invoke_agent method

4. **`ab_cli/abui/providers/mock_data_provider.py`**
   - Update method signature to match base class

## Expected Behavior After Fix

### Task Agent Invocation

```
User navigates: Agent Listing → 💬 Chat button (task agent)
1. Chat view opens
2. System loads agent details in background
3. Input schema displays correctly
4. User enters: {"claim_id": "01", "policy_number": "POL001"}
5. System calls: ab invoke task <id> --task '{"claim_id": "01", ...}' --format json
6. Response displays successfully
```

### Chat Agent Invocation

```
User navigates: Agent Listing → 💬 Chat button (chat agent)
1. Chat view opens
2. System loads agent details in background (if needed)
3. Chat interface displays
4. User enters: "Hello"
5. System calls: ab invoke chat <id> --message "Hello" --format json
6. Response displays successfully
```

## Benefits

1. **Consistent UX**: Both navigation paths work identically
2. **Correct API Usage**: Task agents use correct endpoint
3. **Better Performance**: On-demand loading only when needed
4. **Error Prevention**: No more inputSchema errors
5. **Type Safety**: Agent type determines invocation method

## Success Criteria

- [ ] Can navigate directly from listing to chat view for task agents
- [ ] Task agents invoke successfully using `invoke task` command
- [ ] Chat agents continue to work with `invoke chat` command
- [ ] Input schema displays correctly for task agents in all navigation paths
- [ ] No errors about undefined inputSchema
- [ ] Verbose mode shows correct CLI commands being executed