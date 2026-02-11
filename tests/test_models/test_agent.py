"""Tests for agent data models."""

from uuid import UUID

from ab_cli.models.agent import (
    Agent,
    AgentCreate,
    AgentList,
    AgentPatch,
    AgentType,
    AgentTypeList,
    AgentUpdate,
    AgentVersion,
    Pagination,
    Version,
    VersionConfig,
    VersionCreate,
    VersionList,
    to_camel,
)


class TestCamelCase:
    """Tests for camelCase conversion."""

    def test_to_camel_single_word(self) -> None:
        """Simple word stays lowercase."""
        assert to_camel("name") == "name"

    def test_to_camel_two_words(self) -> None:
        """Two words convert correctly."""
        assert to_camel("agent_type") == "agentType"

    def test_to_camel_multiple_words(self) -> None:
        """Multiple words convert correctly."""
        assert to_camel("is_global_agent") == "isGlobalAgent"

    def test_to_camel_already_single(self) -> None:
        """Already single word unchanged."""
        assert to_camel("id") == "id"


class TestPagination:
    """Tests for Pagination model."""

    def test_pagination_creation(self) -> None:
        """Create pagination with required fields."""
        pagination = Pagination(limit=50, offset=0, total_items=100, has_more=True)
        assert pagination.limit == 50
        assert pagination.offset == 0
        assert pagination.total_items == 100
        assert pagination.has_more is True

    def test_pagination_serialization(self) -> None:
        """Pagination serializes to camelCase."""
        pagination = Pagination(limit=50, offset=10, total_items=100, has_more=False)
        data = pagination.model_dump(by_alias=True)
        assert "limit" in data
        assert "offset" in data
        assert "totalItems" in data
        assert "hasMore" in data


class TestAgent:
    """Tests for Agent model."""

    def test_agent_from_dict(self) -> None:
        """Create agent from dict with camelCase."""
        data = {
            "id": "12345678-1234-5678-1234-567812345678",
            "type": "base",
            "name": "TestAgent",
            "description": "A test agent",
            "status": "CREATED",
            "isGlobalAgent": False,
            "currentVersionId": "87654321-4321-8765-4321-876543218765",
            "createdAt": "2024-01-01T00:00:00Z",
            "createdBy": "user@example.com",
            "modifiedAt": "2024-01-02T00:00:00Z",
            "modifiedBy": "user@example.com",
        }
        agent = Agent.model_validate(data)
        assert agent.name == "TestAgent"
        assert agent.type == "base"
        assert agent.is_global_agent is False
        assert str(agent.id) == "12345678-1234-5678-1234-567812345678"

    def test_agent_default_status(self) -> None:
        """Agent has default status."""
        data = {
            "id": "12345678-1234-5678-1234-567812345678",
            "type": "base",
            "name": "TestAgent",
            "description": "A test agent",
            "createdAt": "2024-01-01T00:00:00Z",
            "createdBy": "user@example.com",
            "modifiedAt": "2024-01-02T00:00:00Z",
        }
        agent = Agent.model_validate(data)
        assert agent.status == "CREATED"

    def test_agent_serialization(self) -> None:
        """Agent serializes to camelCase."""
        agent = Agent(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            type="tool",
            name="MyAgent",
            description="Test",
            created_at="2024-01-01",
            created_by="user",
            modified_at="2024-01-02",
        )
        data = agent.model_dump(by_alias=True)
        assert "isGlobalAgent" in data
        assert "createdAt" in data
        assert "createdBy" in data


class TestAgentCreate:
    """Tests for AgentCreate model."""

    def test_agent_create_minimal(self) -> None:
        """Create agent with required fields."""
        agent = AgentCreate(
            name="NewAgent",
            description="A new agent",
            agent_type="base",
            config={"llm_model_id": "test-model"},
        )
        assert agent.name == "NewAgent"
        assert agent.agent_type == "base"
        assert agent.version_label is None

    def test_agent_create_with_optional(self) -> None:
        """Create agent with optional fields."""
        agent = AgentCreate(
            name="NewAgent",
            description="A new agent",
            agent_type="tool",
            config={"llm_model_id": "test-model", "tools": []},
            version_label="v1.0",
            notes="Initial version",
        )
        assert agent.version_label == "v1.0"
        assert agent.notes == "Initial version"

    def test_agent_create_serialization(self) -> None:
        """AgentCreate serializes to camelCase."""
        agent = AgentCreate(
            name="Test",
            description="Test",
            agent_type="base",
            config={},
            version_label="v1.0",
        )
        data = agent.model_dump(by_alias=True, exclude_none=True)
        assert "agentType" in data
        assert "versionLabel" in data


class TestAgentUpdate:
    """Tests for AgentUpdate model."""

    def test_agent_update_empty(self) -> None:
        """Create update with no changes."""
        update = AgentUpdate()
        assert update.config is None
        assert update.version_label is None
        assert update.notes is None

    def test_agent_update_with_config(self) -> None:
        """Create update with new config."""
        update = AgentUpdate(
            config={"llm_model_id": "new-model"},
            version_label="v2.0",
            notes="Updated model",
        )
        assert update.config is not None
        assert update.version_label == "v2.0"


class TestAgentPatch:
    """Tests for AgentPatch model."""

    def test_agent_patch_name_only(self) -> None:
        """Patch only name."""
        patch = AgentPatch(name="NewName")
        assert patch.name == "NewName"
        assert patch.description is None

    def test_agent_patch_both(self) -> None:
        """Patch name and description."""
        patch = AgentPatch(name="NewName", description="New description")
        assert patch.name == "NewName"
        assert patch.description == "New description"


