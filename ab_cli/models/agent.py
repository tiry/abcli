"""Agent and Version data models.

These models represent the data structures returned by the Agent Builder API.
They use camelCase aliases to match the API's JSON format.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


class CamelModel(BaseModel):
    """Base model with camelCase serialization."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class Pagination(CamelModel):
    """Pagination information for list responses."""

    limit: int
    offset: int
    total_items: int  # Maps to totalItems
    has_more: bool = False  # Maps to hasMore


# =============================================================================
# Agent Models
# =============================================================================


class Agent(CamelModel):
    """Agent response model."""

    id: UUID
    type: str
    name: str
    description: str
    status: str = "CREATED"
    is_global_agent: bool = False
    current_version_id: UUID | None = None
    created_at: str
    created_by: str
    modified_at: str
    modified_by: str | None = None


class AgentList(CamelModel):
    """List of agents with pagination."""

    agents: list[Agent]
    pagination: Pagination


class AgentCreate(CamelModel):
    """Model for creating a new agent."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., max_length=200)
    agent_type: str
    version_label: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=255)
    config: dict[str, Any]

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "MyAgent",
                    "description": "A helpful assistant",
                    "agentType": "base",
                    "config": {
                        "llm_model_id": "anthropic.claude-3-haiku-20240307-v1:0",
                        "system_prompt": "You are a helpful assistant.",
                        "inference_config": {"max_tokens": 4000},
                    },
                }
            ]
        },
    )


class AgentUpdate(CamelModel):
    """Model for updating an agent (creates new version)."""

    version_label: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=255)
    config: dict[str, Any] | None = None


class AgentPatch(CamelModel):
    """Model for patching agent name/description without new version."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=200)


# =============================================================================
# Version Models
# =============================================================================


class Version(CamelModel):
    """Version summary model (without config)."""

    id: UUID
    number: int
    version_label: str | None = None
    notes: str | None = None
    created_at: str
    created_by: str


class VersionConfig(Version):
    """Version model with full configuration."""

    config: dict[str, Any]


class VersionCreate(CamelModel):
    """Model for creating a new version."""

    version_label: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=255)
    config: dict[str, Any]


class VersionList(CamelModel):
    """List of versions with associated agent and pagination."""

    agent: Agent
    versions: list[Version]
    pagination: Pagination


class AgentVersion(CamelModel):
    """Agent with its current version configuration."""

    agent: Agent
    version: VersionConfig


class AgentWithVersion(CamelModel):
    """Alias for AgentVersion for backward compatibility."""

    agent: Agent
    version: VersionConfig


# =============================================================================
# Agent Type Models
# =============================================================================


class AgentType(CamelModel):
    """Agent type information."""

    type: str
    description: str


class AgentTypeList(CamelModel):
    """List of available agent types."""

    agent_types: list[AgentType]
    pagination: Pagination
