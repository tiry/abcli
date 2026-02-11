"""Tests for configuration settings."""

import pytest
from pydantic import ValidationError

from ab_cli.config.settings import ABSettings, _redact, get_config_summary


class TestABSettings:
    """Tests for ABSettings model."""

    def test_valid_settings(self) -> None:
        """Test creating settings with valid values."""
        settings = ABSettings(
            environment_id="test-env-id",
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        assert settings.environment_id == "test-env-id"
        assert settings.client_id == "test-client-id"
        assert settings.client_secret == "test-client-secret"

    def test_default_values(self) -> None:
        """Test default values are applied."""
        settings = ABSettings(
            environment_id="test-env-id",
            client_id="test-client-id",
            client_secret="test-client-secret",
        )

        assert settings.api_endpoint.endswith("/")
        assert settings.timeout == 30.0
        assert settings.max_retries == 3
        assert settings.default_output_format == "table"
        assert settings.auth_scope == ["hxp"]

    def test_missing_required_fields(self) -> None:
        """Test validation error for missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            ABSettings()  # type: ignore[call-arg]

        errors = exc_info.value.errors()
        assert len(errors) >= 3
        # Check that required fields are reported as missing
        error_locs = {e["loc"][0] for e in errors}
        assert "environment_id" in error_locs
        assert "client_id" in error_locs
        assert "client_secret" in error_locs

    def test_api_endpoint_trailing_slash(self) -> None:
        """Test that API endpoint gets trailing slash added."""
        settings = ABSettings(
            environment_id="test",
            client_id="test",
            client_secret="test",
            api_endpoint="https://api.example.com",
        )

        assert settings.api_endpoint == "https://api.example.com/"

    def test_api_endpoint_keeps_existing_slash(self) -> None:
        """Test that existing trailing slash is preserved."""
        settings = ABSettings(
            environment_id="test",
            client_id="test",
            client_secret="test",
            api_endpoint="https://api.example.com/",
        )

        assert settings.api_endpoint == "https://api.example.com/"

    def test_invalid_url(self) -> None:
        """Test validation error for invalid URL."""
        with pytest.raises(ValidationError) as exc_info:
            ABSettings(
                environment_id="test",
                client_id="test",
                client_secret="test",
                api_endpoint="not-a-url",
            )

        errors = exc_info.value.errors()
        assert any("http" in str(e["msg"]).lower() for e in errors)

    def test_invalid_output_format(self) -> None:
        """Test validation error for invalid output format."""
        with pytest.raises(ValidationError) as exc_info:
            ABSettings(
                environment_id="test",
                client_id="test",
                client_secret="test",
                default_output_format="invalid",
            )

        errors = exc_info.value.errors()
        assert any("output format" in str(e["msg"]).lower() for e in errors)

    def test_valid_output_formats(self) -> None:
        """Test all valid output formats."""
        for fmt in ["table", "json", "yaml", "TABLE", "JSON", "YAML"]:
            settings = ABSettings(
                environment_id="test",
                client_id="test",
                client_secret="test",
                default_output_format=fmt,
            )
            assert settings.default_output_format == fmt.lower()

    def test_get_auth_scope_string(self) -> None:
        """Test auth scope string generation."""
        settings = ABSettings(
            environment_id="test",
            client_id="test",
            client_secret="test",
            auth_scope=["hxp", "openid"],
        )

        assert settings.get_auth_scope_string() == "hxp openid"

    def test_timeout_bounds(self) -> None:
        """Test timeout validation bounds."""
        # Too low
        with pytest.raises(ValidationError):
            ABSettings(
                environment_id="test",
                client_id="test",
                client_secret="test",
                timeout=0.5,
            )

        # Too high
        with pytest.raises(ValidationError):
            ABSettings(
                environment_id="test",
                client_id="test",
                client_secret="test",
                timeout=500.0,
            )


class TestConfigSummary:
    """Tests for config summary functions."""

    def test_get_config_summary(self) -> None:
        """Test config summary generation."""
        settings = ABSettings(
            environment_id="test-env-123",
            client_id="client-abc-xyz-123",
            client_secret="secret-value",
        )

        summary = get_config_summary(settings)

        assert summary["environment_id"] == "test-env-123"
        assert "..." in summary["client_id"]  # Redacted
        assert summary["client_secret"] == "********"
        assert "api_endpoint" in summary

    def test_redact_short_value(self) -> None:
        """Test redaction of short values."""
        assert _redact("short") == "*****"

    def test_redact_long_value(self) -> None:
        """Test redaction of long values."""
        result = _redact("this-is-a-long-secret-value")
        assert result.startswith("this")
        assert result.endswith("alue")
        assert "..." in result
