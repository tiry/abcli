"""Main CLI entry point for ab-cli."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from ab_cli import __version__
from ab_cli.api import AuthClient, AuthenticationError
from ab_cli.api.exceptions import TokenError

# Import command groups
from ab_cli.cli.agents import agents
from ab_cli.cli.versions import versions
from ab_cli.config import (
    ConfigurationError,
    find_config_file,
    get_config_summary,
    get_profile_summary,
    load_config,
    validate_config_file,
)
from ab_cli.config.loader import load_config_with_profile

# Rich console for formatted output
console = Console()
error_console = Console(stderr=True)


@click.group(invoke_without_command=True)
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--profile",
    type=str,
    help="Configuration profile to use (e.g., dev, staging, prod)",
)
@click.version_option(__version__, prog_name="ab-cli")
@click.pass_context
def main(ctx: click.Context, verbose: bool, config: Path | None, profile: str | None) -> None:
    """Agent Builder CLI - Manage and invoke AI agents.

    Use 'ab COMMAND --help' for more information about a command.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    # Find and load configuration
    config_path = config or find_config_file()
    ctx.obj["config_path"] = str(config_path) if config_path else None
    ctx.obj["profile"] = profile  # Store profile for subcommands

    # If no subcommand was provided, show helpful message
    if ctx.invoked_subcommand is None:
        # Show default help
        console.print(ctx.get_help())
        console.print()

        # If no config found, show helpful hint
        if not config_path:
            console.print("[yellow]💡 Getting Started:[/yellow]")
            console.print("   No configuration file found. To set up ab-cli, run:")
            console.print("   [cyan]ab configure[/cyan]")
            console.print()
        return

    if config_path:
        try:
            # Load config with profile support
            if profile:
                ctx.obj["settings"] = load_config_with_profile(config_path, profile=profile)
                if verbose:
                    console.print(
                        f"[dim]Loaded config from: {config_path} (profile: {profile})[/dim]"
                    )
                    settings = ctx.obj["settings"]
                    console.print(f"[dim]  → client_id: {settings.client_id[:12]}...[/dim]")
                    console.print(f"[dim]  → api_endpoint: {settings.api_endpoint}[/dim]")
            else:
                ctx.obj["settings"] = load_config(config_path)
                if verbose:
                    console.print(f"[dim]Loaded config from: {config_path}[/dim]")
        except ConfigurationError as e:
            error_console.print(f"[red]Configuration error:[/red] {e}")
            error_console.print("\nTo fix your configuration, run:")
            error_console.print("  [cyan]ab configure[/cyan]")
            sys.exit(1)
        except ValueError as e:
            # Profile not found
            error_msg = str(e).replace("[", "\\[").replace("]", "\\]")
            error_console.print(f"[red]Profile error:[/red] {error_msg}")
            error_console.print("\nTo see available profiles, run:")
            error_console.print("  [cyan]ab profiles list[/cyan]")
            sys.exit(1)


