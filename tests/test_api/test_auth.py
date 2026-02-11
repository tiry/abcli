"""Tests for the OAuth2 authentication client."""

import time
from unittest.mock import MagicMock, patch

import httpx
import pytest

from ab_cli.api.auth import AuthClient, TokenInfo
from ab_cli.api.exceptions import AuthenticationError, TokenError
from ab_cli.config.settings import ABSettings


class TestTokenInfo:
    """Tests for TokenInfo class."""

    def test_token_creation(self):
        """Test creating a token info object."""
        token = TokenInfo(
            access_token="test-token",
            token_type="Bearer",
            expires_at=time.time() + 3600,
            scope="read write"
        )

        assert token.access_token == "test-token"
        assert token.token_type == "Bearer"
        assert token.scope == "read write"
        assert token.is_expired is False

    def test_token_expiration(self):
        """Test token expiration check."""
        # Token expired
        token = TokenInfo(
            access_token="test-token",
            token_type="Bearer",
            expires_at=time.time() - 10,  # Already expired
            scope="read"
        )
        assert token.is_expired is True

        # Token about to expire (within 30s buffer)
        token = TokenInfo(
            access_token="test-token",
            token_type="Bearer",
            expires_at=time.time() + 20,  # Within 30s buffer
            scope="read"
        )
        assert token.is_expired is True

        # Token valid
        token = TokenInfo(
            access_token="test-token",
            token_type="Bearer",
            expires_at=time.time() + 100,  # Far from expiring
            scope="read"
        )
        assert token.is_expired is False

    def test_from_response(self):
        """Test creating token info from OAuth response."""
        current_time = time.time()
        with patch("time.time", return_value=current_time):
            response = {
                "access_token": "test-token",
                "token_type": "Bearer",
                "expires_in": 3600,
                "scope": "read write"
            }

            token = TokenInfo.from_response(response)

            assert token.access_token == "test-token"
            assert token.token_type == "Bearer"
            assert token.expires_at == current_time + 3600
            assert token.scope == "read write"

    def test_from_response_defaults(self):
        """Test defaults when optional fields are missing."""
        current_time = time.time()
        with patch("time.time", return_value=current_time):
            response = {
                "access_token": "test-token",
                # token_type missing
                # expires_in missing
                # scope missing
            }

            token = TokenInfo.from_response(response)

            assert token.access_token == "test-token"
            assert token.token_type == "Bearer"  # Default
            assert token.expires_at == current_time + 3600  # Default
            assert token.scope is None


