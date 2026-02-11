"""Configuration exceptions for ab-cli."""

from __future__ import annotations


class ConfigurationError(Exception):
    """Base exception for configuration errors.

    Raised when there are issues with loading, parsing, or validating
    the configuration file or environment variables.
    """

    def __init__(self, message: str, field: str | None = None) -> None:
        """Initialize configuration error.

        Args:
            message: Error description.
            field: Optional field name that caused the error.
        """
        self.field = field
        super().__init__(message)


class ConfigFileNotFoundError(ConfigurationError):
    """Raised when a configuration file cannot be found."""

    def __init__(self, path: str) -> None:
        """Initialize with the missing file path.

        Args:
            path: Path to the missing configuration file.
        """
        self.path = path
        super().__init__(f"Configuration file not found: {path}")


class ConfigFileParseError(ConfigurationError):
    """Raised when a configuration file cannot be parsed."""

    def __init__(self, path: str, reason: str) -> None:
        """Initialize with the file path and parse error reason.

        Args:
            path: Path to the configuration file.
            reason: Description of the parse error.
        """
        self.path = path
        self.reason = reason
        super().__init__(f"Failed to parse configuration file '{path}': {reason}")


class ConfigValidationError(ConfigurationError):
    """Raised when configuration validation fails."""

    def __init__(self, errors: list[str]) -> None:
        """Initialize with a list of validation errors.

        Args:
            errors: List of validation error messages.
        """
        self.errors = errors
        message = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        super().__init__(message)
