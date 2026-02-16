"""Configuration settings for ab-cli using Pydantic."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ABSettings(BaseSettings):
    """Agent Builder CLI configuration settings.

    Settings can be loaded from:
    1. Environment variables (prefixed with AB_)
    2. A .env file
    3. A YAML configuration file (via loader)

    Environment variables take precedence over file-based configuration.
    """

    model_config = SettingsConfigDict(
        env_prefix="AB_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Required identifiers (HxP tenant info)
    environment_id: Annotated[
        str,
        Field(
            description="HxP environment ID for the target tenant",
            min_length=1,
        ),
    ]

    # Authentication
    client_id: Annotated[
        str,
        Field(
            description="OAuth2 client ID for authentication",
            min_length=1,
        ),
    ]
    client_secret: Annotated[
        str,
        Field(
            description="OAuth2 client secret for authentication",
            min_length=1,
        ),
    ]

    # API Endpoints
    api_endpoint: Annotated[
        str,
        Field(
            default="https://api.agentbuilder.experience.hyland.com/",
            description="Agent Builder API base URL",
        ),
    ]
    auth_endpoint: Annotated[
        str,
        Field(
            default="https://auth.iam.experience.hyland.com/idp/connect/token",
            description="OAuth2 token endpoint URL",
        ),
    ]
    auth_scope: Annotated[
        list[str],
        Field(
            default=["hxp"],
            description="OAuth2 scopes to request",
        ),
    ]
    grant_type: Annotated[
        str,
        Field(
            default="client_credentials",
            description="OAuth2 grant type (e.g., client_credentials, urn:hyland:params:oauth:grant-type:api-credentials)",
        ),
    ]

    # Processing settings
    timeout: Annotated[
        float,
        Field(
            default=30.0,
            ge=1.0,
            le=300.0,
            description="HTTP request timeout in seconds",
        ),
    ]
    retry_backoff: Annotated[
        float,
        Field(
            default=2.0,
            ge=1.0,
            le=10.0,
            description="Exponential backoff multiplier for retries",
        ),
    ]
    max_retries: Annotated[
        int,
        Field(
            default=3,
            ge=0,
            le=10,
            description="Maximum number of retry attempts",
        ),
    ]

    # Output preferences
    default_output_format: Annotated[
        str,
        Field(
            default="table",
            description="Default output format (table, json, yaml)",
        ),
    ]

    # Audit settings
    record_updates: Annotated[
        bool,
        Field(
            default=False,
            description="Whether to save API payloads for create/update operations",
        ),
    ]

    # Pagination Configuration
    class PaginationSettings(BaseSettings):
        """Pagination-specific settings."""

        max_filter_pages: Annotated[
            int,
            Field(
                default=10,
                ge=1,
                le=100,
                description="Maximum server pages to fetch when using client-side filters",
            ),
        ]

    # UI Configuration
    class UISettings(BaseSettings):
        """UI-specific settings."""

        data_provider: Annotated[
            str,
            Field(
                default="cli",
                description="Data provider to use (cli or mock)",
            ),
        ]

        mock_data_dir: Annotated[
            str | None,
            Field(
                default=None,
                description="Directory containing mock data files",
            ),
        ]

        @field_validator("data_provider")
        @classmethod
        def validate_data_provider(cls, v: str) -> str:
            """Validate data provider is one of the allowed values.

            Args:
                v: The data provider value.

            Returns:
                The validated data provider in lowercase.

            Raises:
                ValueError: If the data provider is not allowed.
            """
            allowed = {"cli", "mock"}
            v_lower = v.lower()
            if v_lower not in allowed:
                raise ValueError(f"Data provider must be one of {allowed}, got: {v}")
            return v_lower

    pagination: Annotated[
        PaginationSettings | None,
        Field(
            default=None,
            description="Pagination configuration settings",
        ),
    ] = None

    ui: Annotated[
        UISettings | None,
        Field(
            default=None,
            description="UI configuration settings",
        ),
    ] = None

    @field_validator("api_endpoint", "auth_endpoint")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that endpoints are valid URLs.

        Args:
            v: The URL value to validate.

        Returns:
            The validated URL with trailing slash ensured for api_endpoint.

        Raises:
            ValueError: If the URL is invalid.
        """
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"URL must start with http:// or https://: {v}")
        return v

    @field_validator("api_endpoint")
    @classmethod
    def ensure_trailing_slash(cls, v: str) -> str:
        """Ensure API endpoint has a trailing slash.

        Args:
            v: The API endpoint URL.

        Returns:
            URL with trailing slash.
        """
        return v if v.endswith("/") else f"{v}/"

    @field_validator("default_output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        """Validate output format is one of the allowed values.

        Args:
            v: The output format value.

        Returns:
            The validated output format in lowercase.

        Raises:
            ValueError: If the format is not allowed.
        """
        allowed = {"table", "json", "yaml"}
        v_lower = v.lower()
        if v_lower not in allowed:
            raise ValueError(f"Output format must be one of {allowed}, got: {v}")
        return v_lower

    def get_auth_scope_string(self) -> str:
        """Get auth scopes as a space-separated string.

        Returns:
            Space-separated scope string for OAuth2 requests.
        """
        return " ".join(self.auth_scope)


def get_config_summary(settings: ABSettings) -> dict[str, str]:
    """Get a summary of configuration values with secrets redacted.

    Args:
        settings: The settings object to summarize.

    Returns:
        Dictionary of setting names to their (possibly redacted) values.
    """
    return {
        "environment_id": settings.environment_id,
        "api_endpoint": settings.api_endpoint,
        "auth_endpoint": settings.auth_endpoint,
        "client_id": _redact(settings.client_id),
        "client_secret": "********",
        "auth_scope": ", ".join(settings.auth_scope),
        "timeout": f"{settings.timeout}s",
        "max_retries": str(settings.max_retries),
        "default_output_format": settings.default_output_format,
        "record_updates": str(settings.record_updates),
        "ui.data_provider": settings.ui.data_provider if settings.ui else "cli",
    }


def _redact(value: str, visible_chars: int = 8) -> str:
    """Redact a sensitive value, showing only first and last few characters.

    Args:
        value: The value to redact.
        visible_chars: Total visible characters (split between start and end).

    Returns:
        Redacted string like "abc1...xyz9".
    """
    if len(value) <= visible_chars:
        return "*" * len(value)

    half = visible_chars // 2
    return f"{value[:half]}...{value[-half:]}"
