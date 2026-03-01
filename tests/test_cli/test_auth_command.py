"""Tests for auth command."""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from ab_cli.api.auth import TokenInfo
from ab_cli.api.exceptions import AuthenticationError, TokenError
from ab_cli.cli.auth import auth


@pytest.fixture
def mock_auth_client():
    """Mock AuthClient for testing."""
    with patch("ab_cli.cli.auth.AuthClient") as mock_client_class:
        mock_client = MagicMock()
        mock_token_info = TokenInfo(
            access_token="test_token_123",
            token_type="Bearer",
            expires_at=1000000000.0 + 3600,  # 1 hour from now
            scope="read write",
        )
        mock_client._token = mock_token_info
        mock_client.get_token.return_value = "test_token_123"
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_config_loading():
    """Mock configuration loading."""
    with patch("ab_cli.cli.auth.find_config_file") as mock_find, \
         patch("ab_cli.cli.auth.load_config") as mock_load:
        mock_find.return_value = "/fake/config.yaml"
        mock_settings = MagicMock()
        mock_settings.api_endpoint = "https://api.example.com"
        mock_settings.environment_id = "test-env-123"
        mock_load.return_value = mock_settings
        yield mock_settings


class TestAuthCommand:
    """Tests for auth command."""

    def test_default_curl_get(self, mock_auth_client, mock_config_loading):  # noqa: ARG002
        """Test default behavior (curl + GET)."""
        runner = CliRunner()
        result = runner.invoke(auth, [], obj={"config_path": "/fake/config.yaml", "profile": None})

        assert result.exit_code == 0
        assert "✓ Authentication successful!" in result.output
        assert "test_token_123" in result.output
        assert "Example curl command (GET - List Agents):" in result.output
        assert "curl -X GET" in result.output
        # GET requests don't include environment_id in URL - single line command
        assert 'curl -X GET "https://api.example.com/v1/agents' in result.output
        assert "/environments/" not in result.output

    def test_curl_post(self, mock_auth_client, mock_config_loading):  # noqa: ARG002
        """Test curl with POST example."""
        runner = CliRunner()
        result = runner.invoke(
            auth, ["--post"], obj={"config_path": "/fake/config.yaml", "profile": None}
        )

        assert result.exit_code == 0
        assert "Example curl command (POST - Invoke Agent):" in result.output
        assert "curl -X POST" in result.output
        assert "<agent-id>" in result.output
        assert "versions/latest/invoke" in result.output
        assert '"messages":' in result.output
        assert '"role": "user"' in result.output
        assert '"content": "Hello, agent!"' in result.output
        # POST requests don't include environment_id in URL
        assert "/environments/" not in result.output

    def test_wget_get(self, mock_auth_client, mock_config_loading):  # noqa: ARG002
        """Test wget with GET example."""
        runner = CliRunner()
        result = runner.invoke(
            auth, ["--wget"], obj={"config_path": "/fake/config.yaml", "profile": None}
        )

        assert result.exit_code == 0
        assert "Example wget command (GET - List Agents):" in result.output
        assert "wget -O -" in result.output
        assert "--header=" in result.output
        # GET requests don't include environment_id in URL
        assert "https://api.example.com/v1/agents" in result.output
        assert "/environments/" not in result.output

    def test_wget_post(self, mock_auth_client, mock_config_loading):  # noqa: ARG002
        """Test wget with POST example."""
        runner = CliRunner()
        result = runner.invoke(
            auth, ["--wget", "--post"], obj={"config_path": "/fake/config.yaml", "profile": None}
        )

        assert result.exit_code == 0
        assert "Example wget command (POST - Invoke Agent):" in result.output
        assert "wget -O -" in result.output
        assert "--header=" in result.output
        assert "--post-data=" in result.output
        assert "<agent-id>" in result.output
        assert "versions/latest/invoke" in result.output
        # POST requests don't include environment_id in URL
        assert "/environments/" not in result.output

    def test_token_expiry_display(self, mock_auth_client, mock_config_loading):  # noqa: ARG002
        """Test token expiry information display."""
        runner = CliRunner()
        result = runner.invoke(auth, [], obj={"config_path": "/fake/config.yaml", "profile": None})

        assert result.exit_code == 0
        assert "Token Details:" in result.output
        assert "Expires in:" in result.output
        assert "Expires at:" in result.output

    def test_auth_failure(self, mock_config_loading):  # noqa: ARG002
        """Test handling of authentication failure."""
        with patch("ab_cli.cli.auth.AuthClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_token.side_effect = AuthenticationError("Invalid credentials")
            mock_client_class.return_value = mock_client

            runner = CliRunner()
            result = runner.invoke(
                auth, [], obj={"config_path": "/fake/config.yaml", "profile": None}
            )

            assert result.exit_code == 1
            assert "✗ Authentication failed:" in result.output
            assert "Invalid credentials" in result.output

    def test_no_config_file(self):
        """Test error when no config file is found."""
        with patch("ab_cli.cli.auth.find_config_file") as mock_find:
            mock_find.return_value = None

            runner = CliRunner()
            result = runner.invoke(auth, [], obj={"config_path": None, "profile": None})

            assert result.exit_code == 1
            assert "✗ No configuration file found" in result.output
            assert "ab configure" in result.output

    def test_with_profile(self, mock_auth_client):  # noqa: ARG002
        """Test auth command with profile."""
        with patch("ab_cli.cli.auth.find_config_file") as mock_find, \
             patch("ab_cli.cli.auth.load_config_with_profile") as mock_load_profile:
            mock_find.return_value = "/fake/config.yaml"
            mock_settings = MagicMock()
            mock_settings.api_endpoint = "https://staging.example.com"
            mock_settings.environment_id = "staging-env"
            mock_load_profile.return_value = mock_settings

            runner = CliRunner()
            result = runner.invoke(
                auth, [], obj={"config_path": "/fake/config.yaml", "profile": "staging"}
            )

            assert result.exit_code == 0
            assert "https://staging.example.com" in result.output
            # GET requests don't include environment_id in URL
            assert "staging.example.com/v1/agents" in result.output
            mock_load_profile.assert_called_once_with("/fake/config.yaml", profile="staging")

    def test_token_error(self, mock_config_loading):  # noqa: ARG002
        """Test handling of token error."""
        with patch("ab_cli.cli.auth.AuthClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client.get_token.side_effect = TokenError("Token request failed")
            mock_client_class.return_value = mock_client

            runner = CliRunner()
            result = runner.invoke(
                auth, [], obj={"config_path": "/fake/config.yaml", "profile": None}
            )

            assert result.exit_code == 1
            assert "✗ Authentication failed:" in result.output
            assert "Token request failed" in result.output

    def test_url_formatting(self, mock_auth_client):  # noqa: ARG002
        """Test that URLs are correctly formatted (trailing slashes removed)."""
        with patch("ab_cli.cli.auth.find_config_file") as mock_find, \
             patch("ab_cli.cli.auth.load_config") as mock_load:
            mock_find.return_value = "/fake/config.yaml"
            mock_settings = MagicMock()
            mock_settings.api_endpoint = "https://api.example.com/"  # With trailing slash
            mock_settings.environment_id = "test-env"
            mock_load.return_value = mock_settings

            runner = CliRunner()
            result = runner.invoke(
                auth, [], obj={"config_path": "/fake/config.yaml", "profile": None}
            )

            assert result.exit_code == 0
            # Should have single slash, not double (GET uses /v1/agents without environment)
            assert "https://api.example.com/v1/agents" in result.output
            assert "https://api.example.com//v1" not in result.output
