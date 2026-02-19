"""Interactive configuration wizard for ab-cli."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click
import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt

from ab_cli.config import find_config_file, load_config, validate_config_file
from ab_cli.config.exceptions import ConfigurationError

# Rich console for formatted output
console = Console()
error_console = Console(stderr=True)

# Default configuration values
DEFAULTS = {
    "grant_type": "client_credentials",
    "auth_scope": ["hxp"],
    "api_endpoint": "https://api.agentbuilder.experience.hyland.com/",
    "auth_endpoint": "https://auth.iam.experience.hyland.com/idp/connect/token",
}


def prompt_for_required_fields(existing_config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Prompt user for required configuration fields.

    Args:
        existing_config: Existing configuration to use as defaults (for updates)

    Returns:
        Dictionary with required field values
    """
    console.print("\n[bold]Required Settings[/bold]")
    console.print("─" * 50)

    # Client ID
    default_client_id = existing_config.get("client_id") if existing_config else None
    client_id = Prompt.ask(
        "\n[cyan]Client ID[/cyan]\n  OAuth2 client ID for authentication",
        default=default_client_id if default_client_id else ...,
    )

    # Client Secret (hidden input)
    has_existing_secret = bool(existing_config and existing_config.get("client_secret"))
    if has_existing_secret and existing_config:
        default_secret_display = "****************"
        console.print(f"\n[cyan]Client Secret[/cyan] [{default_secret_display}]")
        console.print("  OAuth2 client secret (leave empty to keep current)")
        client_secret = Prompt.ask("  Enter new secret", password=True, default="")
        if not client_secret:  # Keep existing
            client_secret = str(existing_config.get("client_secret", ""))
    else:
        client_secret = Prompt.ask(
            "\n[cyan]Client Secret[/cyan]\n  OAuth2 client secret (input will be hidden)",
            password=True,
        )

    # API Endpoint
    default_api = (
        existing_config.get("api_endpoint") if existing_config else DEFAULTS["api_endpoint"]
    )
    console.print("\n[cyan]API Endpoint[/cyan]")
    console.print("  Agent Builder API endpoint URL")
    console.print("  [dim]Examples:[/dim]")
    console.print(f"    [dim]Production: {DEFAULTS['api_endpoint']}[/dim]")
    console.print("    [dim]Development: https://api.agentbuilder.dev.experience.hyland.com/[/dim]")
    api_endpoint = Prompt.ask("  ", default=default_api)

    # Auth Endpoint
    default_auth = (
        existing_config.get("auth_endpoint") if existing_config else DEFAULTS["auth_endpoint"]
    )
    console.print("\n[cyan]Auth Endpoint[/cyan]")
    console.print("  OAuth2 authentication endpoint URL")
    console.print("  [dim]Examples:[/dim]")
    console.print(f"    [dim]Production: {DEFAULTS['auth_endpoint']}[/dim]")
    console.print(
        "    [dim]Development: https://auth.iam.dev.experience.hyland.com/idp/connect/token[/dim]"
    )
    auth_endpoint = Prompt.ask("  ", default=default_auth)

    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "api_endpoint": api_endpoint,
        "auth_endpoint": auth_endpoint,
    }


def prompt_for_optional_fields(existing_config: dict[str, Any] | None = None) -> dict[str, Any]:
    """Prompt user for optional configuration fields.

    Args:
        existing_config: Existing configuration to use as defaults (for updates)

    Returns:
        Dictionary with optional field values
    """
    console.print("\n[bold]Optional Settings[/bold]")
    console.print("─" * 50)

    # Ask if user wants to configure optional settings
    configure_optional = Confirm.ask("\nConfigure optional settings?", default=False)

    if not configure_optional:
        # Return defaults or existing values
        if existing_config:
            return {
                "grant_type": existing_config.get("grant_type", DEFAULTS["grant_type"]),
                "auth_scope": existing_config.get("auth_scope", DEFAULTS["auth_scope"]),
            }
        return {
            "grant_type": DEFAULTS["grant_type"],
            "auth_scope": DEFAULTS["auth_scope"],
        }

    # Grant Type
    default_grant = existing_config.get("grant_type") if existing_config else DEFAULTS["grant_type"]
    grant_type = Prompt.ask(
        "\n[cyan]OAuth2 Grant Type[/cyan]",
        default=default_grant,
    )

    # Auth Scope
    default_scope = existing_config.get("auth_scope") if existing_config else DEFAULTS["auth_scope"]
    scope_str = " ".join(default_scope) if isinstance(default_scope, list) else str(default_scope)
    scope_input = Prompt.ask(
        "\n[cyan]OAuth2 Scopes[/cyan] (space-separated)",
        default=scope_str,
    )
    auth_scope = scope_input.split() if scope_input else []

    return {
        "grant_type": grant_type,
        "auth_scope": auth_scope,
    }


