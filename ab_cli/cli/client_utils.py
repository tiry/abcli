"""Shared utility functions for CLI commands."""

from __future__ import annotations

import sys

from rich.console import Console

from ab_cli.api.client import AgentBuilderClient
from ab_cli.config.exceptions import ConfigurationError
from ab_cli.config.loader import find_config_file, load_config

error_console = Console(stderr=True)


def get_client_with_error_handling(config_path: str | None = None) -> AgentBuilderClient:
    """Get an authenticated API client with user-friendly error handling.

    Args:
        config_path: Optional path to config file. If not provided, will search standard locations.

    Returns:
        AgentBuilderClient instance

    Raises:
        SystemExit: If config file not found or invalid (exits with code 1)
    """
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
        settings = load_config(config_file)
    except ConfigurationError as e:
        error_console.print(f"[red]✗ Configuration error:[/red] {e}")
        error_console.print()
        error_console.print("To fix your configuration, run:")
        error_console.print("  [cyan]ab configure[/cyan]")
        error_console.print()
        sys.exit(1)

    return AgentBuilderClient(settings)
