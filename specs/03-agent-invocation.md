# Phase 3: Agent Invocation

**Status:** Draft - Awaiting user review  
**Spec Reference:** `specs/00-draft-spec.md`  
**Previous Phase:** Phase 2 - Agent Management (Complete, 62 tests passing)

---

## 1. Overview

This phase implements agent invocation commands, allowing users to interact with agents through chat messages, structured task inputs, and an interactive REPL mode.

### 1.1 Goals

- Implement `ab invoke chat` for chat-style invocations
- Implement `ab invoke task` for structured task inputs
- Support streaming responses with `--stream` flag
- Implement interactive REPL mode (`ab invoke interactive`)
- Create invocation models for request/response handling

---

## 2. API Endpoints

Based on the Agent Builder API OpenAPI spec:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/agents/{agent_id}/versions/{version_id}/invoke` | Invoke agent (chat) |
| `POST` | `/v1/agents/{agent_id}/versions/{version_id}/invoke-stream` | Invoke with streaming |
| `POST` | `/v1/agents/{agent_id}/versions/{version_id}/invoke-task` | Invoke task agent |
| `POST` | `/v1/agents/{agent_id}/versions/{version_id}/invoke-task-stream` | Invoke task with streaming |

---

## 3. CLI Commands

### 3.1 `ab invoke chat`

Invoke an agent with a chat message.

```bash
# Basic invocation (uses 'latest' version)
ab invoke chat AGENT_ID --message "What is the capital of France?"

# With specific version
ab invoke chat AGENT_ID VERSION_ID --message "Hello"

# With streaming
ab invoke chat AGENT_ID --message "Write a poem about AI" --stream

# From file (for longer prompts)
ab invoke chat AGENT_ID --message-file prompt.txt

# JSON output
ab invoke chat AGENT_ID --message "Hello" --json
```

**Options:**
- `--message, -m TEXT` - The message to send
- `--message-file PATH` - Read message from file
- `--stream, -s` - Enable streaming response
- `--json` - Output in JSON format

### 3.2 `ab invoke task`

Invoke a task agent with structured input.

```bash
# Basic task invocation
ab invoke task AGENT_ID --input task-input.json

# With specific version
ab invoke task AGENT_ID VERSION_ID --input task-input.json

# With streaming
ab invoke task AGENT_ID --input task-input.json --stream
```

**Options:**
- `--input, -i PATH` - JSON file with structured input
- `--stream, -s` - Enable streaming response
- `--json` - Output in JSON format

### 3.3 `ab invoke interactive`

Start an interactive chat session (REPL).

```bash
ab invoke interactive AGENT_ID [VERSION_ID]
```

**Session Commands:**
- Type messages to chat
- `exit` or `quit` - End session
- `clear` - Clear conversation history
- `Ctrl+C` - Interrupt streaming

---

## 4. Data Models

### 4.1 `ab_cli/models/invocation.py`

```python
"""Invocation request and response models."""

from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime
from uuid import UUID

class ChatMessage(BaseModel):
    """A chat message."""
    role: str  # "user" | "assistant" | "system"
    content: str

class InvokeRequest(BaseModel):
    """Request to invoke a chat agent."""
    messages: list[ChatMessage]
    # Optional inference parameters
    temperature: float | None = None
    max_tokens: int | None = None

class InvokeTaskRequest(BaseModel):
    """Request to invoke a task agent."""
    inputs: dict[str, Any]
    # Optional inference parameters
    temperature: float | None = None
    max_tokens: int | None = None

class InvokeResponse(BaseModel):
    """Response from agent invocation."""
    response: str
    finish_reason: str | None = None
    usage: dict[str, int] | None = None  # token counts
    metadata: dict[str, Any] | None = None

class StreamEvent(BaseModel):
    """A streaming event from agent invocation."""
    event: str  # "text" | "error" | "done"
    data: str | None = None

