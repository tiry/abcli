# Specification 26: UI Navigation and JSON Viewers

## Overview

This specification documents improvements to the Agent Builder UI for better navigation between views and enhanced data visibility through JSON viewers. These features improve user experience by providing quick navigation and full transparency into agent configurations and API responses.

## Related Specifications

- Spec 13: UI-Chat (original chat implementation)
- Spec 25: Enhanced Chat Response Display with RAG Source Citations

## Features Implemented

### 1. View/Edit Navigation Buttons in Chat Interface

**File**: `ab_cli/abui/views/chat.py`

**Feature**: Added quick navigation buttons in the chat interface header to access agent details and edit views without returning to the main agents list.

**Implementation**:
```python
# Header with back button and View/Edit buttons
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    if st.button("← Back to Agent Selection"):
        st.session_state.selected_agent = None
        st.rerun()

with col2:
    if st.button("👁️ View Agent"):
        st.session_state.agent_to_view = agent
        st.session_state.current_page = "AgentDetails"
        st.rerun()

with col3:
    if st.button("✏️ Edit Agent"):
        st.session_state.agent_to_edit = agent
        st.session_state.current_page = "EditAgent"
        st.rerun()
```

**User Benefits**:
- Quick access to agent details while chatting
- Direct path to edit agent configuration
- Streamlined workflow - no need to navigate back to agents list

**Session State Variables Used**:
- `agent_to_view`: Stores the agent object for the details view
- `agent_to_edit`: Stores the agent object for the edit view
- `current_page`: Controls app-level navigation (values: "AgentDetails", "EditAgent")

### 2. JSON Viewer in Agent Details

**File**: `ab_cli/abui/views/agent_details.py`

**Feature**: Added a "📄 JSON" button in the agent details header that toggles display of the complete agent JSON structure.

**Implementation**:
```python
# Header includes JSON button
title_col, json_col, action_col1, action_col2 = st.columns([3, 1, 1, 1])

with json_col:
    if st.button("📄 JSON", use_container_width=True):
        if "show_agent_json" not in st.session_state:
            st.session_state.show_agent_json = False
        st.session_state.show_agent_json = not st.session_state.show_agent_json
        st.rerun()

# Display JSON if toggled
if st.session_state.get("show_agent_json", False):
    st.markdown("---")
    st.markdown("### Full Agent JSON")
    st.json(agent_to_view)
    st.markdown("---")
```

**User Benefits**:
- Full visibility into agent configuration
- Useful for debugging and understanding agent structure
- Easy copy/paste of agent configuration
- Toggle on/off to avoid clutter

**Session State Variables Used**:
- `show_agent_json`: Boolean flag controlling JSON visibility

### 3. JSON Viewer for Chat Responses

**File**: `ab_cli/abui/views/chat.py`

**Feature**: Added "📄 View Full JSON" button for each assistant response in the chat, displaying the complete API response with all metadata.

**Implementation**:

**A. Store Full Response in Chat History**:
```python
# Store full response structure including complete API response
chat_history.append({
    "role": "assistant",
    "content": response_data.get("response_text", ""),
    "metadata": {
        "model": response_data.get("model"),
        "source_nodes": response_data.get("source_nodes", []),
        "rag_mode": response_data.get("rag_mode"),
        "created_at": response_data.get("created_at"),
    },
    "full_response": response_data  # Complete API response
})
```

**B. Display JSON Button for Each Message**:
```python
# In display_chat_history function
for idx, message in enumerate(chat_history):
    # ... display message content ...
    
    # Add JSON button if full response is available
    if full_response:
        json_key = f"show_json_{idx}"
        if json_key not in st.session_state:
            st.session_state[json_key] = False
        
        if st.button("📄 View Full JSON", key=f"json_btn_{idx}", type="secondary"):
            st.session_state[json_key] = not st.session_state[json_key]
            st.rerun()
        
        # Show JSON if toggled
        if st.session_state[json_key]:
            st.json(full_response)
```

**User Benefits**:
- Full transparency into API responses
- Debug agent behavior by seeing complete response structure
- Verify source nodes, metadata, and model information
- Independent toggle for each message in chat history

