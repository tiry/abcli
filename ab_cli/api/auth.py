"""OAuth2 client credentials authentication for ab-cli."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx

from ab_cli.api.exceptions import AuthenticationError, TokenError
from ab_cli.config.settings import ABSettings


@dataclass
class TokenInfo:
    """OAuth2 access token information."""

    access_token: str
    token_type: str
    expires_at: float  # Unix timestamp when token expires
    scope: str | None = None

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired (with 30s buffer)."""
        return time.time() >= (self.expires_at - 30)

    @classmethod
    def from_response(cls, data: dict[str, Any]) -> TokenInfo:
        """Create TokenInfo from OAuth2 token response.

        Args:
            data: Token response data containing access_token, expires_in, etc.

        Returns:
            TokenInfo instance.
        """
        expires_in = data.get("expires_in", 3600)
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_at=time.time() + expires_in,
            scope=data.get("scope"),
        )


class AuthClient:
    """OAuth2 client credentials authentication client.

    Manages token acquisition and caching for API authentication.
    """

    def __init__(self, settings: ABSettings) -> None:
        """Initialize the auth client.

        Args:
            settings: Application settings containing auth configuration.
        """
        self._settings = settings
        self._token: TokenInfo | None = None
        self._http_client: httpx.Client | None = None

    @property
    def _client(self) -> httpx.Client:
        """Get or create the HTTP client for token requests."""
        if self._http_client is None:
            self._http_client = httpx.Client(timeout=self._settings.timeout)
        return self._http_client

    def get_token(self, force_refresh: bool = False) -> str:
        """Get a valid access token, refreshing if necessary.

        Args:
            force_refresh: If True, always fetch a new token.

        Returns:
            Valid access token string.

        Raises:
            TokenError: If token acquisition fails.
        """
        if not force_refresh and self._token and not self._token.is_expired:
            return self._token.access_token

        self._token = self._fetch_token()
        return self._token.access_token

    def _fetch_token(self) -> TokenInfo:
        """Fetch a new access token from the auth server.

        Returns:
            TokenInfo with the new token.

        Raises:
            TokenError: If the token request fails.
        """
        data = {
            "grant_type": self._settings.grant_type,
            "client_id": self._settings.client_id,
            "client_secret": self._settings.client_secret,
            "scope": self._settings.get_auth_scope_string(),
        }

        try:
            response = self._client.post(
                self._settings.auth_endpoint,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.TimeoutException:
            raise TokenError("Token request timed out")
        except httpx.RequestError as e:
            raise TokenError(f"Token request failed: {e}")

        if response.status_code != 200:
            self._handle_error_response(response)

        try:
            token_data = response.json()
            return TokenInfo.from_response(token_data)
        except (ValueError, KeyError) as e:
            raise TokenError(f"Invalid token response: {e}")

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses from the auth server.

        Args:
            response: The error response from the auth server.

        Raises:
            TokenError: With appropriate error details.
        """
        try:
            error_data = response.json()
            error_code = error_data.get("error", "unknown_error")
            error_description = error_data.get("error_description", "")
            message = f"Token request failed: {error_code}"
            if error_description:
                message += f" - {error_description}"
        except ValueError:
            error_code = None
            error_description = None
            message = f"Token request failed with status {response.status_code}"

        raise TokenError(message, error_code=error_code, error_description=error_description)

    def get_auth_header(self) -> dict[str, str]:
        """Get the Authorization header for API requests.

        Returns:
            Dictionary with Authorization header.
        """
        token = self.get_token()
        return {"Authorization": f"Bearer {token}"}

    def validate_credentials(self) -> bool:
        """Validate that the credentials are correct.

        Returns:
            True if credentials are valid.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        try:
            self.get_token(force_refresh=True)
            return True
        except TokenError as e:
            raise AuthenticationError(f"Invalid credentials: {e}")

    def close(self) -> None:
        """Close the HTTP client."""
        if self._http_client is not None:
            self._http_client.close()
            self._http_client = None

    def __enter__(self) -> AuthClient:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