@main.command()
@click.option(
    "-c",
    "--config",
    "config_override",
    type=click.Path(exists=True),
    default=None,
    help="Path to configuration file (default: config.yaml).",
)
@click.option("--auth-only", is_flag=True, help="Only check authentication (skip API test)")
@click.pass_context
def check(ctx: click.Context, config_override: str | None, auth_only: bool) -> None:
    """Test API connectivity with verbose output.

    This command performs a full connectivity check against the Agent Builder API:

    \b
    1. Validates configuration
    2. Tests authentication and token retrieval
    3. Pings the Agent Builder API (lists agent types)

    Use this command to debug setup or configuration issues.

    \b
    Examples:
        # Full connectivity check
        ab check -c config.yaml
        # Only check authentication
        ab check -c config.yaml --auth-only
    """
    import time
    from pathlib import Path

    from ab_cli.api.client import AgentBuilderClient

    # Resolve config path: command option > parent group option > default file
    config_path = config_override or ctx.obj.get("config_path")
    if not config_path:
        # Check if default config.yaml exists
        default_config = Path("config.yaml")
        if default_config.exists():
            config_path = str(default_config)

    # Track steps
    steps_completed = 0
    total_steps = 2 if auth_only else 3

    console.print()
    console.print("[bold cyan]=== Agent Builder API Connectivity Check ===[/bold cyan]")
    console.print()

    # ===== Step 1: Configuration =====
    console.print(f"[bold yellow]Step 1/{total_steps}:[/bold yellow] Loading configuration")
    console.print(f"  Config file: {config_path}")

    if not config_path:
        error_console.print("  [red]✗ No configuration file found[/red]")
        error_console.print()
        error_console.print("  To create a configuration file, run:")
        error_console.print("    [cyan]ab configure[/cyan]")
        error_console.print()
        error_console.print("  Searched locations:")
        error_console.print("    • config.yaml (current directory)")
        error_console.print("    • ab-cli.yaml (current directory)")
        error_console.print("    • ~/.ab-cli/config.yaml")
        console.print()
        sys.exit(1)

    try:
        # Use profile-aware settings from context if available
        profile = ctx.obj.get("profile")
        if profile and ctx.obj.get("settings"):
            # Settings already loaded with profile in main()
            settings = ctx.obj["settings"]
            console.print(
                f"[green]  ✓ Configuration loaded successfully (profile: {profile})[/green]"
            )
        elif profile:
            # Profile specified but settings not in context, load with profile
            settings = load_config_with_profile(config_path, profile=profile)
            console.print(
                f"[green]  ✓ Configuration loaded successfully (profile: {profile})[/green]"
            )
        else:
            # No profile, load normally
            settings = load_config(config_path)
            console.print("[green]  ✓ Configuration loaded successfully[/green]")
        console.print()
        console.print("  Configuration Summary:")
        console.print(f"    API endpoint:     {settings.api_endpoint}")
        console.print(f"    Auth endpoint:    {settings.auth_endpoint}")
        if settings.environment_id:
            console.print(f"    Environment ID:   {settings.environment_id}")
        console.print(f"    Client ID:        {settings.client_id[:8]}...{settings.client_id[-4:]}")
        console.print(f"    Client secret:    {'*' * 20}")
        console.print()
        steps_completed += 1

    except ConfigurationError as e:
        error_console.print(f"  [red]✗ Configuration error: {e}[/red]")
        sys.exit(1)

    # ===== Step 2: Authentication =====
    console.print(f"[bold yellow]Step 2/{total_steps}:[/bold yellow] Testing authentication")
    console.print("  Creating auth client...")
    console.print(f"    Token endpoint: {settings.auth_endpoint}")

    try:
        auth_client = AuthClient(settings)
        console.print("[green]  ✓ Auth client created[/green]")
    except Exception as e:
        error_console.print(f"  [red]✗ Failed to create auth client: {e}[/red]")
        sys.exit(1)

    console.print("  Fetching OAuth2 token from auth server...")
    start_time = time.time()

    try:
        token = auth_client.get_token()
        elapsed = time.time() - start_time

        console.print("[green]  ✓ Valid OAuth2 token received![/green]")
        console.print()
        console.print("  Token Details:")
        console.print(f"    Token prefix:   {token[:20]}...")
        console.print(f"    Token length:   {len(token)} characters")
        console.print(f"    Request time:   {elapsed:.3f}s")
        console.print()
        console.print("[bold green]  Authentication: SUCCESS[/bold green]")
        console.print()
        steps_completed += 1

    except (AuthenticationError, TokenError) as e:
        elapsed = time.time() - start_time
        error_console.print(f"  [red]✗ Token request failed ({elapsed:.3f}s)[/red]")
        console.print()
        console.print("  Error Details:")
        console.print(f"    Type:    {type(e).__name__}")
        console.print(f"    Message: {e}")
        console.print()
        console.print("[bold red]  Authentication: FAILED[/bold red]")
        sys.exit(1)

    if auth_only:
        console.print()
        console.print("[bold green]=== Check Complete (auth only) ===[/bold green]")
        console.print(f"  Steps completed: {steps_completed}/{total_steps}")
        return

    # ===== Step 3: API Connectivity =====
    console.print(f"[bold yellow]Step 3/{total_steps}:[/bold yellow] Testing API connectivity")
    console.print("  Creating Agent Builder API client...")
    console.print(f"    API endpoint:    {settings.api_endpoint}")
    console.print(f"    Environment ID:  {settings.environment_id}")

    try:
        client = AgentBuilderClient(settings, auth_client=auth_client)
        console.print("[green]  ✓ API client created[/green]")
        console.print()
    except Exception as e:
        error_console.print(f"  [red]✗ Failed to create API client: {e}[/red]")
        sys.exit(1)

    # Test API by calling health endpoint
    console.print("  Pinging Agent Builder API (GET /health)...")
    start_time = time.time()

    try:
        with client:
            result = client.health_check()
        elapsed = time.time() - start_time

        console.print("[green]  ✓ API responded successfully![/green]")
        console.print()
        console.print("  Health Check Response:")
        status = result.get("status", "unknown")
        console.print(f"    Status: {status}")
        # Display any additional health info if present
        for key, value in result.items():
            if key != "status":
                console.print(f"    {key}: {value}")
        console.print(f"    Request time: {elapsed:.3f}s")
        console.print()
        console.print("[bold green]  API Connectivity: SUCCESS[/bold green]")
        console.print()
        steps_completed += 1

    except Exception as e:
        elapsed = time.time() - start_time
        error_console.print(f"  [red]✗ API request failed ({elapsed:.3f}s)[/red]")
        console.print()
        console.print("  Error Details:")
        console.print(f"    Type:    {type(e).__name__}")
        console.print(f"    Message: {e}")
        console.print()
        console.print("[bold red]  API Connectivity: FAILED[/bold red]")
        sys.exit(1)

    # ===== Summary =====
    console.print()
    console.print("[bold green]=== Check Complete ===[/bold green]")
    console.print(f"  Steps completed: {steps_completed}/{total_steps}")
    console.print()
    console.print("  All API endpoints are working correctly!")
    console.print()


