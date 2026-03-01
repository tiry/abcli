"""Models for batch collection results."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CollectionMetrics(BaseModel):
    """Metrics for a single invocation in a collection."""

    success: bool = Field(description="Whether the invocation succeeded")
    status_code: int | None = Field(default=None, description="HTTP status code")
    execution_time_ms: int = Field(description="Execution time in milliseconds")
    retry_count: int = Field(default=0, description="Number of retries attempted (0, 1)")
    error_message: str | None = Field(default=None, description="Error details if failed")


class CollectionAgent(BaseModel):
    """Agent information for a collection result."""

    agent_id: str = Field(description="Agent ID")
    version_id: str = Field(description="Version ID")


class CollectionResult(BaseModel):
    """Single result in a collection batch."""

    timestamp: datetime = Field(description="When the invocation completed")
    invocation_index: int = Field(description="Zero-based index in the batch")
    message_id: str = Field(description="Message ID from input or generated")
    agent: CollectionAgent = Field(description="Agent information")
    input: dict[str, Any] = Field(description="Input sent to the agent")
    output: dict[str, Any] | None = Field(default=None, description="Response from agent")
    metrics: CollectionMetrics = Field(description="Invocation metrics")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSONL output.

        Returns:
            Dictionary with ISO timestamp string
        """
        data = self.model_dump()
        # Convert datetime to ISO string
        data["timestamp"] = self.timestamp.isoformat()
        return data
