"""Invocation request and response models.

Models for agent invocation requests and responses, supporting both chat and task agents.
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A chat message in a conversation."""

    role: str  # "user" | "assistant" | "system"
    content: str | list[dict[str, Any]]


class InvokeRequest(BaseModel):
    """Request to invoke a chat agent.

    Matches the ChatRequestBaseSchema from API specification.
    """

    messages: list[ChatMessage]
    temperature: float | None = None
    max_tokens: int | None = None

    # Additional fields from API spec
    hxql_query: str | None = Field(None, alias="hxqlQuery")
    hybrid_search: bool | None = Field(None, alias="hybridSearch")
    enable_deep_search: bool = Field(False, alias="enableDeepSearch")
    guardrails: list[str] | None = None

    class Config:
        populate_by_name = True


class InvokeTaskRequest(BaseModel):
    """Request to invoke a task agent with structured input."""

    inputs: dict[str, Any]
    temperature: float | None = None
    max_tokens: int | None = None


class InvokeResponse(BaseModel):
    """Response from agent invocation.

    Matches the AgentResponse from API specification with additional fields for compatibility.
    """

    # The response field might be in different places based on API version
    response: str | None = None

    # Fields from AgentResponse in OpenAPI spec
    created_at: int | None = Field(None, alias="createdAt")
    model: str | None = None
    object: Literal["response"] | None = "response"
    output: list[dict[str, Any]] | None = None
    custom_outputs: dict[str, Any] | None = Field(None, alias="customOutputs")

    # Additional fields for compatibility
    finish_reason: str | None = None
    usage: dict[str, int] | None = None  # token counts
    metadata: dict[str, Any] | None = None
    rag_mode: str | None = Field(None, alias="ragMode")

    # Allow extra fields to be captured
    model_config = {
        "extra": "allow",
        "populate_by_name": True,
    }

    def __init__(self, **data: Any) -> None:
        """Initialize with API response data.

        This constructor handles responses that may have the actual response
        content nested within various fields depending on the API version.
        """
        # Extract response from different possible locations

        # Case 1: Direct response field
        response_text = data.get("response")

        # Case 2: Nested in 'answer' field
        if not response_text and "answer" in data:
            if isinstance(data["answer"], dict) and "text" in data["answer"]:
                response_text = data["answer"]["text"]
            elif isinstance(data["answer"], str):
                response_text = data["answer"]

        # Case 3: In 'text' field
        if not response_text and "text" in data:
            response_text = data["text"]

        # Case 4: Nested in output[].content[].text structure
        if not response_text and "output" in data and isinstance(data["output"], list):
            # Iterate through all output items, but prioritize "message" type items
            for output_item in data["output"]:
                if not isinstance(output_item, dict):
                    continue

                # Look for message type items with content
                if (
                    output_item.get("type") == "message"
                    and "content" in output_item
                    and isinstance(output_item["content"], list)
                ):
                    for content_item in output_item["content"]:
                        if isinstance(content_item, dict) and "text" in content_item:
                            response_text = content_item["text"]
                            break
                    if response_text:
                        break

            # If we didn't find any message type, try the first item as fallback
            if not response_text and len(data["output"]) > 0:
                output_item = data["output"][0]
                if (
                    isinstance(output_item, dict)
                    and "content" in output_item
                    and isinstance(output_item["content"], list)
                ):
                    for content_item in output_item["content"]:
                        if isinstance(content_item, dict) and "text" in content_item:
                            response_text = content_item["text"]
                            break

        # Case 5: Nested in customOutputs structure
        if (
            not response_text
            and "customOutputs" in data
            and isinstance(data["customOutputs"], dict)
        ):
            custom = data["customOutputs"]
            if "answer" in custom:
                if isinstance(custom["answer"], dict) and "text" in custom["answer"]:
                    response_text = custom["answer"]["text"]
                elif isinstance(custom["answer"], str):
                    response_text = custom["answer"]

        # Update the response field if we found text
        if response_text:
            data["response"] = response_text

        super().__init__(**data)

        # Store extra fields
        self._extra_data = {
            k: v for k, v in data.items() if k not in self.__class__.__annotations__
        }

    def __getattr__(self, name: str) -> Any:
        """Allow access to extra fields not defined in the model."""
        if name in self._extra_data:
            return self._extra_data[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")


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