**Session State Variables Used**:
- `show_json_{idx}`: Boolean flags controlling JSON visibility per message (indexed)

### 4. Visual "Thinking" Indicator

**File**: `ab_cli/abui/views/chat.py`

**Feature**: Added visual feedback while agent processes requests.

**Implementation**:
```python
with st.chat_message("assistant"):
    with st.spinner("🤔 Agent is thinking..."):
        # Get response from agent
        response_data = data_provider.invoke_agent(...)
```

**User Benefits**:
- Clear feedback that system is processing
- Improved perceived responsiveness
- Better user experience

## Modified Files Summary

1. **ab_cli/abui/views/chat.py**
   - Added View/Edit navigation buttons in header
   - Added "thinking" indicator with spinner
   - Store full API response in chat history
   - Added JSON viewer button for each assistant message
   - Modified `display_chat_history()` to handle JSON display

2. **ab_cli/abui/views/agent_details.py**
   - Added JSON button to header
   - Added JSON display section with toggle

## Testing

### Manual Testing Checklist

**Chat Navigation**:
- [ ] Chat interface shows View and Edit buttons
- [ ] View button navigates to agent details page
- [ ] Edit button navigates to agent edit page
- [ ] Back button returns to agent selection
- [ ] Navigation preserves agent context

**Agent Details JSON Viewer**:
- [ ] JSON button appears in agent details header
- [ ] Clicking JSON button shows full agent JSON
- [ ] Clicking again hides JSON
- [ ] JSON is properly formatted and readable

**Chat Response JSON Viewer**:
- [ ] "View Full JSON" button appears for each assistant response
- [ ] Button click toggles JSON display for that specific message
- [ ] Multiple messages can have JSON visible simultaneously
- [ ] JSON displays complete API response with all fields

**Thinking Indicator**:
- [ ] Spinner appears when sending message
- [ ] Shows "🤔 Agent is thinking..." text
- [ ] Disappears when response is received

### Automated Testing

No new automated tests required - these are UI-only changes that rely on Streamlit's session state management and don't affect core business logic.

## User Experience Flow

### Scenario 1: Quick Navigation While Chatting
1. User is chatting with an agent
2. User wants to check agent configuration
3. User clicks "👁️ View Agent"
4. Agent details page opens
5. User can click JSON button to see full configuration
6. User returns to chat or edits agent

### Scenario 2: Debugging Agent Response
1. User receives response from RAG agent
2. Response seems incorrect
3. User clicks "📄 View Full JSON" on response
4. User reviews source_nodes to see which documents were used
5. User checks metadata for model and RAG mode
6. User identifies issue (e.g., wrong documents retrieved)

### Scenario 3: Copying Agent Configuration
1. User navigates to agent details
2. User clicks "📄 JSON" button
3. Full agent JSON is displayed
4. User selects and copies JSON
5. User can paste into documentation or share with team

## Success Criteria

✅ **All Implemented Successfully**:
1. View/Edit buttons functional in chat interface
2. JSON button toggles agent JSON in details view
3. JSON viewer shows complete API responses in chat
4. Thinking indicator displays during agent processing
5. All navigation flows work correctly
6. Session state properly manages UI toggles
7. No errors in console or UI

## Future Enhancements

Potential future improvements (not in scope):

1. **FR-Future-1**: Download JSON button to save responses to file
2. **FR-Future-2**: Copy to clipboard button for JSON content
3. **FR-Future-3**: JSON diff view to compare responses
4. **FR-Future-4**: Syntax highlighting for JSON display
5. **FR-Future-5**: Collapsible sections within large JSON objects

## Notes

- All features use Streamlit's native components and session state
- JSON display uses `st.json()` which provides built-in formatting
- Navigation leverages existing app.py routing logic
- Changes are backward compatible with existing chat history
- No database or API changes required

## References

- Streamlit session state documentation
- Spec 13: UI-Chat (base chat implementation)
- Spec 25: Enhanced Chat Response Display
- UI.md: Agent Builder UI documentation
