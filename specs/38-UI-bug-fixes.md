# Spec 38: UI Bug Fixes

## Overview

Collection of bug fixes found during UI testing and usage.

## Bug 1: System Prompt Only Captures First Line

**Status:** ✅ Fixed

### Problem

When creating/editing an agent in the UI, the system prompt text area only captures the first line of multi-line input. The rest of the content is lost.

### Reproduction Steps

1. Navigate to Create/Edit Agent page
2. Enter multi-line system prompt:
   ```
   You are an Contract expert.
   Answer that you can get details on {{contract_id}}.
   If {{contract_id}} is not defined, then ask what contract the user wants to access to.
   ```
3. Submit the form
4. Check audit log - only first line is saved: `"You are a task assistant named TYContractAgent."`

### Root Cause

In `edit_agent.py` around line 118, the default prompt is generated dynamically **after** the text area widget is created:

```python
system_prompt = st.text_area("System Prompt", value=default_prompt, height=150)

# Later in code (line 118):
default_prompt = agent_config.get(
    "systemPrompt", f"You are a {agent_type} assistant named {name}."
)
```

The dynamic default is being generated using the **selected** `agent_type` and entered `name`, which overwrites the user's actual input from the text area.

### Solution

The `default_prompt` should be calculated **before** creating the text area widget, and should use the edit mode's existing prompt or a static default for create mode:

```python
# Calculate default prompt BEFORE the form
if agent_to_edit and agent_config:
    default_prompt = agent_config.get("systemPrompt", "")
else:
    # For new agents, use a simple default that user will replace
    default_prompt = "You are a helpful assistant."

# Inside form, create text area with the default
system_prompt = st.text_area("System Prompt", value=default_prompt, height=150)
```

### Files to Modify

- `ab_cli/abui/views/edit_agent.py`

### Implementation

- [x] Move default_prompt calculation before the form ✅
- [x] Use agent_config prompt if editing, simple default if creating ✅
- [x] Remove dynamic prompt generation inside form ✅
- [x] Linting checks pass ✅
- [ ] Test with multi-line prompts (Manual testing required)
- [ ] Verify edit mode preserves existing prompts (Manual testing required)
- [ ] Verify create mode allows custom prompts (Manual testing required)

### What Was Changed

**File:** `ab_cli/abui/views/edit_agent.py`

Moved the `default_prompt` calculation **before** the form starts, ensuring it uses the correct source:
- **Edit mode**: Uses existing `agent_config.get("systemPrompt", "")`
- **Create mode**: Uses simple static default `"You are a helpful assistant."`

This prevents the dynamic generation inside the form from overwriting user input with a calculated value based on form fields.

---

## Bug Tracking

| Bug # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 1 | System prompt only captures first line | ✅ Fixed | High |

---

## Testing Checklist

- [ ] Bug 1: Test multi-line system prompt in create mode
- [ ] Bug 1: Test multi-line system prompt in edit mode  
- [ ] Bug 1: Verify template variables {{var}} are preserved
- [ ] Bug 1: Check audit logs show full prompt

**Note:** Manual testing is needed to verify the fix works as expected.

---

## Bug 2: Edit Agent Fails After Chat - Wrong Object Type

**Status:** ✅ Fixed

### Problem

After chatting with an agent and clicking "Edit Agent", the application crashes with:

```
Error loading latest configuration: 'Agent' object has no attribute 'agent'
AttributeError: 'Agent' object has no attribute 'agent'
```

### Root Cause

The `agent_to_edit` session state variable can contain two different object types:
- **From Agents List**: `AgentVersion` object (has `.agent` and `.version` attributes)
- **From Chat View**: `Agent` object directly (no `.agent` attribute)

The code assumes it's always an `AgentVersion` object:
```python
default_name = agent_to_edit.agent.name if agent_to_edit else ""
```

### Solution

Need to handle both object types by checking which type we have:

```python
# Handle both Agent and AgentVersion objects
if agent_to_edit:
    if hasattr(agent_to_edit, 'agent'):
        # It's an AgentVersion object
        agent_obj = agent_to_edit.agent
        version_obj = agent_to_edit.version
    else:
        # It's an Agent object directly - fetch the version
        agent_obj = agent_to_edit
        # Need to fetch version separately
        version_obj = None  # Will be fetched
else:
    agent_obj = None
    version_obj = None

default_name = agent_obj.name if agent_obj else ""
```

### Files to Modify

- `ab_cli/abui/views/edit_agent.py`

### Implementation

- [x] Add type normalization at function start ✅
- [x] Handle Agent object by fetching AgentVersion ✅
- [x] Handle AgentVersion object (pass through) ✅
- [x] Linting checks pass ✅
- [ ] Test navigation from chat view (Manual testing required)
- [ ] Test navigation from agents list (Manual testing required)

### What Was Changed

**File:** `ab_cli/abui/views/edit_agent.py`

Added object type normalization at the beginning of the function:
- **Detects object type**: Checks if `agent_to_edit` has `.agent` attribute
- **Agent object**: Fetches full `AgentVersion` via `provider.get_agent(agent_id)`
- **AgentVersion object**: No conversion needed, passes through
- **Updates session state**: Stores normalized `AgentVersion` object

This ensures the rest of the function always works with `AgentVersion` objects regardless of navigation source.

---

## Bug Tracking

| Bug # | Description | Status | Priority |
|-------|-------------|--------|----------|
| 1 | System prompt only captures first line | ✅ Fixed | High |
| 2 | Edit Agent fails after chat - wrong object type | ✅ Fixed | High |