class TestVersion:
    """Tests for Version model."""

    def test_version_from_dict(self) -> None:
        """Create version from dict."""
        data = {
            "id": "12345678-1234-5678-1234-567812345678",
            "number": 1,
            "versionLabel": "v1.0",
            "notes": "Initial version",
            "createdAt": "2024-01-01T00:00:00Z",
            "createdBy": "user@example.com",
        }
        version = Version.model_validate(data)
        assert version.number == 1
        assert version.version_label == "v1.0"
        assert version.notes == "Initial version"

    def test_version_without_optional(self) -> None:
        """Create version without optional fields."""
        data = {
            "id": "12345678-1234-5678-1234-567812345678",
            "number": 1,
            "createdAt": "2024-01-01T00:00:00Z",
            "createdBy": "user@example.com",
        }
        version = Version.model_validate(data)
        assert version.version_label is None
        assert version.notes is None


class TestVersionConfig:
    """Tests for VersionConfig model."""

    def test_version_config_inherits(self) -> None:
        """VersionConfig has all Version fields plus config."""
        data = {
            "id": "12345678-1234-5678-1234-567812345678",
            "number": 1,
            "createdAt": "2024-01-01T00:00:00Z",
            "createdBy": "user@example.com",
            "config": {"llm_model_id": "test-model", "system_prompt": "Hello"},
        }
        version = VersionConfig.model_validate(data)
        assert version.number == 1
        assert version.config["llm_model_id"] == "test-model"


class TestVersionCreate:
    """Tests for VersionCreate model."""

    def test_version_create(self) -> None:
        """Create version with config."""
        version = VersionCreate(
            config={"llm_model_id": "test-model"},
            version_label="v2.0",
            notes="New version",
        )
        assert version.config["llm_model_id"] == "test-model"
        assert version.version_label == "v2.0"


class TestAgentList:
    """Tests for AgentList model."""

    def test_agent_list_from_dict(self) -> None:
        """Create agent list from API response."""
        data = {
            "agents": [
                {
                    "id": "12345678-1234-5678-1234-567812345678",
                    "type": "base",
                    "name": "Agent1",
                    "description": "First agent",
                    "createdAt": "2024-01-01T00:00:00Z",
                    "createdBy": "user",
                    "modifiedAt": "2024-01-01T00:00:00Z",
                },
            ],
            "pagination": {"limit": 50, "offset": 0, "totalItems": 1, "hasMore": False},
        }
        result = AgentList.model_validate(data)
        assert len(result.agents) == 1
        assert result.agents[0].name == "Agent1"
        assert result.pagination.total_items == 1


class TestVersionList:
    """Tests for VersionList model."""

    def test_version_list_from_dict(self) -> None:
        """Create version list from API response."""
        data = {
            "agent": {
                "id": "12345678-1234-5678-1234-567812345678",
                "type": "base",
                "name": "TestAgent",
                "description": "Test",
                "createdAt": "2024-01-01T00:00:00Z",
                "createdBy": "user",
                "modifiedAt": "2024-01-01T00:00:00Z",
            },
            "versions": [
                {
                    "id": "87654321-4321-8765-4321-876543218765",
                    "number": 1,
                    "createdAt": "2024-01-01T00:00:00Z",
                    "createdBy": "user",
                },
            ],
            "pagination": {"limit": 50, "offset": 0, "totalItems": 1, "hasMore": False},
        }
        result = VersionList.model_validate(data)
        assert result.agent.name == "TestAgent"
        assert len(result.versions) == 1
        assert result.versions[0].number == 1


class TestAgentVersion:
    """Tests for AgentVersion model."""

    def test_agent_version_from_dict(self) -> None:
        """Create agent version from API response."""
        data = {
            "agent": {
                "id": "12345678-1234-5678-1234-567812345678",
                "type": "base",
                "name": "TestAgent",
                "description": "Test",
                "createdAt": "2024-01-01T00:00:00Z",
                "createdBy": "user",
                "modifiedAt": "2024-01-01T00:00:00Z",
            },
            "version": {
                "id": "87654321-4321-8765-4321-876543218765",
                "number": 1,
                "createdAt": "2024-01-01T00:00:00Z",
                "createdBy": "user",
                "config": {"llm_model_id": "test-model"},
            },
        }
        result = AgentVersion.model_validate(data)
        assert result.agent.name == "TestAgent"
        assert result.version.config["llm_model_id"] == "test-model"


class TestAgentType:
    """Tests for AgentType model."""

    def test_agent_type_from_dict(self) -> None:
        """Create agent type from dict."""
        data = {"type": "base", "description": "Basic conversational agent"}
        agent_type = AgentType.model_validate(data)
        assert agent_type.type == "base"
        assert "conversational" in agent_type.description.lower()


class TestAgentTypeList:
    """Tests for AgentTypeList model."""

    def test_agent_type_list_from_dict(self) -> None:
        """Create agent type list from API response."""
        data = {
            "agentTypes": [
                {"type": "base", "description": "Basic agent"},
                {"type": "tool", "description": "Agent with tools"},
            ],
            "pagination": {"limit": 50, "offset": 0, "totalItems": 2, "hasMore": False},
        }
        result = AgentTypeList.model_validate(data)
        assert len(result.agent_types) == 2
        assert result.agent_types[0].type == "base"
        assert result.agent_types[1].type == "tool"
