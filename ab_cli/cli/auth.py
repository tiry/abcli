"""Auth command - retrieve OAuth2 token and show API examples."""

from __future__ import annotations

import sys
import time
from datetime import datetime

import click
from rich.console import Console

from ab_cli.api import AuthClient
from ab_cli.api.exceptions import AuthenticationError, TokenError
from ab_cli.config import ConfigurationError, find_config_file, load_config
from ab_cli.config.loader import load_config_with_profile

console = Console()
error_console = Console(stderr=True)


@click.command("auth")
@click.option(
    "--curl",
    "tool",
    flag_value="curl",
    default=True,
    help="Generate curl example (default)",
)
@click.option(
    "--wget",
    "tool",
    flag_value="wget",
    help="Generate wget example",
)
@click.option(
    "--get",
    "method",
    flag_value="get",
    default=True,
    help="Show GET example - list agents (default)",
)
@click.option(
    "--post",
    "method",
    flag_value="post",
    help="Show POST example - invoke agent",
)
@click.option(
    "-c",
    "--config",
    "config_override",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option(
    "--profile",
    "profile_override",
    type=str,
    help="Configuration profile to use",
)
@click.pass_context
def auth(
    ctx: click.Context,
    tool: str,
    method: str,
    config_override: str | None,
    profile_override: str | None,
) -> None:
    """Authenticate and show API example with token.

    This command retrieves an OAuth2 token and generates ready-to-use
    curl or wget commands for calling the Agent Builder API.

    \b
    Examples:
        # Default: curl GET example
        ab auth

        # wget GET example
        ab auth --wget

        # curl POST example
        ab auth --post

        # wget POST example
        ab auth --wget --post

        # With config file
        ab auth --config custom.yaml

        # With profile (either way works)
        ab auth --profile staging
        ab --profile staging auth

        # Combined
        ab auth --config custom.yaml --profile staging
    """
    # Load configuration - command options override parent context
    config_path = config_override or ctx.obj.get("config_path")
    profile = profile_override or ctx.obj.get("profile")

    if not config_path:
        config_path = find_config_file()

    if not config_path:
        error_console.print("[red]✗ No configuration file found[/red]")
        error_console.print()
        error_console.print("To create a configuration file, run:")
        error_console.print("  [cyan]ab configure[/cyan]")
        sys.exit(1)

    # Load settings (reuse logic from check command)
    try:
        if profile:
            settings = load_config_with_profile(config_path, profile=profile)
        else:
            settings = load_config(config_path)
    except ConfigurationError as e:
        error_console.print(f"[red]Configuration error:[/red] {e}")
        sys.exit(1)
    except ValueError as e:
        error_msg = str(e).replace("[", "\\[").replace("]", "\\]")
        error_console.print(f"[red]Profile error:[/red] {error_msg}")
        sys.exit(1)

    # Authenticate and get token (reuse AuthClient)
    try:
        auth_client = AuthClient(settings)
        token = auth_client.get_token()
        token_info = auth_client._token  # Access internal token info for expiry
    except (AuthenticationError, TokenError) as e:
        error_console.print(f"[red]✗ Authentication failed:[/red] {e}")
        sys.exit(1)

    # Display success and token
    console.print()
    console.print("[green]✓ Authentication successful![/green]")
    console.print()
    console.print("[bold]Access Token:[/bold]")
    # Print token in plain text (no formatting) so it can be copy-pasted
    print(token)
    console.print()

    # Display token expiry information
    if token_info and hasattr(token_info, "expires_at"):
        expires_at_timestamp = token_info.expires_at
        expires_at_dt = datetime.fromtimestamp(expires_at_timestamp)
        now = time.time()
        expires_in_seconds = int(expires_at_timestamp - now)

        # Format human-readable time
        if expires_in_seconds >= 3600:
            hours = expires_in_seconds // 3600
            minutes = (expires_in_seconds % 3600) // 60
            if minutes > 0:
                human_readable = f"{hours} hour{'s' if hours != 1 else ''}, {minutes} minute{'s' if minutes != 1 else ''}"
            else:
                human_readable = f"{hours} hour{'s' if hours != 1 else ''}"
        elif expires_in_seconds >= 60:
            minutes = expires_in_seconds // 60
            human_readable = f"{minutes} minute{'s' if minutes != 1 else ''}"
        else:
            human_readable = f"{expires_in_seconds} second{'s' if expires_in_seconds != 1 else ''}"

        console.print("[bold]Token Details:[/bold]")
        console.print(f"  Expires in: {expires_in_seconds} seconds ({human_readable})")
        console.print(f"  Expires at: {expires_at_dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        console.print()

    # Generate example command
    api_endpoint = settings.api_endpoint.rstrip("/")
    env_id = settings.environment_id

    if tool == "curl":
        if method == "get":
            example_title, example_cmd = _generate_curl_get(api_endpoint, env_id, token)
        else:
            example_title, example_cmd = _generate_curl_post(api_endpoint, env_id, token)
    else:  # wget
        if method == "get":
            example_title, example_cmd = _generate_wget_get(api_endpoint, env_id, token)
        else:
            example_title, example_cmd = _generate_wget_post(api_endpoint, env_id, token)

    # Print title with Rich formatting, command in plain text for copy-paste
    console.print(f"[bold]{example_title}[/bold]")
    print(example_cmd)
    console.print()


def _generate_curl_get(api_endpoint: str, env_id: str | None, token: str) -> tuple[str, str]:  # noqa: ARG001
    """Generate curl command for GET request (list agents)."""
    # Note: env_id parameter kept for backward compatibility but not used for GET
    url = f"{api_endpoint}/v1/agents?limit=50&offset=0"

    title = "Example curl command (GET - List Agents):"
    cmd = f'curl -X GET "{url}" -H "Authorization: Bearer {token}"'

    return title, cmd


def _generate_curl_post(api_endpoint: str, env_id: str | None, token: str) -> tuple[str, str]:  # noqa: ARG001
    """Generate curl command for POST request (invoke agent)."""
    # Note: env_id parameter kept for backward compatibility but not used for POST
    url = f"{api_endpoint}/v1/agents/<agent-id>/versions/latest/invoke"

    title = "Example curl command (POST - Invoke Agent):"
    cmd = f'curl -X POST "{url}" -H "Authorization: Bearer {token}" -H "Content-Type: application/json" -d \'{{"messages": [{{"role": "user", "content": "Hello, agent!"}}]}}\''

    return title, cmd


def _generate_wget_get(api_endpoint: str, env_id: str | None, token: str) -> tuple[str, str]:  # noqa: ARG001
    """Generate wget command for GET request (list agents)."""
    # Note: env_id parameter kept for backward compatibility but not used for GET
    url = f"{api_endpoint}/v1/agents?limit=50&offset=0"

    title = "Example wget command (GET - List Agents):"
    cmd = f'wget -O - --header="Authorization: Bearer {token}" "{url}"'

    return title, cmd


def _generate_wget_post(api_endpoint: str, env_id: str | None, token: str) -> tuple[str, str]:  # noqa: ARG001
    """Generate wget command for POST request (invoke agent)."""
    # Note: env_id parameter kept for backward compatibility but not used for POST
    url = f"{api_endpoint}/v1/agents/<agent-id>/versions/latest/invoke"

    title = "Example wget command (POST - Invoke Agent):"
    cmd = f'wget -O - --header="Authorization: Bearer {token}" --header="Content-Type: application/json" --post-data=\'{{"messages": [{{"role": "user", "content": "Hello, agent!"}}]}}\' "{url}"'

    return title, cmd
