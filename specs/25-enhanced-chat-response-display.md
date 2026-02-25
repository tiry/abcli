# Specification 25: Enhanced Chat Response Display with RAG Source Citations

## Overview

This specification defines enhancements to the chat interface to properly display agent responses with full context, including RAG source citations. Currently, the UI only shows the response text, but the API provides rich metadata including source documents, scores, and RAG mode information that should be displayed to users.

## Current State

### Critical Issues
1. **WRONG TEXT DISPLAYED**: Chat shows source chunk text instead of actual agent response! Screenshot shows "## 7.1.7 Notice and Scheduling\n\n *" which is from a source chunk, not the response
2. **Response Parsing Bug**: `invoke_agent()` method not correctly extracting the "response" field
3. **No Source Citations**: RAG agents return source documents (`sourceNodes`) but these are not displayed
4. **No Markdown Rendering**: Response text with Markdown formatting is displayed as plain text
5. **Lost Metadata**: `custom_outputs`, `usage`, `model`, `rag_mode` fields are stripped and discarded

### Current Flow
```
CLI Command → Full JSON Response → invoke_agent() strips to text → Chat displays text only
```

### Example Full Response (from CLI)
```json
{
  "response": "Hello! I'm HR Portal Agent...",
  "created_at": 1771976121,
  "model": "us.mistral.pixtral-large-2502-v1:0",
  "output": [
    {
      "type": "message",
      "status": "completed",
      "content": [
        {
          "type": "output_text",
          "text": "Response text with **Markdown** formatting..."
        }
      ],
      "role": "assistant"
    }
  ],
  "custom_outputs": {
    "sourceNodes": [
      {
        "docId": "d6fcc7f2-9e4f-4c21-b840-d890f799cfd3__2045b5dd-e089-4494-b187-267533bf55e2",
        "chunkId": "9e4cd378-c138-3953-915f-1a08d37bd502",
        "score": 0.5984379,
        "text": "# UNLIMITED PTO FAQS\n **REQUESTING UNLIMITED PTO**..."
      }
    ],
    "ragMode": "normal"
  }
}
```

## Requirements

### 1. Return Full Response Structure

**FR-1.1**: Modify `cli_data_provider.invoke_agent()` to return structured response object instead of plain text string

**FR-1.2**: Response object structure:
```python
{
    "response_text": str,           # Main response text
    "model": str | None,             # Model used
    "created_at": int | None,        # Unix timestamp
    "source_nodes": list[dict],      # RAG source citations
    "rag_mode": str | None,          # RAG mode (normal, hybrid, etc.)
    "usage": dict | None,            # Token usage info
    "finish_reason": str | None,     # Completion reason
    "metadata": dict | None          # Additional metadata
}
```

**FR-1.3**: Return error structure if parsing fails with clear error message

### 2. Enhanced Chat Message Display

**FR-2.1**: Display response text with Markdown rendering using `st.markdown()` instead of `st.write()`

