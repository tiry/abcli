"""Tests for invocation data models."""

import json
from datetime import datetime
from uuid import UUID

from ab_cli.models.invocation import (
    ChatMessage,
    ConversationState,
    InvokeRequest,
    InvokeResponse,
    InvokeTaskRequest,
    StreamEvent,
)


class TestChatMessage:
    """Tests for ChatMessage model."""

    def test_chat_message_creation(self) -> None:
        """Create chat message with role and content."""
        message = ChatMessage(role="user", content="Hello world")
        assert message.role == "user"
        assert message.content == "Hello world"

        # Test with complex content
        complex_content = [
            {"type": "text", "text": "Hello"},
            {"type": "image", "source": {"type": "url", "url": "https://example.com/image.jpg"}}
        ]
        message2 = ChatMessage(role="user", content=complex_content)
        assert message2.role == "user"
        assert isinstance(message2.content, list)
        assert len(message2.content) == 2
        assert message2.content[0]["type"] == "text"

    def test_chat_message_serialization(self) -> None:
        """Chat message serializes to a dict."""
        message = ChatMessage(role="assistant", content="How can I help you?")
        data = message.model_dump()
        assert data["role"] == "assistant"
        assert data["content"] == "How can I help you?"

    def test_chat_message_from_dict(self) -> None:
        """Create chat message from dict."""
        data = {"role": "system", "content": "You are a helpful assistant."}
        message = ChatMessage.model_validate(data)
        assert message.role == "system"
        assert message.content == "You are a helpful assistant."

        # Test with complex content
        data2 = {
            "role": "user",
            "content": [
                {"type": "text", "text": "Analyze this document"},
                {"type": "document", "name": "Report", "source": {"type": "url", "url": "https://example.com/doc.pdf"}}
            ]
        }
        message2 = ChatMessage.model_validate(data2)
        assert message2.role == "user"
        assert isinstance(message2.content, list)
        assert len(message2.content) == 2

    def test_chat_message_json(self) -> None:
        """Chat message serializes to JSON."""
        message = ChatMessage(role="user", content="Tell me a story")
        json_data = message.model_dump_json()
        loaded = json.loads(json_data)
        assert loaded["role"] == "user"
        assert loaded["content"] == "Tell me a story"


class TestInvokeRequest:
    """Tests for InvokeRequest model."""

    def test_invoke_request_minimal(self) -> None:
        """Create invoke request with just messages."""
        messages = [
            ChatMessage(role="user", content="Hello")
        ]
        request = InvokeRequest(messages=messages)
        assert len(request.messages) == 1
        assert request.messages[0].role == "user"
        assert request.messages[0].content == "Hello"
        assert request.temperature is None
        assert request.max_tokens is None
        # Check default values for new fields
        assert request.enable_deep_search is False
        assert request.hxql_query is None
        assert request.hybrid_search is None
        assert request.guardrails is None

    def test_invoke_request_with_parameters(self) -> None:
        """Create invoke request with inference parameters."""
        messages = [
            ChatMessage(role="user", content="Generate a long story")
        ]
        request = InvokeRequest(
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
            hxqlQuery="SELECT * FROM SysContent",
            hybridSearch=True,
            enableDeepSearch=True,
            guardrails=["HAIP-Hate-High"]
        )
        assert request.temperature == 0.7
        assert request.max_tokens == 1000
        assert request.hxql_query == "SELECT * FROM SysContent"
        assert request.hybrid_search is True
        assert request.enable_deep_search is True
        assert request.guardrails == ["HAIP-Hate-High"]

    def test_invoke_request_serialization(self) -> None:
        """Invoke request serializes without None values."""
        messages = [
            ChatMessage(role="user", content="Hello")
        ]
        request = InvokeRequest(messages=messages)
        data = request.model_dump(exclude_none=True)
        assert "messages" in data
        assert "temperature" not in data
        assert "max_tokens" not in data
        assert "enable_deep_search" in data  # This is always included since it has a default

        # Check aliased serialization
        data = request.model_dump(exclude_none=True, by_alias=True)
        assert "enableDeepSearch" in data  # When by_alias=True we get camelCase

    def test_invoke_request_with_multiple_messages(self) -> None:
        """Create invoke request with message history."""
        messages = [
            ChatMessage(role="system", content="You are a helpful assistant"),
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there! How can I help?"),
            ChatMessage(role="user", content="Tell me about Python"),
        ]
        request = InvokeRequest(messages=messages)
        assert len(request.messages) == 4
        assert request.messages[0].role == "system"
        assert request.messages[-1].content == "Tell me about Python"


