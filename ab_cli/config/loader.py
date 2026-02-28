"""Configuration loader for ab-cli - loads settings from YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from ab_cli.config.exceptions import (
    ConfigFileNotFoundError,
    ConfigFileParseError,
    ConfigValidationError,
)
from ab_cli.config.settings import ABSettings


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    """Load and parse a YAML configuration file.

    Args:
        path: Path to the YAML file.

    Returns:
        Dictionary of configuration values.

    Raises:
        ConfigFileNotFoundError: If the file does not exist.
        ConfigFileParseError: If the file cannot be parsed as YAML.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise ConfigFileNotFoundError(str(file_path))

    try:
        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigFileParseError(str(file_path), str(e))

    # Handle empty files
    if data is None:
        return {}

    if not isinstance(data, dict):
        raise ConfigFileParseError(str(file_path), "Root element must be a mapping")

    return data


def load_config(config_path: str | Path | None = None) -> ABSettings:
    """Load configuration from a YAML file and/or environment variables.

    The loading order (later overrides earlier):
    1. Default values from ABSettings
    2. YAML configuration file (if provided)
    3. Environment variables (AB_* prefix)

    Args:
        config_path: Optional path to a YAML configuration file.

    Returns:
        Validated ABSettings instance.

    Raises:
        ConfigFileNotFoundError: If the specified file does not exist.
        ConfigFileParseError: If the file cannot be parsed.
        ConfigValidationError: If the configuration is invalid.
    """
    config_data: dict[str, Any] = {}

    # Load from YAML file if provided
    if config_path is not None:
        config_data = load_yaml_file(config_path)

    # Create settings - Pydantic will merge with environment variables
    try:
        settings = ABSettings(**config_data)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            loc = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"{loc}: {msg}")
        raise ConfigValidationError(errors)

    return settings


def validate_config_file(config_path: str | Path) -> tuple[ABSettings, list[str]]:
    """Validate a configuration file and return settings with any warnings.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Tuple of (settings, warnings) where warnings is a list of
        non-fatal warning messages.

    Raises:
        ConfigFileNotFoundError: If the file does not exist.
        ConfigFileParseError: If the file cannot be parsed.
        ConfigValidationError: If the configuration is invalid.
    """
    warnings: list[str] = []

    # Load and validate
    settings = load_config(config_path)

    # Check for potential issues (non-fatal warnings)
    if settings.timeout < 10.0:
        warnings.append(f"Low timeout value ({settings.timeout}s) may cause issues with slow APIs")

    if settings.max_retries == 0:
        warnings.append("Retries disabled (max_retries=0), transient errors will not be retried")

    if "localhost" in settings.api_endpoint or "127.0.0.1" in settings.api_endpoint:
        warnings.append("Using localhost API endpoint - ensure local server is running")

    return settings, warnings


def find_config_file() -> Path | None:
    """Search for a configuration file in standard locations.

    Searches in order:
    1. ./config.yaml
    2. ./ab-cli.yaml
    3. ~/.ab-cli/config.yaml

    Returns:
        Path to the first found configuration file, or None if not found.
    """
    search_paths = [
        Path("config.yaml"),
        Path("ab-cli.yaml"),
        Path.home() / ".ab-cli" / "config.yaml",
    ]

    for path in search_paths:
        if path.exists():
            return path

    return None


def deep_merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries, with override values taking precedence.

    Args:
        base: Base dictionary with default values.
        override: Dictionary with values to override.

    Returns:
        New dictionary with merged values.
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = deep_merge_dicts(result[key], value)
        else:
            # Override the value
            result[key] = value

    return result


def get_available_profiles(config_path: str | Path) -> list[str]:
    """Get list of available profile names from a configuration file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        List of profile names, or empty list if no profiles defined.

    Raises:
        ConfigFileNotFoundError: If the file does not exist.
        ConfigFileParseError: If the file cannot be parsed.
    """
    config_data = load_yaml_file(config_path)
    profiles = config_data.get("profiles", {})

    if not isinstance(profiles, dict):
        return []

    return list(profiles.keys())


def load_config_with_profile(
    config_path: str | Path | None = None, profile: str | None = None
) -> ABSettings:
    """Load configuration with optional profile support.

    Args:
        config_path: Optional path to a YAML configuration file.
        profile: Optional profile name to apply.

    Returns:
        Validated ABSettings instance with profile applied.

    Raises:
        ConfigFileNotFoundError: If the specified file does not exist.
        ConfigFileParseError: If the file cannot be parsed.
        ConfigValidationError: If the configuration is invalid.
        ValueError: If the specified profile does not exist.
    """
    config_data: dict[str, Any] = {}

    # Load from YAML file if provided
    if config_path is not None:
        config_data = load_yaml_file(config_path)

    # Apply profile if specified
    if profile:
        profiles = config_data.get("profiles", {})

        if not isinstance(profiles, dict):
            raise ValueError("Invalid profiles section in configuration")

        if profile not in profiles:
            available = list(profiles.keys())
            raise ValueError(
                f"Profile '{profile}' not found. Available profiles: {', '.join(available) if available else '(none)'}"
            )

        profile_data = profiles[profile]
        if not isinstance(profile_data, dict):
            raise ValueError(f"Profile '{profile}' must be a dictionary")

        # Deep merge profile overrides into base config
        # Remove 'profiles' key from base to avoid including it in merge
        base_config = {k: v for k, v in config_data.items() if k != "profiles"}
        config_data = deep_merge_dicts(base_config, profile_data)

    # Remove 'profiles' section before creating settings (not a valid field)
    config_data_for_settings = {k: v for k, v in config_data.items() if k != "profiles"}

    # Create settings - Pydantic will merge with environment variables
    try:
        settings = ABSettings(**config_data_for_settings)
    except ValidationError as e:
        errors = []
        for error in e.errors():
            loc = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"{loc}: {msg}")
        raise ConfigValidationError(errors)

    return settings
