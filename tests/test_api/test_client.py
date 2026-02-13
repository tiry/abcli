"""Tests for AgentBuilderClient."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from ab_cli.api.client import AgentBuilderClient
from ab_cli.api.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)
from ab_cli.api.exceptions import (
    ConnectionError as APIConnectionError,
)
from ab_cli.config.settings import ABSettings
from ab_cli.models.agent import AgentCreate, AgentPatch, AgentUpdate, VersionCreate


@pytest.fixture
def settings() -> ABSettings:
    """Create test settings."""
    return ABSettings(
        api_endpoint="https://api.example.com/",
        oauth_token_url="https://auth.example.com/token",
        client_id="test-client",
        client_secret="test-secret",
        environment_id="env-12345678-1234-5678-1234-567812345678",
    )


@pytest.fixture
def mock_auth() -> MagicMock:
    """Create a mock auth client."""
    auth = MagicMock()
    auth.get_access_token.return_value = "test-token"
    return auth


@pytest.fixture
def client(settings: ABSettings, mock_auth: MagicMock) -> AgentBuilderClient:
    """Create a test client with mock auth."""
    return AgentBuilderClient(settings, auth_client=mock_auth)


class TestAgentBuilderClientInit:
    """Tests for client initialization."""

    def test_base_url_construction(self, client: AgentBuilderClient) -> None:
        """Base URL uses v1 prefix (environment from token)."""
        assert client.base_url.endswith("/v1")
        assert "environments" not in client.base_url

    def test_creates_auth_client_if_not_provided(self, settings: ABSettings) -> None:
        """Auth client is created if not provided."""
        with patch("ab_cli.api.client.AuthClient") as MockAuth:
            client = AgentBuilderClient(settings)
            MockAuth.assert_called_once_with(settings)


class TestAgentBuilderClientContextManager:
    """Tests for context manager behavior."""

    def test_context_manager(self, client: AgentBuilderClient) -> None:
        """Client can be used as context manager."""
        with client as c:
            assert c is client

    def test_context_manager_closes(self, client: AgentBuilderClient) -> None:
        """Close is called on context exit."""
        mock_http_client = MagicMock()
        client._client = mock_http_client
        with client:
            pass
        # After close(), client._client is set to None
        mock_http_client.close.assert_called_once()


class TestHandleResponse:
    """Tests for response handling."""

    def test_handle_success_response(self, client: AgentBuilderClient) -> None:
        """Success response returns JSON data."""
        response = MagicMock()
        response.status_code = 200
        response.is_success = True
        response.json.return_value = {"key": "value"}

        result = client._handle_response(response)
        assert result == {"key": "value"}

    def test_handle_204_response(self, client: AgentBuilderClient) -> None:
        """204 No Content returns empty dict."""
        response = MagicMock()
        response.status_code = 204

        result = client._handle_response(response)
        assert result == {}

    def test_handle_401_response(self, client: AgentBuilderClient) -> None:
        """401 raises AuthenticationError."""
        response = MagicMock()
        response.status_code = 401
        response.is_success = False
        response.json.return_value = {"detail": "Invalid token"}

        with pytest.raises(AuthenticationError, match="Authentication failed"):
            client._handle_response(response)

    def test_handle_403_response(self, client: AgentBuilderClient) -> None:
        """403 raises AuthenticationError."""
        response = MagicMock()
        response.status_code = 403
        response.is_success = False
        response.json.return_value = {"detail": "Access denied"}

        with pytest.raises(AuthenticationError, match="Access denied"):
            client._handle_response(response)

    def test_handle_404_response(self, client: AgentBuilderClient) -> None:
        """404 raises NotFoundError."""
        response = MagicMock()
        response.status_code = 404
        response.is_success = False
        response.json.return_value = {"detail": "Agent not found"}

        with pytest.raises(NotFoundError, match="not found"):
            client._handle_response(response)

    def test_handle_400_response(self, client: AgentBuilderClient) -> None:
        """400 raises ValidationError."""
        response = MagicMock()
        response.status_code = 400
        response.is_success = False
        response.json.return_value = {"detail": "Invalid data"}

        with pytest.raises(ValidationError, match="Validation error"):
            client._handle_response(response)

    def test_handle_422_response(self, client: AgentBuilderClient) -> None:
        """422 raises ValidationError."""
        response = MagicMock()
        response.status_code = 422
        response.is_success = False
        response.json.return_value = {"detail": "Unprocessable entity"}

        with pytest.raises(ValidationError, match="Validation error"):
            client._handle_response(response)

    def test_handle_429_response(self, client: AgentBuilderClient) -> None:
        """429 raises RateLimitError."""
        response = MagicMock()
        response.status_code = 429
        response.is_success = False
        response.json.return_value = {"detail": "Too many requests"}

        with pytest.raises(RateLimitError, match="Rate limit"):
            client._handle_response(response)


class TestListAgents:
    """Tests for list_agents method."""

    def test_list_agents_success(self, client: AgentBuilderClient) -> None:
        """List agents returns AgentList."""
        mock_response = {
            "agents": [
                {
                    "id": "12345678-1234-5678-1234-567812345678",
                    "type": "base",
                    "name": "TestAgent",
                    "description": "Test",
                    "createdAt": "2024-01-01T00:00:00Z",
                    "createdBy": "user",
                    "modifiedAt": "2024-01-01T00:00:00Z",
                }
            ],
            "pagination": {"limit": 50, "offset": 0, "totalItems": 1, "hasMore": False},
        }

        with patch.object(client, "_request", return_value=mock_response):
            result = client.list_agents()
            assert len(result.agents) == 1
            assert result.agents[0].name == "TestAgent"
            assert result.pagination.total_items == 1

    def test_list_agents_with_pagination(self, client: AgentBuilderClient) -> None:
        """List agents passes pagination params."""
        mock_response = {
            "agents": [],
            "pagination": {"limit": 10, "offset": 20, "totalItems": 0, "hasMore": False},
        }

        with patch.object(client, "_request", return_value=mock_response) as mock_req:
            client.list_agents(limit=10, offset=20)
            mock_req.assert_called_once_with(
                "GET",
                "/agents",
                params={"limit": 10, "offset": 20},
            )


class TestGetAgent:
    """Tests for get_agent method."""

    def test_get_agent_success(self, client: AgentBuilderClient) -> None:
        """Get agent returns AgentVersion."""
        mock_response = {
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

        with patch.object(client, "_request", return_value=mock_response):
            result = client.get_agent("12345678-1234-5678-1234-567812345678")
            assert result.agent.name == "TestAgent"
            assert result.version.config["llm_model_id"] == "test-model"


class TestCreateAgent:
    """Tests for create_agent method."""

    def test_create_agent_success(self, client: AgentBuilderClient) -> None:
        """Create agent returns a dictionary."""
        agent_create = AgentCreate(
            name="NewAgent",
            description="A new agent",
            agent_type="base",
            config={"llm_model_id": "test-model"},
        )

        mock_response = {
            "id": "12345678-1234-5678-1234-567812345678",
            "type": "base",
            "name": "NewAgent",
            "description": "A new agent",
            "createdAt": "2024-01-01T00:00:00Z",
            "createdBy": "user",
            "modifiedAt": "2024-01-01T00:00:00Z",
            "currentVersionId": "87654321-4321-8765-4321-876543218765",
        }

        with patch.object(client, "_request", return_value=mock_response) as mock_req:
            result = client.create_agent(agent_create)
            assert result["name"] == "NewAgent"
            assert result["id"] == "12345678-1234-5678-1234-567812345678"

            # Verify POST was called with correct data
            mock_req.assert_called_once()
            call_args = mock_req.call_args
            assert call_args[0][0] == "POST"
            assert call_args[0][1] == "/agents"


class TestUpdateAgent:
    """Tests for update_agent method."""

    def test_update_agent_success(self, client: AgentBuilderClient) -> None:
        """Update agent returns AgentVersion with new version."""
        update = AgentUpdate(
            config={"llm_model_id": "new-model"},
            version_label="v2.0",
        )

        mock_response = {
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
                "id": "99999999-9999-9999-9999-999999999999",
                "number": 2,
                "versionLabel": "v2.0",
                "createdAt": "2024-01-02T00:00:00Z",
                "createdBy": "user",
                "config": {"llm_model_id": "new-model"},
            },
        }

        with patch.object(client, "_request", return_value=mock_response):
            result = client.update_agent("12345678-1234-5678-1234-567812345678", update)
            assert result.version.number == 2
            assert result.version.version_label == "v2.0"


class TestPatchAgent:
    """Tests for patch_agent method."""

    def test_patch_agent_success(self, client: AgentBuilderClient) -> None:
        """Patch agent returns updated Agent."""
        agent_patch = AgentPatch(name="NewName", description="New desc")

        mock_response = {
            "id": "12345678-1234-5678-1234-567812345678",
            "type": "base",
            "name": "NewName",
            "description": "New desc",
            "createdAt": "2024-01-01T00:00:00Z",
            "createdBy": "user",
            "modifiedAt": "2024-01-02T00:00:00Z",
        }

        with patch.object(client, "_request", return_value=mock_response):
            result = client.patch_agent("12345678-1234-5678-1234-567812345678", agent_patch)
            assert result.name == "NewName"
            assert result.description == "New desc"


class TestDeleteAgent:
    """Tests for delete_agent method."""

    def test_delete_agent_success(self, client: AgentBuilderClient) -> None:
        """Delete agent calls DELETE endpoint."""
        with patch.object(client, "_request", return_value={}) as mock_req:
            client.delete_agent("12345678-1234-5678-1234-567812345678")
            mock_req.assert_called_once_with(
                "DELETE",
                "/agents/12345678-1234-5678-1234-567812345678",
            )


class TestListVersions:
    """Tests for list_versions method."""

    def test_list_versions_success(self, client: AgentBuilderClient) -> None:
        """List versions returns VersionList."""
        mock_response = {
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
                {
                    "id": "99999999-9999-9999-9999-999999999999",
                    "number": 2,
                    "createdAt": "2024-01-02T00:00:00Z",
                    "createdBy": "user",
                },
            ],
            "pagination": {"limit": 50, "offset": 0, "totalItems": 2, "hasMore": False},
        }

        with patch.object(client, "_request", return_value=mock_response):
            result = client.list_versions("12345678-1234-5678-1234-567812345678")
            assert len(result.versions) == 2
            assert result.versions[0].number == 1
            assert result.versions[1].number == 2


class TestGetVersion:
    """Tests for get_version method."""

    def test_get_version_success(self, client: AgentBuilderClient) -> None:
        """Get version returns AgentVersion."""
        mock_response = {
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

        with patch.object(client, "_request", return_value=mock_response):
            result = client.get_version(
                "12345678-1234-5678-1234-567812345678",
                "87654321-4321-8765-4321-876543218765",
            )
            assert result.version.number == 1


class TestCreateVersion:
    """Tests for create_version method."""

    def test_create_version_success(self, client: AgentBuilderClient) -> None:
        """Create version returns AgentVersion."""
        version_create = VersionCreate(
            config={"llm_model_id": "new-model"},
            version_label="v2.0",
            notes="New version",
        )

        mock_response = {
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
                "id": "99999999-9999-9999-9999-999999999999",
                "number": 2,
                "versionLabel": "v2.0",
                "notes": "New version",
                "createdAt": "2024-01-02T00:00:00Z",
                "createdBy": "user",
                "config": {"llm_model_id": "new-model"},
            },
        }

        with patch.object(client, "_request", return_value=mock_response):
            result = client.create_version(
                "12345678-1234-5678-1234-567812345678",
                version_create,
            )
            assert result.version.number == 2
            assert result.version.version_label == "v2.0"


class TestConnectionErrors:
    """Tests for connection error handling."""

    def test_connect_error(self, client: AgentBuilderClient) -> None:
        """Connection error raises APIConnectionError."""
        mock_http_client = MagicMock()
        mock_http_client.request.side_effect = httpx.ConnectError("Connection refused")
        client._client = mock_http_client

        with pytest.raises(APIConnectionError, match="Failed to connect"):
            client._request("GET", "/agents")

    def test_timeout_error(self, client: AgentBuilderClient) -> None:
        """Timeout raises APIConnectionError."""
        mock_http_client = MagicMock()
        mock_http_client.request.side_effect = httpx.TimeoutException("Request timed out")
        client._client = mock_http_client

        with pytest.raises(APIConnectionError, match="timed out"):
            client._request("GET", "/agents")
