"""API exceptions for ab-cli."""

from __future__ import annotations

from typing import Any


class APIError(Exception):
    """Base exception for API-related errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize API error.

        Args:
            message: Error description.
            status_code: HTTP status code if available.
        """
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        """Initialize authentication error.

        Args:
            message: Error description.
        """
        super().__init__(message, status_code=401)


class TokenError(AuthenticationError):
    """Raised when there is an issue with the OAuth2 token."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        error_description: str | None = None,
    ) -> None:
        """Initialize token error.

        Args:
            message: Error description.
            error_code: OAuth2 error code if available.
            error_description: OAuth2 error description if available.
        """
        self.error_code = error_code
        self.error_description = error_description
        super().__init__(message)


class AuthorizationError(APIError):
    """Raised when the user is not authorized to perform an action."""

    def __init__(self, message: str = "Not authorized") -> None:
        """Initialize authorization error.

        Args:
            message: Error description.
        """
        super().__init__(message, status_code=403)


class NotFoundError(APIError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        """Initialize not found error.

        Args:
            resource_type: Type of resource (e.g., "agent", "version").
            resource_id: ID of the resource.
        """
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} not found: {resource_id}", status_code=404)


class ValidationError(APIError):
    """Raised when the API returns a validation error."""

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None) -> None:
        """Initialize validation error.

        Args:
            message: Error description.
            errors: List of validation error details if available.
        """
        self.errors = errors or []
        super().__init__(message, status_code=422)


class RateLimitError(APIError):
    """Raised when the API rate limit is exceeded."""

    def __init__(self, retry_after: float | None = None) -> None:
        """Initialize rate limit error.

        Args:
            retry_after: Seconds to wait before retrying, if provided by API.
        """
        self.retry_after = retry_after
        message = "Rate limit exceeded"
        if retry_after:
            message += f", retry after {retry_after}s"
        super().__init__(message, status_code=429)


class ServerError(APIError):
    """Raised when the API returns a server error (5xx)."""

    def __init__(self, message: str = "Server error", status_code: int = 500) -> None:
        """Initialize server error.

        Args:
            message: Error description.
            status_code: HTTP status code (5xx).
        """
        super().__init__(message, status_code=status_code)


class ConnectionError(APIError):
    """Raised when unable to connect to the API."""

    def __init__(self, message: str = "Connection failed") -> None:
        """Initialize connection error.

        Args:
            message: Error description.
        """
        super().__init__(message)


class TimeoutError(APIError):
    """Raised when an API request times out."""

    def __init__(self, timeout: float) -> None:
        """Initialize timeout error.

        Args:
            timeout: The timeout value that was exceeded.
        """
        self.timeout = timeout
        super().__init__(f"Request timed out after {timeout}s")