class TestInvokeTaskRequest:
    """Tests for InvokeTaskRequest model."""

    def test_invoke_task_request_minimal(self) -> None:
        """Create task request with just inputs."""
        inputs = {"document": "sample.pdf", "fields": ["date", "amount"]}
        request = InvokeTaskRequest(inputs=inputs)
        assert request.inputs["document"] == "sample.pdf"
        assert len(request.inputs["fields"]) == 2
        assert request.temperature is None
        assert request.max_tokens is None

    def test_invoke_task_request_with_parameters(self) -> None:
        """Create task request with inference parameters."""
        inputs = {"query": "What is machine learning?", "context": "AI textbook"}
        request = InvokeTaskRequest(
            inputs=inputs,
            temperature=0.5,
            max_tokens=500
        )
        assert request.temperature == 0.5
        assert request.max_tokens == 500

    def test_invoke_task_request_serialization(self) -> None:
        """Task request serializes without None values."""
        inputs = {"query": "What is Python?"}
        request = InvokeTaskRequest(inputs=inputs)
        data = request.model_dump(exclude_none=True)
        assert "inputs" in data
        assert "temperature" not in data
        assert "max_tokens" not in data

    def test_invoke_task_request_complex_inputs(self) -> None:
        """Create task request with nested inputs."""
        inputs = {
            "query": "Summarize the document",
            "document": {
                "title": "Annual Report",
                "sections": [
                    {"heading": "Introduction", "content": "..."},
                    {"heading": "Financial Results", "content": "..."}
                ]
            }
        }
        request = InvokeTaskRequest(inputs=inputs)
        assert request.inputs["query"] == "Summarize the document"
        assert request.inputs["document"]["title"] == "Annual Report"
        assert len(request.inputs["document"]["sections"]) == 2


class TestInvokeResponse:
    """Tests for InvokeResponse model."""

    def test_invoke_response_minimal(self) -> None:
        """Create response with just the text."""
        response = InvokeResponse(response="This is a test response.")
        assert response.response == "This is a test response."
        assert response.finish_reason is None
        assert response.usage is None
        assert response.metadata is None

    def test_invoke_response_with_metadata(self) -> None:
        """Create response with additional metadata."""
        response = InvokeResponse(
            response="The capital of France is Paris.",
            finish_reason="stop",
            usage={"prompt_tokens": 10, "completion_tokens": 6, "total_tokens": 16},
            metadata={"source": "knowledge_base", "confidence": 0.95}
        )
        assert response.finish_reason == "stop"
        assert response.usage["total_tokens"] == 16
        assert response.metadata["confidence"] == 0.95

    def test_invoke_response_from_dict(self) -> None:
        """Create response from API result dict."""
        data = {
            "response": "Hello, how can I help you today?",
            "finish_reason": "stop",
            "usage": {"prompt_tokens": 8, "completion_tokens": 7, "total_tokens": 15}
        }
        response = InvokeResponse.model_validate(data)
        assert response.response == "Hello, how can I help you today?"
        assert response.finish_reason == "stop"
        assert response.usage["prompt_tokens"] == 8

    def test_invoke_response_with_answer_string(self) -> None:
        """Create response from API with 'answer' field containing a string."""
        data = {
            "answer": "This is the answer from the API",
            "finish_reason": "stop"
        }
        response = InvokeResponse.model_validate(data)
        assert response.response == "This is the answer from the API"
        assert response.finish_reason == "stop"

    def test_invoke_response_with_answer_object(self) -> None:
        """Create response from API with 'answer' field containing an object with 'text'."""
        data = {
            "answer": {
                "text": "This is the answer text",
                "sources": ["doc1", "doc2"]
            },
            "finish_reason": "stop"
        }
        response = InvokeResponse.model_validate(data)
        assert response.response == "This is the answer text"
        assert response.finish_reason == "stop"

    def test_invoke_response_with_text_field(self) -> None:
        """Create response from API with 'text' field."""
        data = {
            "text": "This is the response text",
            "finish_reason": "stop"
        }
        response = InvokeResponse.model_validate(data)
        assert response.response == "This is the response text"
        assert response.finish_reason == "stop"

    def test_invoke_response_with_nested_custom_outputs(self) -> None:
        """Create response from API with nested answer in customOutputs."""
        data = {
            "finish_reason": "stop",
            "customOutputs": {
                "answer": "This is from the custom outputs field",
                "sources": ["doc1", "doc2"]
            }
        }
        response = InvokeResponse.model_validate(data)
        assert response.response == "This is from the custom outputs field"
        assert response.finish_reason == "stop"

    def test_invoke_response_with_api_specific_fields(self) -> None:
        """Create response with additional API-specific fields."""
        data = {
            "response": "Hello!",
            "createdAt": 1770752261,
            "ragMode": "normal",
            "some_other_field": "value"
        }
        response = InvokeResponse.model_validate(data)
        assert response.response == "Hello!"
        assert response.created_at == 1770752261
        assert response.rag_mode == "normal"
        # Access extra field through __getattr__
        assert response.some_other_field == "value"

    def test_invoke_response_with_bedrock_format(self) -> None:
        """Create response from Amazon Bedrock/Nova format."""
        data = {
            "model": "amazon.nova-micro-v1:0",
            "object": "response",
            "output": [
                {
                    "type": "message",
                    "status": "completed",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "I'm sorry, but I don't have enough information to help with that."
                        }
                    ],
                    "role": "assistant"
                }
            ],
            "customOutputs": {
                "sourceNodes": [],
                "ragMode": "normal"
            },
            "createdAt": 1770753022
        }
        response = InvokeResponse.model_validate(data)
        assert response.response == "I'm sorry, but I don't have enough information to help with that."
        assert response.created_at == 1770753022
        assert response.model == "amazon.nova-micro-v1:0"
        assert len(response.output) == 1
        assert response.output[0]["role"] == "assistant"

    def test_invoke_response_with_function_calls(self) -> None:
        """Create response from Anthropic/Claude format with function calls."""
        data = {
            "created_at": 1770753262,
            "output": [
                {
                    "type": "function_call",
                    "status": "completed",
                    "arguments": "{\"a\": 5, \"b\": 7}",
                    "callId": "tooluse_lIWxQd1Zji6SmRfFYSqil7",
                    "name": "multiply"
                },
                {
                    "type": "message",
                    "status": "completed",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "The result of 5 + 7 is 12."
                        }
                    ],
                    "role": "assistant"
                }
            ],
            "model": "anthropic.claude-3-haiku-20240307-v1:0",
            "object": "response"
        }
        response = InvokeResponse.model_validate(data)
        assert response.response == "The result of 5 + 7 is 12."
        assert response.created_at == 1770753262
        assert response.model == "anthropic.claude-3-haiku-20240307-v1:0"
        assert len(response.output) == 2
        assert response.output[0]["type"] == "function_call"
        assert response.output[1]["type"] == "message"

    def test_invoke_response_serialization(self) -> None:
        """Response serializes to dict with only present values."""
        response = InvokeResponse(response="Test response")
        data = response.model_dump(exclude_none=True)
        assert "response" in data
        assert "finish_reason" not in data
        assert "usage" not in data
        assert "metadata" not in data


