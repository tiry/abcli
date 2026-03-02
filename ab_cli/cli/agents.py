"""CLI commands for agent management."""

import json
import sys

import click
import yaml
from rich.console import Console
from rich.table import Table

from ab_cli.api.client import AgentBuilderClient
from ab_cli.api.exceptions import APIError, NotFoundError
from ab_cli.api.pagination import fetch_agents_paginated
from ab_cli.cli.client_utils import get_client_with_error_handling
from ab_cli.cli.common_options import profile_option
from ab_cli.cli.pagination_utils import (
    get_single_keypress,
    show_next_page_command,
    show_pagination_info,
)
from ab_cli.config.loader import find_config_file, load_config, load_config_with_profile
from ab_cli.config.settings import ABSettings
from ab_cli.models.agent import AgentUpdate
from ab_cli.services.agent_service import AgentService
from ab_cli.utils.editor import get_editor, open_editor
from ab_cli.utils.tempfile_manager import (
    cleanup_tempfile,
    create_agent_edit_tempfile,
    read_agent_edit_tempfile,
)
from ab_cli.utils.version import increment_version

console = Console()


def get_client(
    config_path: str | None = None,
    profile: str | None = None,
    settings: ABSettings | None = None,
) -> AgentBuilderClient:
    """Get an authenticated API client with user-friendly error handling."""
    return get_client_with_error_handling(config_path, profile, settings)


def output_json(data: dict) -> None:
    """Output data as JSON."""
    console.print_json(json.dumps(data, default=str))


def output_yaml(data: dict) -> None:
    """Output data as YAML."""
    console.print(yaml.dump(data, default_flow_style=False))


@click.group()
@profile_option
@click.pass_context
def agents(ctx: click.Context, profile: str | None) -> None:
    """Manage agents (list, create, update, delete)."""
    # Store profile in context for subcommands
    ctx.ensure_object(dict)
    if profile:
        ctx.obj["profile"] = profile
        # Load config with profile if profile is specified
        config_path = ctx.obj.get("config_path") or find_config_file()
        if config_path:
            try:
                ctx.obj["settings"] = load_config_with_profile(config_path, profile=profile)
            except ValueError as e:
                console.print(f"[red]Profile error:[/red] {e}")
                console.print("\nTo see available profiles, run:")
                console.print("  [cyan]ab profiles list[/cyan]")
                raise SystemExit(1)