def display_config_summary(
    config: dict[str, Any], existing_config: dict[str, Any] | None = None
) -> None:
    """Display configuration summary before saving.

    Args:
        config: New configuration
        existing_config: Existing configuration (for showing changes)
    """
    console.print("\n[bold]Configuration Summary[/bold]")
    console.print("─" * 50)

    # Show modified fields if updating
    if existing_config:
        console.print("\n[yellow]Modified fields:[/yellow]")
        changes = []
        for key, new_value in config.items():
            old_value = existing_config.get(key)
            if old_value != new_value and key != "client_secret":
                if isinstance(new_value, list):
                    new_display = ", ".join(new_value)
                    old_display = (
                        ", ".join(old_value) if isinstance(old_value, list) else str(old_value)
                    )
                else:
                    new_display = str(new_value)
                    old_display = str(old_value) if old_value else "(not set)"
                changes.append((key, old_display, new_display))

        if changes:
            for key, old_val, new_val in changes:
                # Truncate long values
                old_display = old_val[:40] + "..." if len(old_val) > 40 else old_val
                new_display = new_val[:40] + "..." if len(new_val) > 40 else new_val
                console.print(f"  ✓ {key}: {old_display} → {new_display}")
        else:
            console.print("  [dim]No changes detected[/dim]")
    else:
        # Show all fields for new config
        # Mask sensitive values
        client_id_display = (
            config["client_id"][:8] + "***" if len(config["client_id"]) > 8 else "***"
        )
        console.print(f"  ✓ Client ID:         {client_id_display}")
        console.print("  ✓ Client Secret:     ****************")
        console.print(f"  ✓ API Endpoint:      {config['api_endpoint']}")
        console.print(f"  ✓ Auth Endpoint:     {config['auth_endpoint']}")
        console.print(f"  ✓ Grant Type:        {config.get('grant_type', 'client_credentials')}")
        scopes = config.get("auth_scope", ["hxp"])
        console.print(f"  ✓ Auth Scopes:       {', '.join(scopes)}")


def save_config(config: dict[str, Any], path: Path) -> None:
    """Save configuration to YAML file with comments.

    Args:
        config: Configuration dictionary
        path: Path to save configuration file
    """
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Build YAML content with comments
    lines = [
        "# Agent Builder CLI Configuration",
        "# Generated by: ab configure",
        f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "# OAuth2 Authentication (required)",
        f'client_id: "{config["client_id"]}"',
        f'client_secret: "{config["client_secret"]}"',
        "",
        "# API Endpoints (required)",
        f'api_endpoint: "{config["api_endpoint"]}"',
        f'auth_endpoint: "{config["auth_endpoint"]}"',
        "",
        "# OAuth2 Configuration (optional)",
        f'grant_type: "{config.get("grant_type", DEFAULTS["grant_type"])}"',
        "auth_scope:",
    ]

    # Add auth scopes
    scopes = config.get("auth_scope", DEFAULTS["auth_scope"])
    for scope in scopes:
        lines.append(f'  - "{scope}"')

    # Add note about advanced settings
    lines.extend(
        [
            "",
            "# Advanced settings (timeout, retries, output format, etc.)",
            "# can be added manually. See config.example.yaml for all options.",
        ]
    )

    # Write file
    content = "\n".join(lines) + "\n"
    path.write_text(content)