@main.command()
@click.option("--show-config", is_flag=True, help="Show loaded configuration values")
@click.argument("config_file", type=click.Path(exists=True, path_type=Path), required=False)
@click.pass_context
def validate(ctx: click.Context, show_config: bool, config_file: Path | None) -> None:
    """Validate configuration file."""
    import yaml

    path = config_file or find_config_file()

    if not path:
        error_console.print("[red]No configuration file found[/red]")
        error_console.print("Searched: config.yaml, ab-cli.yaml, ~/.ab-cli/config.yaml")
        sys.exit(1)

    console.print(f"\n[bold]Validating:[/bold] {path}\n")

    try:
        settings, warnings = validate_config_file(path)
        console.print("✅ [green]Configuration is valid[/green]")

        if warnings:
            console.print("\n[yellow]Warnings:[/yellow]")
            for warning in warnings:
                console.print(f"  ⚠️  {warning}")

        if show_config:
            # Get active profile from context
            active_profile = ctx.obj.get("profile") if ctx.obj else None

            # Load raw config data to get available profiles
            with open(path) as f:
                config_data = yaml.safe_load(f) or {}

            # Display profile information
            console.print("\n[bold]Profile Information:[/bold]")
            profile_info = get_profile_summary(config_data, active_profile)
            for key, value in profile_info.items():
                console.print(f"  {key}: [dim]{value}[/dim]")

            # Display configuration values
            console.print("\n[bold]Configuration Values:[/bold]")
            config_summary = get_config_summary(settings)
            for key, value in config_summary.items():
                console.print(f"  {key}: [dim]{value}[/dim]")

    except ConfigurationError as e:
        console.print("❌ [red]Configuration is invalid[/red]")
        console.print(f"\n{e}")
        sys.exit(1)

    console.print()


# Import all commands
from ab_cli.cli.auth import auth  # noqa: E402
from ab_cli.cli.configure import configure  # noqa: E402
from ab_cli.cli.invoke import invoke  # noqa: E402
from ab_cli.cli.profiles import profiles  # noqa: E402
from ab_cli.cli.resources import resources  # noqa: E402
from ab_cli.cli.ui import ui  # noqa: E402

# Register all commands
main.add_command(auth)
main.add_command(configure)
main.add_command(agents)
main.add_command(versions)
main.add_command(invoke)
main.add_command(profiles)
main.add_command(resources)
main.add_command(ui)


if __name__ == "__main__":
    main()
