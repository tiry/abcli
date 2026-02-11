"""Resource models for models and guardrails."""

from pydantic import Field

from ab_cli.models.agent import CamelModel, Pagination


class DeprecationStatus(CamelModel):
    """Deprecation status for LLM models."""

    deprecated: bool = False
    deprecation_date: str = ""
    replacement_model_name: str = ""


class LLMModel(CamelModel):
    """LLM model information."""

    id: str
    name: str
    description: str
    badge: str
    metadata: str
    agent_types: list[str]
    capabilities: dict
    regions: list[str]
    deprecation_status: DeprecationStatus = Field(default_factory=DeprecationStatus)


class LLMModelList(CamelModel):
    """List of LLM models with pagination."""

    models: list[LLMModel]
    pagination: Pagination


class GuardrailModel(CamelModel):
    """Guardrail information."""

    name: str
    description: str = ""


class GuardrailList(CamelModel):
    """List of guardrails with pagination."""

    guardrails: list[GuardrailModel]
    pagination: Pagination