@click.command()
@click.option(
    "-c",
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    help="Target configuration file (default: ~/.ab-cli/config.yaml)",
)
@click.option(
    "-o",
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    help="Alternative syntax for target file",
)
@click.option("--client-id", help="Set OAuth2 client ID")
@click.option("--client-secret", help="Set OAuth2 client secret")
@click.option("--api-endpoint", help="Set API endpoint URL")
@click.option("--auth-endpoint", help="Set auth endpoint URL")
@click.option("--grant-type", help="Set OAuth2 grant type")
@click.option("--auth-scope", multiple=True, help="Set OAuth2 scope (can be repeated)")
@click.option("--show", is_flag=True, help="Show current configuration and exit")
@click.option("--force", is_flag=True, help="Overwrite existing file without confirmation")
def configure(
    config_path: Path | None,
    output_path: Path | None,
    client_id: str | None,
    client_secret: str | None,
    api_endpoint: str | None,
    auth_endpoint: str | None,
    grant_type: str | None,
    auth_scope: tuple[str, ...],
    show: bool,
    force: bool,
) -> None:
    """Interactive configuration wizard for ab-cli.

    Create or update your ab-cli configuration file with guided prompts.
    """
    # Determine target config path
    target_path = output_path or config_path
    if not target_path:
        # Use default location
        target_path = Path.home() / ".ab-cli" / "config.yaml"

    # Handle --show flag
    if show:
        current_path = config_path or find_config_file()
        if not current_path:
            error_console.print("[red]No configuration file found.[/red]")
            sys.exit(1)

        try:
            settings = load_config(current_path)
            console.print(f"\n[bold]Current Configuration:[/bold] {current_path}\n")
            # Display redacted config
            from ab_cli.config import get_config_summary

            summary = get_config_summary(settings)
            for key, value in summary.items():
                console.print(f"  {key}: [dim]{value}[/dim]")
            console.print()
            return
        except ConfigurationError as e:
            error_console.print(f"[red]Error loading configuration:[/red] {e}")
            sys.exit(1)

    # Check if we're in non-interactive mode (all required fields provided)
    non_interactive = all([client_id, client_secret, api_endpoint, auth_endpoint])

    # Display header
    console.print("\n[bold cyan]=== Agent Builder CLI Configuration ===[/bold cyan]\n")
    console.print("This wizard will help you configure ab-cli.\n")
    console.print(f"Configuration file: [cyan]{target_path}[/cyan]")

    # Check if file exists
    file_exists = target_path.exists()
    console.print(f"File exists: [yellow]{'Yes' if file_exists else 'No'}[/yellow]\n")

    # Load existing configuration if updating
    existing_config: dict[str, Any] | None = None
    if file_exists:
        console.print("Loading current configuration...\n")
        try:
            # Read raw YAML to preserve non-managed fields
            with open(target_path) as f:
                existing_config = yaml.safe_load(f) or {}
            console.print("[green]✓ Current configuration loaded.[/green]\n")
        except Exception as e:
            error_console.print(f"[yellow]Warning: Could not load existing config: {e}[/yellow]\n")
            existing_config = {}

        if not force and not non_interactive:
            console.print("You can now update any field. Press Enter to keep the current value.\n")

    if non_interactive:
        # Build config from CLI options
        config = {
            "client_id": client_id,
            "client_secret": client_secret,
            "api_endpoint": api_endpoint,
            "auth_endpoint": auth_endpoint,
            "grant_type": grant_type or existing_config.get("grant_type")
            if existing_config
            else DEFAULTS["grant_type"],
            "auth_scope": list(auth_scope)
            if auth_scope
            else (existing_config.get("auth_scope") if existing_config else DEFAULTS["auth_scope"]),
        }
    else:
        # Interactive mode
        console.print("Let's configure the required settings.\n")

        # Prompt for required fields
        required = prompt_for_required_fields(existing_config)

        # Prompt for optional fields
        optional = prompt_for_optional_fields(existing_config)

        # Merge configurations
        config = {**required, **optional}

        # Preserve other fields from existing config
        if existing_config:
            for key, value in existing_config.items():
                if key not in config:
                    config[key] = value

    # Display summary
    display_config_summary(config, existing_config)

    # Confirm save
    if (
        not force
        and not non_interactive
        and not Confirm.ask(f"\nSave configuration to {target_path}?", default=True)
    ):
        console.print("\n[yellow]Configuration not saved.[/yellow]")
        return

    # Save configuration
    try:
        save_config(config, target_path)
        console.print("\n[green]✓ Configuration saved successfully![/green]\n")

        # Validate the saved configuration
        try:
            validate_config_file(target_path)
            console.print("[green]✓ Configuration is valid.[/green]\n")
        except ConfigurationError as e:
            error_console.print(f"[yellow]Warning: Configuration validation failed:[/yellow] {e}\n")

        # Show next steps
        console.print("[bold]Next Steps:[/bold]")
        console.print("  1. Test your configuration: [cyan]ab check[/cyan]")
        console.print("  2. List available agents: [cyan]ab agents list[/cyan]")
        console.print("  3. Get help: [cyan]ab --help[/cyan]\n")

        # Offer to run check command
        if not non_interactive and Confirm.ask("Test the configuration now?", default=True):
            console.print()
            # Import here to avoid circular dependency
            from ab_cli.cli.main import check

            ctx = click.Context(check)
            ctx.invoke(check, config_override=str(target_path), auth_only=False)

    except Exception as e:
        error_console.print(f"\n[red]Error saving configuration:[/red] {e}")
        sys.exit(1)