class ConversationState(BaseModel):
    """State for interactive conversation."""
    agent_id: UUID
    version_id: UUID | None = None
    messages: list[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
```

---

## 5. API Client Methods

### 5.1 Add to `ab_cli/api/client.py`

```python
def invoke_agent(
    self,
    agent_id: str | UUID,
    version_id: str | UUID,
    request: InvokeRequest,
) -> InvokeResponse:
    """Invoke an agent with chat messages.
    
    Args:
        agent_id: The agent ID.
        version_id: The version ID (or 'latest').
        request: The invocation request.
    
    Returns:
        The agent's response.
    """
    data = self._request(
        "POST",
        f"/agents/{agent_id}/versions/{version_id}/invoke",
        json=request.model_dump(exclude_none=True),
    )
    return InvokeResponse.model_validate(data)

def invoke_agent_stream(
    self,
    agent_id: str | UUID,
    version_id: str | UUID,
    request: InvokeRequest,
) -> Generator[StreamEvent, None, None]:
    """Invoke an agent with streaming response.
    
    Args:
        agent_id: The agent ID.
        version_id: The version ID (or 'latest').
        request: The invocation request.
    
    Yields:
        Stream events as they arrive.
    """
    # Implementation uses httpx streaming

def invoke_task(
    self,
    agent_id: str | UUID,
    version_id: str | UUID,
    request: InvokeTaskRequest,
) -> InvokeResponse:
    """Invoke a task agent with structured input.
    
    Args:
        agent_id: The agent ID.
        version_id: The version ID (or 'latest').
        request: The task invocation request.
    
    Returns:
        The agent's response.
    """
    data = self._request(
        "POST",
        f"/agents/{agent_id}/versions/{version_id}/invoke-task",
        json=request.model_dump(exclude_none=True),
    )
    return InvokeResponse.model_validate(data)

def invoke_task_stream(
    self,
    agent_id: str | UUID,
    version_id: str | UUID,
    request: InvokeTaskRequest,
) -> Generator[StreamEvent, None, None]:
    """Invoke a task agent with streaming response."""
    # Implementation uses httpx streaming
```

---

## 6. CLI Implementation

### 6.1 `ab_cli/cli/invoke.py`

```python
"""Agent invocation CLI commands."""

import json
from pathlib import Path
from uuid import UUID

import click
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel

from ab_cli.api.client import AgentBuilderClient
from ab_cli.config import load_config
from ab_cli.models.invocation import (
    ChatMessage,
    InvokeRequest,
    InvokeTaskRequest,
)

console = Console()

@click.group()
def invoke():
    """Invoke agents (chat, task, interactive)."""
    pass

@invoke.command("chat")
@click.argument("agent_id")
@click.argument("version_id", required=False, default="latest")
@click.option("--message", "-m", help="Message to send")
@click.option("--message-file", type=click.Path(exists=True), help="Read message from file")
@click.option("--stream", "-s", is_flag=True, help="Enable streaming")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def chat(ctx, agent_id, version_id, message, message_file, stream, as_json):
    """Invoke agent with a chat message."""
    # Implementation here

@invoke.command("task") 
@click.argument("agent_id")
@click.argument("version_id", required=False, default="latest")
@click.option("--input", "-i", "input_file", required=True, type=click.Path(exists=True))
@click.option("--stream", "-s", is_flag=True, help="Enable streaming")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.pass_context
def task(ctx, agent_id, version_id, input_file, stream, as_json):
    """Invoke task agent with structured input."""
    # Implementation here

@invoke.command("interactive")
@click.argument("agent_id")
@click.argument("version_id", required=False, default="latest")
@click.pass_context
def interactive(ctx, agent_id, version_id):
    """Start interactive chat session (REPL)."""
    # Implementation here
```

---

## 7. Streaming Implementation

### 7.1 SSE (Server-Sent Events) Handling

```python
def invoke_agent_stream(
    self,
    agent_id: str | UUID,
    version_id: str | UUID,
    request: InvokeRequest,
) -> Generator[StreamEvent, None, None]:
    """Invoke agent with streaming response."""
    url = f"{self.base_url}/agents/{agent_id}/versions/{version_id}/invoke-stream"
    
    with self._get_client().stream(
        "POST",
        url,
        json=request.model_dump(exclude_none=True),
        headers=self._get_headers(),
    ) as response:
        for line in response.iter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                yield StreamEvent.model_validate(data)
```

### 7.2 CLI Streaming Output

```python
def stream_response(client, agent_id, version_id, request):
    """Stream response with live updates."""
    full_response = ""
    
    with Live(console=console, refresh_per_second=10) as live:
        for event in client.invoke_agent_stream(agent_id, version_id, request):
            if event.event == "text":
                full_response += event.data
                live.update(Markdown(full_response))
            elif event.event == "done":
                break
            elif event.event == "error":
                raise APIError(event.data)
    
    return full_response
```

---

## 8. Interactive Mode

### 8.1 REPL Implementation

```python
def run_interactive_session(client, agent_id, version_id):
    """Run interactive chat session."""
    messages = []
    
    console.print(Panel.fit(
        f"Interactive session with agent: {agent_id}\n"
        "Type 'exit' or 'quit' to end, 'clear' to reset history",
        title="Agent Chat",
        border_style="cyan",
    ))
    
    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ")
        except (KeyboardInterrupt, EOFError):
            console.print("\nSession ended.")
            break
            
        if user_input.lower() in ("exit", "quit"):
            console.print("Session ended.")
            break
        elif user_input.lower() == "clear":
            messages = []
            console.print("[dim]Conversation history cleared.[/dim]")
            continue
        elif not user_input.strip():
            continue
        
        messages.append(ChatMessage(role="user", content=user_input))
        request = InvokeRequest(messages=messages)
        
        console.print("[bold cyan]Agent:[/bold cyan] ", end="")
        
        try:
            # Stream the response
            full_response = ""
            for event in client.invoke_agent_stream(agent_id, version_id, request):
                if event.event == "text":
                    console.print(event.data, end="")
                    full_response += event.data
                elif event.event == "done":
                    break
            
            console.print()  # Newline after response
            messages.append(ChatMessage(role="assistant", content=full_response))
            
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
```

---

## 9. Files to Create/Modify

### New Files

| File | Description |
|------|-------------|
| `ab_cli/models/invocation.py` | Invocation request/response models |
| `ab_cli/cli/invoke.py` | Invoke CLI commands |
| `tests/test_models/test_invocation.py` | Model tests |
| `tests/test_cli/test_invoke.py` | CLI command tests |
| `tests/test_api/test_invoke.py` | API client tests for invocation |

### Modify Files

| File | Changes |
|------|---------|
| `ab_cli/api/client.py` | Add invoke methods |
| `ab_cli/cli/main.py` | Register invoke command group |
| `ab_cli/models/__init__.py` | Export invocation models |

---

## 10. Implementation Steps

1. **Create invocation models** (`models/invocation.py`)
   - ChatMessage, InvokeRequest, InvokeTaskRequest
   - InvokeResponse, StreamEvent
   - Unit tests

2. **Add invoke methods to client** (`api/client.py`)
   - invoke_agent(), invoke_agent_stream()
   - invoke_task(), invoke_task_stream()
   - Unit tests with mocked responses

3. **Implement invoke chat command** (`cli/invoke.py`)
   - Message input from --message or --message-file
   - Non-streaming invocation
   - CLI tests

4. **Add streaming support**
   - SSE parsing for streaming responses
   - Live output with Rich
   - Stream with --stream flag

5. **Implement invoke task command**
   - JSON input file handling
   - Streaming support
   - CLI tests

6. **Implement interactive mode**
   - REPL loop with conversation history
   - Streaming output
   - Session commands (exit, clear)

7. **Update main.py**
   - Replace placeholder invoke group
   - Register new invoke commands

---

## 11. Example Usage

### Chat Invocation

```bash
# Simple question
$ ab invoke chat 123e4567-e89b-12d3-a456-426614174000 \
  --message "What is machine learning?"

Agent: Machine learning is a subset of artificial intelligence (AI) that 
enables systems to learn and improve from experience without being 
explicitly programmed...

# With streaming (real-time output)
$ ab invoke chat 123e4567-e89b-12d3-a456-426614174000 \
  --message "Write a haiku about coding" \
  --stream

Agent: Lines of syntax dance,
Logic flows through silicon—
Bugs bloom, then are crushed.
```

### Task Invocation

```bash
# task-input.json:
# {
#   "document": "path/to/document.pdf",
#   "extraction_fields": ["title", "date", "amount"]
# }

$ ab invoke task 123e4567-e89b-12d3-a456-426614174000 \
  --input task-input.json

Result:
{
  "title": "Invoice #12345",
  "date": "2026-02-09",
  "amount": "$1,234.56"
}
```

### Interactive Mode

```bash
$ ab invoke interactive 123e4567-e89b-12d3-a456-426614174000

╭────────────────────────────────────────────────────────╮
│ Interactive session with agent: 123e4567...            │
│ Type 'exit' or 'quit' to end, 'clear' to reset history │
╰────────────────────────────────────────────────────────╯

You: Hello, what can you help me with?
Agent: I'm a knowledge assistant that can help you with...

You: Tell me about our product offerings
Agent: Based on our knowledge base, we offer three main products...

You: exit
Session ended.
```

---

## 12. Testing Strategy

### Unit Tests

- Model validation (invocation.py)
- Request serialization
- Response parsing
- Stream event parsing

### API Client Tests (Mocked)

- invoke_agent() success/failure
- invoke_agent_stream() with mock SSE
- invoke_task() success/failure
- Error handling for invocation failures

### CLI Tests

- chat command with message
- chat command with message-file
- task command with input file
- Streaming flag handling
- JSON output format

---

## 13. Next Steps

1. **Review and approve this spec**
2. **Implementation in order:**
   - [ ] Invocation models
   - [ ] API client methods (non-streaming)
   - [ ] invoke chat command (non-streaming)
   - [ ] Streaming support
   - [ ] invoke task command
   - [ ] Interactive mode
3. **Run tests and verify**
4. **Update README/Usage.md**

---

*Document created: 2026-02-09*
*Status: DRAFT - Awaiting user review*
