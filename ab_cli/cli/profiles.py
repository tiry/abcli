"""Profiles command for managing configuration profiles."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ab_cli.config import find_config_file, get_config_summary
from ab_cli.config.loader import get_available_profiles, load_config_with_profile

console = Console()
error_console = Console(stderr=True)


@click.group()
def profiles() -> None:
    """Manage configuration profiles for different environments.

    Profiles allow you to maintain multiple environment configurations
    (dev, staging, prod) in a single config file and switch between them
    using the --profile flag.

    \b
    Examples:
        # List all available profiles
        ab profiles list

        # Show merged config for dev profile
        ab profiles show dev

        # Show default profile config
        ab profiles show
    """
    pass


@profiles.command("list")
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.pass_context
def list_profiles(ctx: click.Context, config: Path | None) -> None:
    """List all available profiles in the configuration file.

    Shows a table of all defined profiles with their names.
    If no profiles are defined, displays a helpful message.

    \b
    Examples:
        ab profiles list
        ab profiles list -c config.yaml
    """
    # Get config path
    config_path = config or ctx.obj.get("config_path") or find_config_file()

    if not config_path:
        error_console.print("[red]No configuration file found[/red]")
        error_console.print("\nSearched locations:")
        error_console.print("  • config.yaml")
        error_console.print("  • ab-cli.yaml")
        error_console.print("  • ~/.ab-cli/config.yaml")
        sys.exit(1)

    try:
        profile_names = get_available_profiles(config_path)

        if not profile_names:
            console.print(f"\n[yellow]No profiles defined in {config_path}[/yellow]")
            console.print("\nTo add profiles, edit your config file and add a 'profiles' section:")
            console.print("\nprofiles:", style="dim")
            console.print("  dev:", style="dim")
            console.print("    api_endpoint: https://api.dev.example.com/", style="dim")
            console.print("  prod:", style="dim")
            console.print("    api_endpoint: https://api.prod.example.com/\n", style="dim")
            return

        # Create table
        table = Table(
            title=f"\nProfiles in {config_path}", show_header=True, header_style="bold cyan"
        )
        table.add_column("Profile Name", style="green")
        table.add_column("Description", style="dim")

        for profile_name in profile_names:
            table.add_row(profile_name, f"Use: ab --profile {profile_name} <command>")

        console.print(table)
        console.print(f"\n[dim]Found {len(profile_names)} profile(s)[/dim]")
        console.print("[dim]Use 'ab profiles show <name>' to view merged configuration[/dim]\n")

    except Exception as e:
        # Escape any markup characters in the exception message
        error_msg = str(e).replace("[", "\\[").replace("]", "\\]")
        error_console.print(f"[red]Error reading profiles: {error_msg}[/red]")
        sys.exit(1)


@profiles.command("show")
@click.argument("profile_name", required=False)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.pass_context
def show_profile(ctx: click.Context, profile_name: str | None, config: Path | None) -> None:
    """Show merged configuration for a profile.

    Displays the effective configuration after applying profile overrides.
    Secrets (client_secret) are redacted for security.

    If no profile name is provided, shows the default (base) configuration.

    \b
    Examples:
        # Show default config
        ab profiles show

        # Show dev profile config
        ab profiles show dev

        # Show staging profile with custom config file
        ab profiles show staging -c config.yaml
    """
    # Get config path
    config_path = config or ctx.obj.get("config_path") or find_config_file()

    if not config_path:
        error_console.print("[red]No configuration file found[/red]")
        error_console.print("\nSearched locations:")
        error_console.print("  • config.yaml")
        error_console.print("  • ab-cli.yaml")
        error_console.print("  • ~/.ab-cli/config.yaml")
        sys.exit(1)

    try:
        # Load config with profile
        settings = load_config_with_profile(config_path, profile=profile_name)

        # Get summary with redacted secrets
        summary = get_config_summary(settings)

        # Display header
        if profile_name:
            console.print(f"\n[bold cyan]Profile:[/bold cyan] {profile_name}")
        else:
            console.print("\n[bold cyan]Profile:[/bold cyan] default (base configuration)")

        console.print(f"[dim]Config file: {config_path}[/dim]\n")

        # Create table
        table = Table(show_header=True, header_style="bold cyan", box=None)
        table.add_column("Setting", style="yellow", no_wrap=True)
        table.add_column("Value", style="white")

        for key, value in summary.items():
            # Highlight redacted secrets
            if "****" in str(value) or "..." in str(value):
                table.add_row(key, f"[dim]{value}[/dim]")
            else:
                table.add_row(key, value)

        console.print(table)
        console.print()

        # Show hint about using profile
        if profile_name:
            console.print(f"[dim]To use this profile, add: --profile {profile_name}[/dim]")
            console.print(f"[dim]Example: ab --profile {profile_name} agents list[/dim]\n")

    except ValueError as e:
        # Profile not found or invalid - escape markup in error message
        error_msg = str(e).replace("[", "\\[").replace("]", "\\]")
        error_console.print(f"[red]Error: {error_msg}[/red]")
        console.print("\nAvailable profiles:")
        try:
            profile_names = get_available_profiles(config_path)
            if profile_names:
                for name in profile_names:
                    console.print(f"  • {name}")
            else:
                console.print("  (none)")
        except Exception:
            pass
        sys.exit(1)
    except Exception as e:
        # Escape any markup characters in the exception message
        error_msg = str(e).replace("[", "\\[").replace("]", "\\]")
        error_console.print(f"[red]Error loading configuration: {error_msg}[/red]")
        sys.exit(1)
