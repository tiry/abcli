"""UI command for launching the Agent Builder UI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click
import streamlit.web.cli as stcli
from rich.console import Console

from ab_cli.cli.common_options import profile_option

# Rich console for formatted output
console = Console()
error_console = Console(stderr=True)


@click.command("ui")
@click.option("--port", default=8501, help="Port to run the Streamlit server on")
@click.option(
    "--config-path", type=click.Path(exists=True, path_type=Path), help="Path to configuration file"
)
@profile_option
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
@click.option("--verbose", is_flag=True, help="Enable verbose output for CLI commands")
@click.option("--mock", is_flag=True, help="Use mock data provider (for testing/demo)")
@click.option("--direct", is_flag=True, help="Use direct API data provider (recommended)")
@click.option("--cli", is_flag=True, help="Use CLI subprocess data provider (legacy)")
@click.pass_context
def ui(
    ctx: click.Context,
    port: int,
    config_path: Path | None,
    profile: str | None,
    no_browser: bool,
    verbose: bool,
    mock: bool,
    direct: bool,
    cli: bool,
) -> int:
    """Launch the Agent Builder UI in a web browser.

    This command launches a Streamlit-based web UI for interacting with
    the Agent Builder API. The UI provides a graphical interface for
    managing and testing agents.

    \b
    Features:
    - List, create, update, and delete agents
    - Chat with agents
    - View configuration details

    \b
    Data Provider Backends:
    By default, the UI uses the CLI subprocess provider. You can choose different backends:
    - --direct: Direct API calls (fastest, recommended for production)
    - --cli: CLI subprocess calls (legacy, default if no flag specified)
    - --mock: Mock data for testing/demo (no real API calls)

    \b
    Examples:
        # Launch UI with direct API provider (recommended)
        ab ui --direct

        # Launch UI on a specific port with mock data
        ab ui --port 9000 --mock

        # Launch UI with a specific configuration file
        ab ui --config-path /path/to/config.yaml --direct

        # Launch UI without opening a browser
        ab ui --no-browser --direct
    """
    # Get configuration from context if not specified
    if not config_path and "config_path" in ctx.obj:
        config_path = ctx.obj["config_path"]

    # Validate mutually exclusive flags
    provider_flags = sum([mock, direct, cli])
    if provider_flags > 1:
        error_console.print(
            "[red]Error: Only one of --mock, --direct, or --cli can be specified[/red]"
        )
        return 1

    # Determine data provider backend
    # Only set if explicitly specified via flags
    provider_type = None
    if mock:
        provider_type = "mock"
    elif direct:
        provider_type = "direct"
    elif cli:
        provider_type = "cli"

    # Use the abui module from ab_cli package
    try:
        # Only set environment variable if explicitly specified via command line
        # Otherwise, let the config file determine the provider type
        if provider_type:
            os.environ["AB_UI_DATA_PROVIDER"] = provider_type
            if verbose:
                provider_names = {
                    "mock": "Mock data provider (testing/demo)",
                    "direct": "Direct API provider (recommended)",
                    "cli": "CLI subprocess provider (legacy)",
                }
                print(f"Data provider: {provider_names[provider_type]}")
        elif verbose:
            print("Data provider: Using setting from config file")

        # The app.py is directly in the abui module
        app_path = os.path.join(os.path.dirname(__file__), "..", "abui", "app.py")
        if getattr(sys, "frozen", False):
            # We are running in a bundle
            bundle_dir = sys._MEIPASS  # type: ignore
            # Path to the python.exe inside your added 'python_env' folder
            app_path = os.path.join(bundle_dir, "abui", "app.py")

        # Build the command
        cmd = [sys.executable, "-m", "streamlit", "run", app_path, "--server.port", str(port)]

        if no_browser:
            cmd.append("--server.headless")

        has_cli_options = config_path or verbose or provider_type != "cli"

        if has_cli_options:
            cmd.append("--")

        if config_path:
            cmd.extend(["--config", str(config_path)])

        if profile:
            cmd.extend(["--profile", profile])

        if verbose:
            cmd.extend(["--verbose"])

        # Pass provider type to the app (only if explicitly set)
        if provider_type and provider_type != "cli":
            cmd.extend(["--provider", provider_type])

        console.print(f"[cyan]Launching Agent Builder UI on port {port}...[/cyan]")

        # Run Streamlit as a subprocess
        if verbose:
            # In verbose mode, show output in console
            print(f"Launching with verbose mode - command: {' '.join(cmd)}")
            # Pass the verbose output directly to stdout/stderr
            subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)
        else:
            # subprocess.run(cmd)
            sys.argv = cmd[2:]
            sys.exit(stcli.main())
        return 0

    except ImportError as e:
        error_console.print(f"[red]Error: {e}[/red]")
        return 1
