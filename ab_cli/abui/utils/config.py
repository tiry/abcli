"""Configuration utilities for the Agent Builder UI."""

from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from ab_cli.config import find_config_file as find_cli_config


class UIConfig(BaseModel):
    """UI configuration settings."""

    theme: str = Field(default="light", description="UI theme (light or dark)")
    show_logo: bool = Field(default=True, description="Whether to show the logo in the UI")


class Config(BaseModel):
    """Configuration for the Agent Builder UI."""

    api_endpoint: str
    auth_endpoint: str
    environment_id: str
    client_id: str
    client_secret: str
    ui: UIConfig | None = Field(default_factory=UIConfig)

    # Store the path to the config file that was used
    config_path: str | None = None


def find_config_file() -> Path | None:
    """Find the configuration file in standard locations.

    Uses the same config file as the CLI.
    """
    return find_cli_config()


def load_config(config_path: str | Path | None = None) -> Config:
    """Load configuration from file or use defaults.

    Args:
        config_path: Path to config file, if None will search for one

    Returns:
        Config object with loaded configuration

    Raises:
        ValueError: If config file not found or invalid
    """
    if config_path is None:
        config_path = find_config_file()
        if config_path is None:
            raise ValueError("No configuration file found")

    if isinstance(config_path, str):
        config_path = Path(config_path)

    # Read the configuration file
    try:
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
    except Exception as e:
        raise ValueError(f"Failed to load configuration file: {e}")

    # Convert to Pydantic model
    try:
        config = Config(**config_data)
        # Store the config_path for future reference
        config.config_path = str(config_path)
        return config
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")
