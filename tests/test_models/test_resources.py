"""Tests for resource models."""


from ab_cli.models.agent import Pagination
from ab_cli.models.resources import (
    DeprecationStatus,
    GuardrailList,
    GuardrailModel,
    LLMModel,
    LLMModelList,
)


class TestDeprecationStatus:
    """Tests for DeprecationStatus model."""

    def test_deprecation_status_defaults(self):
        """Test default values for DeprecationStatus."""
        status = DeprecationStatus()

        assert status.deprecated is False
        assert status.deprecation_date == ""
        assert status.replacement_model_name == ""

    def test_deprecation_status_with_values(self):
        """Test DeprecationStatus with provided values."""
        status = DeprecationStatus(
            deprecated=True,
            deprecation_date="2025-12-31",
            replacement_model_name="new-model"
        )

        assert status.deprecated is True
        assert status.deprecation_date == "2025-12-31"
        assert status.replacement_model_name == "new-model"

    def test_deprecation_status_serialization(self):
        """Test serialization of DeprecationStatus."""
        status = DeprecationStatus(
            deprecated=True,
            deprecation_date="2025-12-31",
            replacement_model_name="new-model"
        )

        serialized = status.model_dump(by_alias=True)

        assert serialized["deprecated"] is True
        assert serialized["deprecationDate"] == "2025-12-31"
        assert serialized["replacementModelName"] == "new-model"


class TestLLMModel:
    """Tests for LLMModel."""

    def test_llm_model_creation(self):
        """Test creating an LLM model."""
        model = LLMModel(
            id="model-123",
            name="Test Model",
            description="A test model",
            badge="Test",
            metadata="metadata",
            agent_types=["tool", "rag"],
            capabilities={"multimodal": True, "streaming": True},
            regions=["us-east", "eu-west"]
        )

        assert model.id == "model-123"
        assert model.name == "Test Model"
        assert model.description == "A test model"
        assert model.badge == "Test"
        assert model.metadata == "metadata"
        assert model.agent_types == ["tool", "rag"]
        assert model.capabilities == {"multimodal": True, "streaming": True}
        assert model.regions == ["us-east", "eu-west"]
        assert model.deprecation_status.deprecated is False  # Default value

    def test_llm_model_with_deprecation(self):
        """Test LLM model with deprecation status."""
        deprecation_status = DeprecationStatus(
            deprecated=True,
            deprecation_date="2025-12-31",
            replacement_model_name="new-model"
        )

        model = LLMModel(
            id="model-123",
            name="Test Model",
            description="A test model",
            badge="Test",
            metadata="metadata",
            agent_types=["tool", "rag"],
            capabilities={"multimodal": True, "streaming": True},
            regions=["us-east", "eu-west"],
            deprecation_status=deprecation_status
        )

        assert model.deprecation_status.deprecated is True
        assert model.deprecation_status.deprecation_date == "2025-12-31"
        assert model.deprecation_status.replacement_model_name == "new-model"

    def test_llm_model_serialization(self):
        """Test serialization of LLM model."""
        model = LLMModel(
            id="model-123",
            name="Test Model",
            description="A test model",
            badge="Test",
            metadata="metadata",
            agent_types=["tool", "rag"],
            capabilities={"multimodal": True, "streaming": True},
            regions=["us-east", "eu-west"]
        )

        serialized = model.model_dump(by_alias=True)

        assert serialized["id"] == "model-123"
        assert serialized["name"] == "Test Model"
        assert serialized["description"] == "A test model"
        assert serialized["badge"] == "Test"
        assert serialized["metadata"] == "metadata"
        assert serialized["agentTypes"] == ["tool", "rag"]
        assert serialized["capabilities"] == {"multimodal": True, "streaming": True}
        assert serialized["regions"] == ["us-east", "eu-west"]
        assert serialized["deprecationStatus"]["deprecated"] is False

    def test_llm_model_from_dict(self):
        """Test creating an LLM model from a dictionary."""
        model_dict = {
            "id": "model-123",
            "name": "Test Model",
            "description": "A test model",
            "badge": "Test",
            "metadata": "metadata",
            "agentTypes": ["tool", "rag"],
            "capabilities": {"multimodal": True, "streaming": True},
            "regions": ["us-east", "eu-west"],
            "deprecationStatus": {
                "deprecated": True,
                "deprecationDate": "2025-12-31",
                "replacementModelName": "new-model"
            }
        }

        model = LLMModel.model_validate(model_dict)

        assert model.id == "model-123"
        assert model.name == "Test Model"
        assert model.description == "A test model"
        assert model.badge == "Test"
        assert model.metadata == "metadata"
        assert model.agent_types == ["tool", "rag"]
        assert model.capabilities == {"multimodal": True, "streaming": True}
        assert model.regions == ["us-east", "eu-west"]
        assert model.deprecation_status.deprecated is True
        assert model.deprecation_status.deprecation_date == "2025-12-31"
        assert model.deprecation_status.replacement_model_name == "new-model"