class TestAuthClient:
    """Tests for AuthClient class."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock(spec=ABSettings)
        settings.auth_endpoint = "https://auth.example.com/oauth/token"
        settings.client_id = "test-client"
        settings.client_secret = "test-secret"
        settings.grant_type = "client_credentials"
        settings.timeout = 10.0
        settings.get_auth_scope_string.return_value = "read write"
        return settings

    @pytest.fixture
    def mock_response(self):
        """Create a mock successful token response."""
        mock = MagicMock(spec=httpx.Response)
        mock.status_code = 200
        mock.json.return_value = {
            "access_token": "test-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "read write"
        }
        return mock

    @pytest.fixture
    def mock_client(self, mock_response):
        """Create a mock HTTP client."""
        mock = MagicMock(spec=httpx.Client)
        mock.post.return_value = mock_response
        return mock

    def test_init(self, mock_settings):
        """Test initializing the auth client."""
        client = AuthClient(mock_settings)
        assert client._settings is mock_settings
        assert client._token is None
        assert client._http_client is None

    def test_client_property(self, mock_settings):
        """Test the HTTP client property."""
        with patch("httpx.Client") as mock_httpx:
            client = AuthClient(mock_settings)
            http_client = client._client

            mock_httpx.assert_called_once_with(timeout=mock_settings.timeout)
            assert http_client is mock_httpx.return_value

            # Second call should return the cached client
            http_client2 = client._client
            assert http_client2 is http_client
            assert mock_httpx.call_count == 1

    def test_get_token_fresh(self, mock_settings, mock_client):
        """Test getting a fresh token."""
        with patch("httpx.Client", return_value=mock_client):
            client = AuthClient(mock_settings)
            token = client.get_token()

            mock_client.post.assert_called_once_with(
                mock_settings.auth_endpoint,
                data={
                    "grant_type": mock_settings.grant_type,
                    "client_id": mock_settings.client_id,
                    "client_secret": mock_settings.client_secret,
                    "scope": mock_settings.get_auth_scope_string()
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            assert token == "test-access-token"
            assert client._token is not None
            assert client._token.access_token == "test-access-token"

    def test_get_token_cached(self, mock_settings, mock_client):
        """Test getting a cached token."""
        with patch("httpx.Client", return_value=mock_client):
            client = AuthClient(mock_settings)

            # First call fetches token
            token1 = client.get_token()
            assert token1 == "test-access-token"
            assert mock_client.post.call_count == 1

            # Second call should use cached token
            token2 = client.get_token()
            assert token2 == "test-access-token"
            assert mock_client.post.call_count == 1  # Still just one call

    def test_get_token_force_refresh(self, mock_settings, mock_client):
        """Test forcing token refresh."""
        with patch("httpx.Client", return_value=mock_client):
            client = AuthClient(mock_settings)

            # First call fetches token
            token1 = client.get_token()
            assert token1 == "test-access-token"
            assert mock_client.post.call_count == 1

            # Force refresh should call API again
            token2 = client.get_token(force_refresh=True)
            assert token2 == "test-access-token"
            assert mock_client.post.call_count == 2

    def test_get_token_expired(self, mock_settings, mock_client):
        """Test refreshing an expired token."""
        with patch("httpx.Client", return_value=mock_client):
            client = AuthClient(mock_settings)

            # First call fetches token
            token1 = client.get_token()
            assert token1 == "test-access-token"
            assert mock_client.post.call_count == 1

            # Make token expired
            client._token.expires_at = time.time() - 10

            # Second call should refresh token
            token2 = client.get_token()
            assert token2 == "test-access-token"
            assert mock_client.post.call_count == 2

    def test_fetch_token_timeout(self, mock_settings):
        """Test handling timeout error."""
        with patch("httpx.Client") as mock_httpx:
            mock_client = MagicMock()
            mock_client.post.side_effect = httpx.TimeoutException("Timeout")
            mock_httpx.return_value = mock_client

            client = AuthClient(mock_settings)

            with pytest.raises(TokenError, match="Token request timed out"):
                client.get_token()

    def test_fetch_token_request_error(self, mock_settings):
        """Test handling general request error."""
        with patch("httpx.Client") as mock_httpx:
            mock_client = MagicMock()
            mock_client.post.side_effect = httpx.RequestError("Network error")
            mock_httpx.return_value = mock_client

            client = AuthClient(mock_settings)

            with pytest.raises(TokenError, match="Token request failed: Network error"):
                client.get_token()

    def test_handle_error_response_json(self, mock_settings):
        """Test handling error response with JSON data."""
        with patch("httpx.Client") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": "invalid_client",
                "error_description": "Client authentication failed"
            }

            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client

            client = AuthClient(mock_settings)

            with pytest.raises(TokenError) as excinfo:
                client.get_token()

            assert "Token request failed: invalid_client" in str(excinfo.value)
            assert "Client authentication failed" in str(excinfo.value)

    def test_handle_error_response_non_json(self, mock_settings):
        """Test handling error response with non-JSON data."""
        with patch("httpx.Client") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.json.side_effect = ValueError("Invalid JSON")

            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client

            client = AuthClient(mock_settings)

            with pytest.raises(TokenError) as excinfo:
                client.get_token()

            assert "Token request failed with status 500" in str(excinfo.value)

    def test_handle_invalid_token_response(self, mock_settings):
        """Test handling invalid token response."""
        with patch("httpx.Client") as mock_httpx:
            mock_response = MagicMock()
            mock_response.status_code = 200
            # Missing access_token field
            mock_response.json.return_value = {
                "token_type": "Bearer",
                "expires_in": 3600
            }

            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            mock_httpx.return_value = mock_client

            client = AuthClient(mock_settings)

            with pytest.raises(TokenError, match="Invalid token response"):
                client.get_token()

    def test_get_auth_header(self, mock_settings, mock_client):
        """Test getting the auth header."""
        with patch("httpx.Client", return_value=mock_client):
            client = AuthClient(mock_settings)
            header = client.get_auth_header()

            assert header == {"Authorization": "Bearer test-access-token"}

    def test_validate_credentials_valid(self, mock_settings, mock_client):
        """Test validating valid credentials."""
        with patch("httpx.Client", return_value=mock_client):
            client = AuthClient(mock_settings)
            result = client.validate_credentials()

            assert result is True
            mock_client.post.assert_called_once()

    def test_validate_credentials_invalid(self, mock_settings):
        """Test validating invalid credentials."""
        # Set up the patch so the fetch_token method raises TokenError
        with patch.object(AuthClient, "_fetch_token", side_effect=TokenError("Invalid client")):
            client = AuthClient(mock_settings)
            with pytest.raises(AuthenticationError, match="Invalid credentials: Invalid client"):
                client.validate_credentials()

    def test_close(self, mock_settings):
        """Test closing the client."""
        with patch("httpx.Client") as mock_httpx:
            mock_client = MagicMock()
            mock_httpx.return_value = mock_client

            client = AuthClient(mock_settings)

            # Access the client to create it
            _ = client._client
            assert client._http_client is not None

            # Close the client
            client.close()

            mock_client.close.assert_called_once()
            assert client._http_client is None

    def test_context_manager(self, mock_settings):
        """Test context manager behavior."""
        with patch.object(AuthClient, "close") as mock_close:
            with AuthClient(mock_settings) as client:
                assert isinstance(client, AuthClient)

            mock_close.assert_called_once()