**FR-2.2**: Support common Markdown features:
- Headers (`#`, `##`, `###`)
- Bold (`**text**`)
- Italic (`*text*`)
- Lists (`*`, `-`, numbered)
- Code blocks (` ``` `)
- Links

**FR-2.3**: Preserve existing JSON display for task agent responses

### 3. Source Citations Display

**FR-3.1**: Display source citations in an expandable section below each assistant message

**FR-3.2**: Source citation section header:
- Title: "📚 Sources" or "📄 Referenced Documents"
- Badge showing count: "3 sources" 
- Default state: Collapsed (expandable)

**FR-3.3**: Each source node displays:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source 1 (Score: 0.598)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📄 Document ID: d6fcc7f2-9e4f-4c21-b840...
🔖 Chunk ID: 9e4cd378-c138-3953-915f...

Content:
# UNLIMITED PTO FAQS
**REQUESTING UNLIMITED PTO**...
```

**FR-3.4**: Sort source nodes by score (highest first)

**FR-3.5**: Display chunk text with Markdown formatting

**FR-3.6**: Truncate long document IDs with tooltip on hover showing full ID

### 4. Metadata Display

**FR-4.1**: Display model and timestamp information in a compact format below response:
```
Model: us.mistral.pixtral-large-2502-v1:0 | RAG Mode: normal | Time: 2026-02-24 18:08:41
```

**FR-4.2**: Display in muted/secondary text style

**FR-4.3**: Only show metadata fields that are available (handle None values gracefully)

### 5. Chat History Storage

**FR-5.1**: Update chat history storage to preserve full response structure:
```python
{
    "role": "assistant",
    "content": "Response text...",
    "metadata": {
        "model": "...",
        "source_nodes": [...],
        "rag_mode": "...",
        "created_at": 123456789
    }
}
```

**FR-5.2**: Maintain backward compatibility with existing chat history (text-only messages)

## Implementation Plan

### Phase 1: Data Provider Enhancement

**File**: `ab_cli/abui/providers/cli_data_provider.py`

1. Modify `invoke_agent()` method:
   - Return dict with structured response instead of string
   - Extract `response` field for text
   - Extract `custom_outputs.sourceNodes` array
   - Extract `model`, `rag_mode`, `created_at`, `usage` fields
   - Handle missing fields gracefully

2. Add helper method `_parse_invoke_response()`:
   - Parse full JSON response
   - Structure data into standard format
   - Handle edge cases (missing fields, different formats)

### Phase 2: Chat Display Enhancement

**File**: `ab_cli/abui/views/chat.py`

1. Update `display_chat_history()` function:
   - Check if message has metadata
   - Use `st.markdown()` for response text
   - Add source citations display
   - Add metadata display

2. Add new function `display_source_citations()`:
   - Create expandable section
   - Loop through source nodes
   - Format each source with dividers
   - Display docId, chunkId, score, text

3. Add new function `display_message_metadata()`:
   - Format model, timestamp, RAG mode
   - Display in compact format

4. Update message storage in `show_chat_agent_interface()`:
   - Store full response structure
   - Preserve metadata in chat history

### Phase 3: Testing

**File**: `tests/test_abui/test_chat_view.py`

1. Test response parsing:
   - Full response with all fields
   - Minimal response (text only)
   - Missing fields handling

2. Test source citation display:
   - Multiple sources
   - No sources (non-RAG agents)
   - Source ordering by score

3. Test Markdown rendering:
   - Headers, bold, italic
   - Lists and code blocks
   - Links

4. Test backward compatibility:
   - Old chat history format
   - Text-only responses

## Files to Modify

1. `ab_cli/abui/providers/cli_data_provider.py` - Return structured response
2. `ab_cli/abui/providers/data_provider.py` - Update interface signature
3. `ab_cli/abui/providers/mock_data_provider.py` - Match new interface
4. `ab_cli/abui/views/chat.py` - Enhanced display logic
5. `tests/test_abui/test_chat_view.py` - Add comprehensive tests

## Example UI Output

```
┌─────────────────────────────────────────────────────┐
│ 👤 User                                              │
│ How can I request PTO?                               │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 🤖 Assistant                                         │
│                                                      │
│ To request PTO, you must request it in advance by   │
│ using **Time Off Request Form** in UltiPro Time and │
│ Attendance.                                          │
│                                                      │
│ **Requirements:**                                    │
│ • One week advance notice for 2 days or less        │
│ • One month advance notice for 5+ days              │
│                                                      │
│ ▼ 📚 Sources (10 documents)                         │
│   ┌─────────────────────────────────────────────┐  │
│   │ Source 1 (Score: 0.598)                      │  │
│   │ 📄 Doc: d6fcc7f2...2045b5dd                  │  │
│   │ 🔖 Chunk: 9e4cd378...d37bd502                │  │
│   │                                              │  │
│   │ # UNLIMITED PTO FAQS                         │  │
│   │ **REQUESTING UNLIMITED PTO**                 │  │
│   │ HOW DO I REQUEST TIME OFF?...                │  │
│   └─────────────────────────────────────────────┘  │
│                                                      │
│ Model: us.mistral.pixtral-large-2502-v1:0           │
│ RAG Mode: normal | 2026-02-24 18:08:41              │
└─────────────────────────────────────────────────────┘
```

## Success Criteria

1. ✅ Response text displays with Markdown formatting
2. ✅ Source citations visible for RAG agents
3. ✅ All source metadata displayed (docId, chunkId, score, text)
4. ✅ Sources sorted by relevance score
5. ✅ Model and timestamp information shown
6. ✅ Backward compatible with existing chat history
7. ✅ No errors for non-RAG agents (no sources)
8. ✅ All tests passing
9. ✅ User can expand/collapse source citations
10. ✅ Chunk text rendered with Markdown

## Notes

- This enhancement significantly improves transparency for RAG-based agents
- Users can verify which documents were used to generate responses
- Supports debugging and trust-building in AI responses
- Foundation for future "View Document" feature (FR-3.7 - future)

## References

- Spec 13: UI-Chat (original chat implementation)
- Spec 24: OpenAPI 1.1 Migration (RAG parameters)
- CLI invoke response structure (see example above)