class TestLLMModelList:
    """Tests for LLMModelList."""

    def test_llm_model_list_creation(self):
        """Test creating an LLM model list."""
        model_list = LLMModelList(
            models=[
                LLMModel(
                    id="model1",
                    name="Test Model 1",
                    description="Test description 1",
                    badge="Test1",
                    metadata="metadata1",
                    agent_types=["tool", "rag"],
                    capabilities={"multimodal": True, "streaming": True},
                    regions=["us-east", "eu-west"]
                ),
                LLMModel(
                    id="model2",
                    name="Test Model 2",
                    description="Test description 2",
                    badge="Test2",
                    metadata="metadata2",
                    agent_types=["task"],
                    capabilities={"multimodal": False, "streaming": False},
                    regions=["us-east"]
                )
            ],
            pagination=Pagination(limit=50, offset=0, total_items=2)
        )

        assert len(model_list.models) == 2
        assert model_list.models[0].id == "model1"
        assert model_list.models[1].id == "model2"
        assert model_list.pagination.total_items == 2

    def test_llm_model_list_serialization(self):
        """Test serialization of LLM model list."""
        model_list = LLMModelList(
            models=[
                LLMModel(
                    id="model1",
                    name="Test Model 1",
                    description="Test description 1",
                    badge="Test1",
                    metadata="metadata1",
                    agent_types=["tool", "rag"],
                    capabilities={"multimodal": True, "streaming": True},
                    regions=["us-east", "eu-west"]
                )
            ],
            pagination=Pagination(limit=50, offset=0, total_items=1)
        )

        serialized = model_list.model_dump(by_alias=True)

        assert len(serialized["models"]) == 1
        assert serialized["models"][0]["id"] == "model1"
        assert serialized["models"][0]["name"] == "Test Model 1"
        assert serialized["pagination"]["totalItems"] == 1

    def test_llm_model_list_from_dict(self):
        """Test creating an LLM model list from a dictionary."""
        model_list_dict = {
            "models": [
                {
                    "id": "model1",
                    "name": "Test Model 1",
                    "description": "Test description 1",
                    "badge": "Test1",
                    "metadata": "metadata1",
                    "agentTypes": ["tool", "rag"],
                    "capabilities": {"multimodal": True, "streaming": True},
                    "regions": ["us-east", "eu-west"],
                    "deprecationStatus": {"deprecated": False}
                }
            ],
            "pagination": {
                "limit": 50,
                "offset": 0,
                "totalItems": 1
            }
        }

        model_list = LLMModelList.model_validate(model_list_dict)

        assert len(model_list.models) == 1
        assert model_list.models[0].id == "model1"
        assert model_list.models[0].name == "Test Model 1"
        assert model_list.models[0].agent_types == ["tool", "rag"]
        assert model_list.pagination.total_items == 1


class TestGuardrailModel:
    """Tests for GuardrailModel."""

    def test_guardrail_model_creation(self):
        """Test creating a guardrail model."""
        guardrail = GuardrailModel(name="test-guardrail", description="Test guardrail")

        assert guardrail.name == "test-guardrail"
        assert guardrail.description == "Test guardrail"

    def test_guardrail_model_default_description(self):
        """Test guardrail model with default description."""
        guardrail = GuardrailModel(name="test-guardrail")

        assert guardrail.name == "test-guardrail"
        assert guardrail.description == ""

    def test_guardrail_model_serialization(self):
        """Test serialization of guardrail model."""
        guardrail = GuardrailModel(name="test-guardrail", description="Test guardrail")

        serialized = guardrail.model_dump(by_alias=True)

        assert serialized["name"] == "test-guardrail"
        assert serialized["description"] == "Test guardrail"

    def test_guardrail_model_from_dict(self):
        """Test creating a guardrail model from a dictionary."""
        guardrail_dict = {
            "name": "test-guardrail",
            "description": "Test guardrail"
        }

        guardrail = GuardrailModel.model_validate(guardrail_dict)

        assert guardrail.name == "test-guardrail"
        assert guardrail.description == "Test guardrail"


class TestGuardrailList:
    """Tests for GuardrailList."""

    def test_guardrail_list_creation(self):
        """Test creating a guardrail list."""
        guardrail_list = GuardrailList(
            guardrails=[
                GuardrailModel(name="guardrail1", description="Test guardrail 1"),
                GuardrailModel(name="guardrail2", description="Test guardrail 2")
            ],
            pagination=Pagination(limit=50, offset=0, total_items=2)
        )

        assert len(guardrail_list.guardrails) == 2
        assert guardrail_list.guardrails[0].name == "guardrail1"
        assert guardrail_list.guardrails[1].name == "guardrail2"
        assert guardrail_list.pagination.total_items == 2

    def test_guardrail_list_serialization(self):
        """Test serialization of guardrail list."""
        guardrail_list = GuardrailList(
            guardrails=[
                GuardrailModel(name="guardrail1", description="Test guardrail 1")
            ],
            pagination=Pagination(limit=50, offset=0, total_items=1)
        )

        serialized = guardrail_list.model_dump(by_alias=True)

        assert len(serialized["guardrails"]) == 1
        assert serialized["guardrails"][0]["name"] == "guardrail1"
        assert serialized["guardrails"][0]["description"] == "Test guardrail 1"
        assert serialized["pagination"]["totalItems"] == 1

    def test_guardrail_list_from_dict(self):
        """Test creating a guardrail list from a dictionary."""
        guardrail_list_dict = {
            "guardrails": [
                {"name": "guardrail1", "description": "Test guardrail 1"},
                {"name": "guardrail2", "description": "Test guardrail 2"}
            ],
            "pagination": {
                "limit": 50,
                "offset": 0,
                "totalItems": 2
            }
        }

        guardrail_list = GuardrailList.model_validate(guardrail_list_dict)

        assert len(guardrail_list.guardrails) == 2
        assert guardrail_list.guardrails[0].name == "guardrail1"
        assert guardrail_list.guardrails[1].name == "guardrail2"
        assert guardrail_list.pagination.total_items == 2
