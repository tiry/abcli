"""CLI commands for agent management."""

import json

import click
import yaml
from rich.console import Console
from rich.table import Table

from ab_cli.api.client import AgentBuilderClient
from ab_cli.api.exceptions import APIError, NotFoundError
from ab_cli.config.loader import find_config_file, load_config
from ab_cli.models.agent import AgentCreate, AgentPatch, AgentUpdate

console = Console()


def get_client(config_path: str | None = None) -> AgentBuilderClient:
    """Get an authenticated API client."""
    config_file = config_path or find_config_file()
    settings = load_config(config_file)
    return AgentBuilderClient(settings)


def output_json(data: dict) -> None:
    """Output data as JSON."""
    console.print_json(json.dumps(data, default=str))


def output_yaml(data: dict) -> None:
    """Output data as YAML."""
    console.print(yaml.dump(data, default_flow_style=False))


@click.group()
def agents() -> None:
    """Manage agents (list, create, update, delete)."""
    pass


@agents.command("list")
@click.option("--limit", "-l", default=50, help="Maximum number of agents to return")
@click.option("--offset", "-o", default=0, help="Offset for pagination")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.pass_context
def list_agents(ctx: click.Context, limit: int, offset: int, output_format: str) -> None:
    """List all agents in the environment."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    try:
        with get_client(config_path) as client:
            result = client.list_agents(limit=limit, offset=offset)

            if output_format == "json":
                output_json(result.model_dump(by_alias=True))
            elif output_format == "yaml":
                output_yaml(result.model_dump(by_alias=True))
            else:
                # Table format
                table = Table(title=f"Agents ({result.pagination.total_items} total)")
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
        with get_client(config_path) as client:
            result = client.get_agent(agent_id)

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

    agent_create = AgentCreate(
        name=name,
        description=description,
        agent_type=agent_type,
        config=config,
        version_label=version_label,
        notes=notes,
    )

    try:
        with get_client(config_path) as client:
            result = client.create_agent(agent_create)

            # Handle the case where result is a raw dict (not an AgentVersion)
            if isinstance(result, dict):
                if output_format == "json":
                    output_json(result)
                elif output_format == "yaml":
                    output_yaml(result)
                else:
                    console.print("[green]✓[/green] Agent created successfully!")
                    # Extract information directly from the response if available
                    agent_id = result.get("id", "00000000-0000-0000-0000-000000000000")
                    agent_name = result.get("name", "Unknown")
                    agent_type = result.get("type", "unknown")
                    # Try to get version information
                    version = "1"  # Default

                    console.print(f"  ID: [cyan]{agent_id}[/cyan]")
                    console.print(f"  Name: {agent_name}")
                    console.print(f"  Type: {agent_type}")
                    console.print(f"  Version: {version}")
            else:
                # Regular handling for AgentVersion object
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

    agent_update = AgentUpdate(
        config=config,
        version_label=version_label,
        notes=notes,
    )

    try:
        with get_client(config_path) as client:
            result = client.update_agent(agent_id, agent_update)

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

    patch = AgentPatch(name=name, description=description)

    try:
        with get_client(config_path) as client:
            result = client.patch_agent(agent_id, patch)

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
        with get_client(config_path) as client:
            client.delete_agent(agent_id)
            console.print(f"[green]✓[/green] Agent deleted: {agent_id}")

    except NotFoundError:
        console.print(f"[red]Agent not found:[/red] {agent_id}")
        raise SystemExit(1)
    except APIError as e:
        console.print(f"[red]Error deleting agent:[/red] {e}")
        raise SystemExit(1)


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
        with get_client(config_path) as client:
            result = client.list_agent_types()

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
