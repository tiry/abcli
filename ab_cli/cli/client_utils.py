"""Shared utility functions for CLI commands."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from rich.console import Console

from ab_cli.api.client import AgentBuilderClient
from ab_cli.config.exceptions import ConfigurationError
from ab_cli.config.loader import find_config_file, load_config, load_config_with_profile

if TYPE_CHECKING:
    from ab_cli.config.settings import ABSettings

error_console = Console(stderr=True)


def get_client_with_error_handling(
    config_path: str | None = None,
    profile: str | None = None,
    settings: ABSettings | None = None,
) -> AgentBuilderClient:
    """Get an authenticated API client with user-friendly error handling.

    Args:
        config_path: Optional path to config file. If not provided, will search standard locations.
        profile: Optional profile name to use from config file.
        settings: Optional pre-loaded settings object (takes precedence over loading from file).

    Returns:
        AgentBuilderClient instance

    Raises:
        SystemExit: If config file not found or invalid (exits with code 1)
    """
    # If settings already provided, use them
    if settings:
        return AgentBuilderClient(settings)

    config_file = config_path or find_config_file()

    if not config_file:
        error_console.print("[red]✗ No configuration file found[/red]")
        error_console.print()
        error_console.print("To create a configuration file, run:")
        error_console.print("  [cyan]ab configure[/cyan]")
        error_console.print()
        error_console.print("Searched locations:")
        error_console.print("  • config.yaml (current directory)")
        error_console.print("  • ab-cli.yaml (current directory)")
        error_console.print("  • ~/.ab-cli/config.yaml")
        error_console.print()
        sys.exit(1)

    try:
        # Load config with profile support if profile specified
        if profile:
            settings = load_config_with_profile(config_file, profile=profile)
        else:
            settings = load_config(config_file)
    except ConfigurationError as e:
        error_console.print(f"[red]✗ Configuration error:[/red] {e}")
        error_console.print()
        error_console.print("To fix your configuration, run:")
        error_console.print("  [cyan]ab configure[/cyan]")
        error_console.print()
        sys.exit(1)
    except ValueError as e:
        # Profile not found
        error_console.print(f"[red]✗ Profile error:[/red] {e}")
        error_console.print()
        error_console.print("To see available profiles, run:")
        error_console.print("  [cyan]ab profiles list[/cyan]")
        error_console.print()
        sys.exit(1)

    return AgentBuilderClient(settings)