class TestStreamEvent:
    """Tests for StreamEvent model."""

    def test_stream_event_text(self) -> None:
        """Create text event."""
        event = StreamEvent(event="text", data="Hello")
        assert event.event == "text"
        assert event.data == "Hello"

    def test_stream_event_error(self) -> None:
        """Create error event."""
        event = StreamEvent(event="error", data="Connection timeout")
        assert event.event == "error"
        assert event.data == "Connection timeout"

    def test_stream_event_done(self) -> None:
        """Create done event (may have no data)."""
        event = StreamEvent(event="done")
        assert event.event == "done"
        assert event.data is None

    def test_stream_event_from_dict(self) -> None:
        """Create stream event from SSE data."""
        data = {"event": "text", "data": "AI is a technology that"}
        event = StreamEvent.model_validate(data)
        assert event.event == "text"
        assert event.data == "AI is a technology that"

    def test_stream_event_serialization(self) -> None:
        """Stream event serializes to dict."""
        event = StreamEvent(event="text", data="Hello world")
        data = event.model_dump(exclude_none=True)
        assert data["event"] == "text"
        assert data["data"] == "Hello world"


class TestConversationState:
    """Tests for ConversationState model."""

    def test_conversation_state_creation(self) -> None:
        """Create new conversation state."""
        agent_id = UUID("12345678-1234-5678-1234-567812345678")
        state = ConversationState(agent_id=agent_id)
        assert state.agent_id == agent_id
        assert state.version_id is None
        assert len(state.messages) == 0
        assert isinstance(state.created_at, datetime)

    def test_conversation_state_with_version(self) -> None:
        """Create conversation with version ID."""
        agent_id = UUID("12345678-1234-5678-1234-567812345678")
        version_id = UUID("87654321-4321-8765-4321-876543218765")
        state = ConversationState(agent_id=agent_id, version_id=version_id)
        assert state.version_id == version_id

    def test_conversation_state_with_messages(self) -> None:
        """Create conversation with initial messages."""
        agent_id = UUID("12345678-1234-5678-1234-567812345678")
        messages = [
            ChatMessage(role="user", content="Hello"),
            ChatMessage(role="assistant", content="Hi there!")
        ]
        state = ConversationState(agent_id=agent_id, messages=messages)
        assert len(state.messages) == 2
        assert state.messages[0].role == "user"
        assert state.messages[1].content == "Hi there!"

    def test_conversation_state_add_message(self) -> None:
        """Add message to existing conversation."""
        agent_id = UUID("12345678-1234-5678-1234-567812345678")
        state = ConversationState(agent_id=agent_id)

        # Add messages
        state.messages.append(ChatMessage(role="user", content="Hello"))
        state.messages.append(ChatMessage(role="assistant", content="Hi there!"))

        assert len(state.messages) == 2
