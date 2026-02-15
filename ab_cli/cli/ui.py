"""UI command for launching the Agent Builder UI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

# Rich console for formatted output
console = Console()
error_console = Console(stderr=True)


@click.command("ui")
@click.option("--port", default=8501, help="Port to run the Streamlit server on")
@click.option(
    "--config-path", type=click.Path(exists=True, path_type=Path), help="Path to configuration file"
)
@click.option("--no-browser", is_flag=True, help="Don't open browser automatically")
@click.option("--verbose", is_flag=True, help="Enable verbose output for CLI commands")
@click.option("--mock", is_flag=True, help="Use mock data provider instead of CLI provider")
@click.pass_context
def ui(
    ctx: click.Context,
    port: int,
    config_path: Path | None,
    no_browser: bool,
    verbose: bool,
    mock: bool,
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

    The UI requires the 'abui' package to be installed. If not installed,
    you will be prompted to install it.

    \b
    Examples:
        # Launch UI on default port
        ab ui

        # Launch UI on a specific port
        ab ui --port 9000

        # Launch UI with a specific configuration file
        ab ui --config-path /path/to/config.yaml

        # Launch UI without opening a browser
        ab ui --no-browser
    """
    # Get configuration from context if not specified
    if not config_path and "config_path" in ctx.obj:
        config_path = ctx.obj["config_path"]

    # Use the abui module from ab_cli package
    try:
        # If mock is set, set the environment variable
        if mock:
            os.environ["AB_UI_DATA_PROVIDER"] = "mock"
            if verbose:
                print("Mock mode enabled: Using mock data provider")

        # The app.py is directly in the abui module
        app_path = os.path.join(os.path.dirname(__file__), "..", "abui", "app.py")

        # Build the command
        cmd = [sys.executable, "-m", "streamlit", "run", app_path, "--server.port", str(port)]

        if no_browser:
            cmd.append("--server.headless")

        has_cli_options = config_path or verbose or mock

        if has_cli_options:
            cmd.append("--")

        if config_path:
            cmd.extend(["--config", str(config_path)])

        if verbose:
            cmd.extend(["--verbose"])

        if mock:
            # Also pass mock flag to the app
            cmd.extend(["--mock", "true"])

        console.print(f"[cyan]Launching Agent Builder UI on port {port}...[/cyan]")

        # Run Streamlit as a subprocess
        if verbose:
            # In verbose mode, show output in console
            print(f"Launching with verbose mode - command: {' '.join(cmd)}")
            # Pass the verbose output directly to stdout/stderr
            subprocess.run(cmd, stdout=sys.stdout, stderr=sys.stderr)
        else:
            subprocess.run(cmd)
        return 0

    except ImportError as e:
        error_console.print(f"[red]Error: {e}[/red]")
        return 1