@agents.command("list")
@click.option("--limit", "-l", default=50, help="Maximum number of agents to return")
@click.option("--offset", "-o", default=0, help="Offset for pagination")
@click.option("--page", "-p", type=int, help="Jump to page N (cannot use with --offset or filters)")
@click.option("--more", is_flag=True, help="Interactive pagination mode")
@click.option("--type", "-t", "agent_type", help="Filter by agent type (tool, rag, task)")
@click.option(
    "--name", "-n", "name_pattern", help="Filter by name (supports substring and wildcards)"
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.option(
    "--verbose", "-v", is_flag=True, help="Show verbose output including raw API response"
)
@click.pass_context
def list_agents(
    ctx: click.Context,
    limit: int,
    offset: int,
    page: int | None,
    more: bool,
    agent_type: str | None,
    name_pattern: str | None,
    output_format: str,
    verbose: bool,
) -> None:
    """List all agents in the environment."""
    # Combine global and command-level verbose (hierarchical)
    global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False
    verbose = global_verbose or verbose

    config_path = ctx.obj.get("config_path") if ctx.obj else None

    # VALIDATION: Check for conflicting options
    if page and offset:
        console.print("[red]Error:[/red] Cannot use both --page and --offset")
        raise SystemExit(1)

    if page and (agent_type or name_pattern):
        console.print("[red]Error:[/red] Cannot use --page with filters. Use --offset instead.")
        raise SystemExit(1)

    if page and page < 1:
        console.print("[red]Error:[/red] Page number must be >= 1")
        raise SystemExit(1)

    # Interactive mode (--more flag)
    if more:
        current_offset = offset

        try:
            # Try to load settings, but use None if not available
            settings = None
            try:
                config_file = config_path or find_config_file()
                settings = load_config(config_file)
            except Exception:
                pass  # Use default pagination settings

            profile = ctx.obj.get("profile") if ctx.obj else None
            settings_from_ctx = ctx.obj.get("settings") if ctx.obj else None
            with get_client(config_path, profile, settings_from_ctx) as client:
                while True:
                    # Fetch current page
                    result = fetch_agents_paginated(
                        client=client,
                        settings=settings,
                        offset=current_offset,
                        limit=limit,
                        page=None,  # Don't use page in interactive mode
                        agent_type=agent_type,
                        name_pattern=name_pattern,
                    )

                    # Display table
                    title_parts = [f"{len(result.agents)} agents"]
                    if result.total_count:
                        title_parts.append(f"of {result.total_count:,} total")
                    title = " ".join(title_parts)

                    table = Table(title=title)
                    table.add_column("ID", style="cyan", no_wrap=True)
                    table.add_column("Name", style="green")
                    table.add_column("Type", style="magenta")
                    table.add_column("Status")
                    table.add_column("Created At")

                    for agent in result.agents:
                        table.add_row(
                            str(agent.id),
                            agent.name,
                            agent.type,
                            agent.status,
                            agent.created_at[:10] if agent.created_at else "",
                        )

                    console.print(table)
                    show_pagination_info(result)

                    # Check if more results available
                    if not result.has_more:
                        console.print("\n[dim](End of results)[/dim]")
                        break

                    # Prompt for next page
                    console.print("\n[dim]Press SPACE for next page, 'q' to quit:[/dim] ", end="")
                    sys.stdout.flush()

                    key = get_single_keypress()

                    if key == " ":
                        current_offset += limit
                        console.print()  # New line
                        continue
                    elif key in ("q", "\x03"):  # q or Ctrl+C
                        console.print()
                        break
                    else:
                        console.print("\n[yellow]Invalid key. Press SPACE or 'q'[/yellow]")

        except APIError as e:
            console.print(f"[red]Error:[/red] {e}")
            raise SystemExit(1)

        return  # Exit after interactive mode

    # Normal (non-interactive) mode
    try:
        # Try to load settings, but use None if not available
        settings = None
        try:
            config_file = config_path or find_config_file()
            settings = load_config(config_file)
        except Exception:
            pass  # Use default pagination settings

        profile = ctx.obj.get("profile") if ctx.obj else None
        settings_from_ctx = ctx.obj.get("settings") if ctx.obj else None
        with get_client(config_path, profile, settings_from_ctx) as client:
            # Use pagination module (handles all API and filtering logic)
            result = fetch_agents_paginated(
                client=client,
                settings=settings,
                offset=offset,
                limit=limit,
                page=page,
                agent_type=agent_type,
                name_pattern=name_pattern,
            )

            # Verbose logging
            if verbose:
                console.print("\n[dim]═══ Pagination Details ═══[/dim]")
                console.print(f"[dim]Requested offset: {offset}[/dim]")
                console.print(f"[dim]Requested limit: {limit}[/dim]")
                if page:
                    console.print(f"[dim]Requested page: {page}[/dim]")
                console.print(f"[dim]Agents returned: {len(result.agents)}[/dim]")
                console.print(f"[dim]Has filters: {result.has_filters}[/dim]")
                if result.has_filters:
                    console.print(f"[dim]Pages fetched from server: {result.pages_fetched}[/dim]")
                console.print("[dim]════════════════════════[/dim]\n")

            # Output based on format
            if output_format == "json":
                # For JSON, create dict from result
                output_data = {
                    "agents": [a.model_dump(by_alias=True) for a in result.agents],
                    "pagination": {
                        "offset": result.offset,
                        "limit": result.limit,
                        "total_items": result.total_count,
                        "has_more": result.has_more,
                    },
                }
                output_json(output_data)

            elif output_format == "yaml":
                output_data = {
                    "agents": [a.model_dump(by_alias=True) for a in result.agents],
                    "pagination": {
                        "offset": result.offset,
                        "limit": result.limit,
                        "total_items": result.total_count,
                        "has_more": result.has_more,
                    },
                }
                output_yaml(output_data)

            else:
                # Table format
                title_parts = [f"{len(result.agents)} agents"]
                if result.total_count:
                    title_parts.append(f"of {result.total_count:,} total")
                title = " ".join(title_parts)

                table = Table(title=title)
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("Name", style="green")
                table.add_column("Type", style="magenta")
                table.add_column("Status")
                table.add_column("Created At")

                for agent in result.agents:
                    table.add_row(
                        str(agent.id),
                        agent.name,
                        agent.type,
                        agent.status,
                        agent.created_at[:10] if agent.created_at else "",
                    )

                console.print(table)

                # Show pagination info
                show_pagination_info(result)

                # Show next page command (if not --more mode)
                if not more:
                    show_next_page_command(result, use_page=bool(page))

    except APIError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@agents.command("get")
@click.argument("agent_id")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.pass_context
def get_agent(ctx: click.Context, agent_id: str, output_format: str) -> None:
    """Get details of a specific agent."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    try:
        profile = ctx.obj.get("profile") if ctx.obj else None

        settings_from_ctx = ctx.obj.get("settings") if ctx.obj else None

        with get_client(config_path, profile, settings_from_ctx) as client:
            agent_service = AgentService(client)
            result = agent_service.get_agent(agent_id)

            if result is None:
                console.print(f"[red]Agent not found:[/red] {agent_id}")
                raise SystemExit(1)

            if output_format == "json":
                output_json(result.model_dump(by_alias=True))
            elif output_format == "yaml":
                output_yaml(result.model_dump(by_alias=True))
            else:
                agent = result.agent
                version = result.version

                console.print(f"[bold cyan]Agent: {agent.name}[/bold cyan]")
                console.print(f"  ID: {agent.id}")
                console.print(f"  Type: {agent.type}")
                console.print(f"  Description: {agent.description}")
                console.print(f"  Status: {agent.status}")
                console.print(f"  Created: {agent.created_at}")
                console.print(f"  Modified: {agent.modified_at}")
                console.print()
                console.print("[bold green]Current Version:[/bold green]")
                console.print(f"  Version ID: {version.id}")
                console.print(f"  Number: {version.number}")
                if version.version_label:
                    console.print(f"  Label: {version.version_label}")
                if version.notes:
                    console.print(f"  Notes: {version.notes}")
                console.print()
                console.print("[bold yellow]Configuration:[/bold yellow]")
                console.print_json(json.dumps(version.config, default=str, indent=2))

    except NotFoundError:
        console.print(f"[red]Agent not found:[/red] {agent_id}")
        raise SystemExit(1)
    except APIError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@agents.command("create")
@click.option("--name", "-n", required=True, help="Agent name")
@click.option("--description", "-d", required=True, help="Agent description")
@click.option(
    "--type", "-t", "agent_type", required=True, help="Agent type (base, tool, rag, task)"
)
@click.option(
    "--agent-config",
    "-c",
    "config_file",
    required=True,
    type=click.Path(exists=True),
    help="Path to JSON agent configuration file",
)
@click.option("--version-label", "-v", help="Version label (e.g., v1.0)")
@click.option("--notes", help="Version notes")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.pass_context
def create_agent(
    ctx: click.Context,
    name: str,
    description: str,
    agent_type: str,
    config_file: str,
    version_label: str | None,
    notes: str | None,
    output_format: str,
) -> None:
    """Create a new agent."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    # Load config from file
    try:
        with open(config_file) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON in config file:[/red] {e}")
        raise SystemExit(1)

    try:
        profile = ctx.obj.get("profile") if ctx.obj else None

        settings_from_ctx = ctx.obj.get("settings") if ctx.obj else None

        with get_client(config_path, profile, settings_from_ctx) as client:
            agent_service = AgentService(client)
            result = agent_service.create_agent(
                {
                    "name": name,
                    "description": description,
                    "agent_type": agent_type,
                    "config": config,
                    "version_label": version_label,
                    "notes": notes,
                }
            )

            # AgentService always returns AgentVersion
            if output_format == "json":
                output_json(result.model_dump(by_alias=True))
            elif output_format == "yaml":
                output_yaml(result.model_dump(by_alias=True))
            else:
                console.print("[green]✓[/green] Agent created successfully!")
                console.print(f"  ID: [cyan]{result.agent.id}[/cyan]")
                console.print(f"  Name: {result.agent.name}")
                console.print(f"  Type: {result.agent.type}")
                console.print(f"  Version: {result.version.number}")

    except APIError as e:
        console.print(f"[red]Error creating agent:[/red] {e}")
        raise SystemExit(1)


@agents.command("update")
@click.argument("agent_id")
@click.option(
    "--agent-config",
    "-c",
    "config_file",
    type=click.Path(exists=True),
    help="Path to JSON agent configuration file",
)
@click.option("--version-label", "-v", help="Version label (e.g., v2.0)")
@click.option("--notes", help="Version notes")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.pass_context
def update_agent(
    ctx: click.Context,
    agent_id: str,
    config_file: str | None,
    version_label: str | None,
    notes: str | None,
    output_format: str,
) -> None:
    """Update an agent (creates a new version)."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    config = None
    if config_file:
        try:
            with open(config_file) as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            console.print(f"[red]Invalid JSON in config file:[/red] {e}")
            raise SystemExit(1)

    try:
        profile = ctx.obj.get("profile") if ctx.obj else None

        settings_from_ctx = ctx.obj.get("settings") if ctx.obj else None

        with get_client(config_path, profile, settings_from_ctx) as client:
            agent_service = AgentService(client)
            result = agent_service.update_agent(
                agent_id,
                {
                    "config": config,
                    "version_label": version_label,
                    "notes": notes,
                },
            )

            # Handle the case where result is a raw dict or an AgentVersion
            if isinstance(result, dict) and not hasattr(result, "agent"):
                if output_format == "json":
                    output_json(result)
                elif output_format == "yaml":
                    output_yaml(result)
                else:
                    console.print("[green]✓[/green] Agent updated successfully!")

                    # Extract information directly from the response if available
                    agent_id = result.get("id", "00000000-0000-0000-0000-000000000000")
                    agent_name = result.get("name", "Unknown")
                    agent_type = result.get("type", "unknown")
                    # Try to get the version info from currentVersionId if present
                    current_version_id = result.get("currentVersionId", "")

                    console.print(f"  ID: [cyan]{agent_id}[/cyan]")
                    console.print(f"  Name: {agent_name}")
                    console.print(f"  Type: {agent_type}")
                    console.print("  New Version Created")
                    if current_version_id:
                        console.print(f"  Version ID: {current_version_id}")
            else:
                # Regular handling for AgentVersion object
                if output_format == "json":
                    output_json(result.model_dump(by_alias=True))
                elif output_format == "yaml":
                    output_yaml(result.model_dump(by_alias=True))
                else:
                    console.print("[green]✓[/green] Agent updated successfully!")
                    console.print(f"  New Version: {result.version.number}")
                    if result.version.version_label:
                        console.print(f"  Label: {result.version.version_label}")

    except NotFoundError:
        console.print(f"[red]Agent not found:[/red] {agent_id}")
        raise SystemExit(1)
    except APIError as e:
        console.print(f"[red]Error updating agent:[/red] {e}")
        raise SystemExit(1)


@agents.command("patch")
@click.argument("agent_id")
@click.option("--name", "-n", help="New agent name")
@click.option("--description", "-d", help="New agent description")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.pass_context
def patch_agent(
    ctx: click.Context,
    agent_id: str,
    name: str | None,
    description: str | None,
    output_format: str,
) -> None:
    """Patch an agent's name/description (no new version)."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    if not name and not description:
        console.print("[yellow]Warning:[/yellow] No changes specified")
        return

    try:
        profile = ctx.obj.get("profile") if ctx.obj else None

        settings_from_ctx = ctx.obj.get("settings") if ctx.obj else None

        with get_client(config_path, profile, settings_from_ctx) as client:
            agent_service = AgentService(client)
            result = agent_service.patch_agent(agent_id, name=name, description=description)

            if output_format == "json":
                output_json(result.model_dump(by_alias=True))
            elif output_format == "yaml":
                output_yaml(result.model_dump(by_alias=True))
            else:
                console.print("[green]✓[/green] Agent patched successfully!")
                console.print(f"  Name: {result.name}")
                console.print(f"  Description: {result.description}")

    except NotFoundError:
        console.print(f"[red]Agent not found:[/red] {agent_id}")
        raise SystemExit(1)
    except APIError as e:
        console.print(f"[red]Error patching agent:[/red] {e}")
        raise SystemExit(1)


@agents.command("delete")
@click.argument("agent_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def delete_agent(ctx: click.Context, agent_id: str, yes: bool) -> None:
    """Delete an agent."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    if not yes and not click.confirm(f"Are you sure you want to delete agent {agent_id}?"):
        console.print("Cancelled")
        return

    try:
        profile = ctx.obj.get("profile") if ctx.obj else None

        settings_from_ctx = ctx.obj.get("settings") if ctx.obj else None

        with get_client(config_path, profile, settings_from_ctx) as client:
            agent_service = AgentService(client)
            agent_service.delete_agent(agent_id)
            console.print(f"[green]✓[/green] Agent deleted: {agent_id}")

    except NotFoundError:
        console.print(f"[red]Agent not found:[/red] {agent_id}")
        raise SystemExit(1)
    except APIError as e:
        console.print(f"[red]Error deleting agent:[/red] {e}")
        raise SystemExit(1)


@agents.command("edit")
@click.argument("agent_id")
@click.option("--editor", help="Override editor selection (e.g., 'vim', 'code --wait')")
@click.option("--keep-temp", is_flag=True, help="Keep temp file after completion for debugging")
@click.option("--notes", help="Version notes for the update")
@click.pass_context
def edit_agent(
    ctx: click.Context,
    agent_id: str,
    editor: str | None,
    keep_temp: bool,
    notes: str | None,
) -> None:
    """Edit an agent configuration interactively in your text editor.

    This command:
    1. Fetches the current agent configuration
    2. Creates a temporary JSON file with the config
    3. Opens your text editor
    4. After you save and close, prompts for confirmation
    5. Creates a new agent version with your changes
    """
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    profile = ctx.obj.get("profile") if ctx.obj else None
    settings_from_ctx = ctx.obj.get("settings") if ctx.obj else None

    # Load full settings to get editor configuration
    settings = settings_from_ctx
    if not settings:
        try:
            config_file = config_path or find_config_file()
            if profile:
                settings = load_config_with_profile(config_file, profile=profile)
            else:
                settings = load_config(config_file)
        except Exception:
            # Create minimal settings if config doesn't exist
            settings = None

    temp_file = None

    try:
        # Step 1: Fetch current agent configuration
        console.print(f"[cyan]Fetching agent {agent_id}...[/cyan]")

        with get_client(config_path, profile, settings_from_ctx) as client:
            agent_service = AgentService(client)
            result = agent_service.get_agent(agent_id)

            if result is None:
                console.print(f"[red]Agent not found:[/red] {agent_id}")
                raise SystemExit(1)

            agent = result.agent
            current_version = result.version

            console.print(f"[green]✓[/green] Loaded: {agent.name}")
            console.print(
                f"  Current version: {current_version.version_label or current_version.number}"
            )

            # Step 2: Create temp file with current config
            # Auto-increment version for user convenience
            suggested_version = increment_version(
                current_version.version_label or f"v{current_version.number}"
            )

            temp_file = create_agent_edit_tempfile(
                agent_id=str(agent.id),
                version_label=suggested_version,
                config=current_version.config,
            )

            console.print(f"\n[dim]Temp file: {temp_file}[/dim]")
            console.print(f"[yellow]Suggested new version: {suggested_version}[/yellow]")
            console.print("[dim](You can change the versionLabel in the editor)[/dim]\n")

            # Step 3: Determine which editor to use
            if settings:
                editor_cmd = get_editor(settings, override=editor)
            else:
                # Fallback if no settings available
                import os
                import platform

                if editor:
                    editor_cmd = editor
                elif os.environ.get("VISUAL"):
                    editor_cmd = os.environ["VISUAL"]
                elif os.environ.get("EDITOR"):
                    editor_cmd = os.environ["EDITOR"]
                elif platform.system() == "Windows":
                    editor_cmd = "notepad.exe"
                else:
                    editor_cmd = "vi"

            console.print(f"[cyan]Opening editor: {editor_cmd}[/cyan]")
            console.print("[dim]Edit the configuration, then save and close the editor...[/dim]\n")

            # Step 4: Open editor
            try:
                exit_code = open_editor(temp_file, editor_cmd)

                if exit_code != 0:
                    console.print(
                        f"\n[yellow]Warning:[/yellow] Editor exited with code {exit_code}"
                    )
                    if not click.confirm("Continue anyway?"):
                        console.print("Cancelled")
                        cleanup_tempfile(temp_file, keep=keep_temp)
                        raise SystemExit(0)

            except FileNotFoundError as e:
                console.print(f"\n[red]Error:[/red] {e}")
                console.print("\nYou can:")
                console.print("  • Install the editor")
                console.print("  • Use --editor flag to specify a different editor")
                console.print("  • Set VISUAL or EDITOR environment variable")
                console.print("  • Configure 'editor' in config.yaml")
                cleanup_tempfile(temp_file, keep=keep_temp)
                raise SystemExit(1)

            except Exception as e:
                console.print(f"\n[red]Error launching editor:[/red] {e}")
                cleanup_tempfile(temp_file, keep=keep_temp)
                raise SystemExit(1)

            # Step 5: Read and validate edited file
            console.print("\n[cyan]Reading changes...[/cyan]")

            try:
                new_version_label, new_config = read_agent_edit_tempfile(temp_file)
            except json.JSONDecodeError as e:
                console.print(f"[red]Invalid JSON:[/red] {e}")
                console.print("\nThe file contains invalid JSON. Please fix and try again.")
                if keep_temp:
                    console.print(f"Temp file kept at: {temp_file}")
                else:
                    cleanup_tempfile(temp_file)
                raise SystemExit(1)
            except (KeyError, ValueError) as e:
                console.print(f"[red]Validation error:[/red] {e}")
                if keep_temp:
                    console.print(f"Temp file kept at: {temp_file}")
                else:
                    cleanup_tempfile(temp_file)
                raise SystemExit(1)

            # Step 6: Show summary and confirm
            console.print("[green]✓[/green] Changes validated")
            console.print("\n[bold]Summary of changes:[/bold]")
            console.print(f"  Agent: {agent.name} ({agent_id})")
            console.print(f"  New version label: {new_version_label}")
            console.print(f"  Config keys: {', '.join(new_config.keys())}")

            if notes:
                console.print(f"  Notes: {notes}")

            console.print()

            if not click.confirm("Create new version with these changes?"):
                console.print("Cancelled")
                cleanup_tempfile(temp_file, keep=keep_temp)
                raise SystemExit(0)

            # Step 7: Create new version via API
            console.print("\n[cyan]Creating new agent version...[/cyan]")

            agent_update = AgentUpdate(
                config=new_config,
                version_label=new_version_label,
                notes=notes or "Updated via interactive editor",
            )

            update_result = agent_service.update_agent(
                str(agent.id), agent_update.model_dump(by_alias=True, exclude_none=True)
            )

            # Step 8: Success!
            console.print("[green]✓ Agent updated successfully![/green]")

            if hasattr(update_result, "version"):
                console.print(f"  New version: {update_result.version.number}")
                console.print(f"  Version label: {update_result.version.version_label}")
            else:
                console.print(f"  Version label: {new_version_label}")

            # Cleanup
            cleanup_tempfile(temp_file, keep=keep_temp)
            if keep_temp:
                console.print(f"\n[dim]Temp file kept at: {temp_file}[/dim]")

    except NotFoundError:
        console.print(f"[red]Agent not found:[/red] {agent_id}")
        if temp_file:
            cleanup_tempfile(temp_file, keep=keep_temp)
        raise SystemExit(1)

    except APIError as e:
        console.print(f"[red]API Error:[/red] {e}")
        if temp_file:
            cleanup_tempfile(temp_file, keep=keep_temp)
        raise SystemExit(1)

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Cancelled by user[/yellow]")
        if temp_file:
            cleanup_tempfile(temp_file, keep=keep_temp)
        raise SystemExit(0)


@agents.command("types")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.pass_context
def list_agent_types(ctx: click.Context, output_format: str) -> None:
    """List available agent types."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    try:
        profile = ctx.obj.get("profile") if ctx.obj else None

        settings_from_ctx = ctx.obj.get("settings") if ctx.obj else None

        with get_client(config_path, profile, settings_from_ctx) as client:
            agent_service = AgentService(client)
            result = agent_service.list_agent_types()

            if output_format == "json":
                output_json(result.model_dump(by_alias=True))
            elif output_format == "yaml":
                output_yaml(result.model_dump(by_alias=True))
            else:
                table = Table(title="Agent Types")
                table.add_column("Type", style="cyan")
                table.add_column("Description")

                for agent_type in result.agent_types:
                    table.add_row(agent_type.type, agent_type.description)

                console.print(table)

    except APIError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
