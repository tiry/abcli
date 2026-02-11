"""CLI commands for version management."""

import json

import click
import yaml
from rich.console import Console
from rich.table import Table

from ab_cli.api.client import AgentBuilderClient
from ab_cli.api.exceptions import APIError, NotFoundError
from ab_cli.config.loader import find_config_file, load_config
from ab_cli.models.agent import VersionCreate

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
def versions() -> None:
    """Manage agent versions (list, get, create)."""
    pass


@versions.command("list")
@click.argument("agent_id")
@click.option("--limit", "-l", default=50, help="Maximum number of versions to return")
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
def list_versions(
    ctx: click.Context, agent_id: str, limit: int, offset: int, output_format: str
) -> None:
    """List all versions of an agent."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    try:
        with get_client(config_path) as client:
            result = client.list_versions(agent_id, limit=limit, offset=offset)

            if output_format == "json":
                output_json(result.model_dump(by_alias=True))
            elif output_format == "yaml":
                output_yaml(result.model_dump(by_alias=True))
            else:
                agent = result.agent
                console.print(f"[bold cyan]Agent: {agent.name}[/bold cyan] (ID: {agent.id})")
                console.print()

                table = Table(title=f"Versions ({result.pagination.total_items} total)")
                table.add_column("Version ID", style="cyan", no_wrap=True)
                table.add_column("Number", style="green")
                table.add_column("Label")
                table.add_column("Notes")
                table.add_column("Created At")
                table.add_column("Created By")

                for version in result.versions:
                    table.add_row(
                        str(version.id),
                        str(version.number),
                        version.version_label or "-",
                        (version.notes[:30] + "...")
                        if version.notes and len(version.notes) > 30
                        else (version.notes or "-"),
                        version.created_at[:10] if version.created_at else "",
                        version.created_by,
                    )

                console.print(table)

    except NotFoundError:
        console.print(f"[red]Agent not found:[/red] {agent_id}")
        raise SystemExit(1)
    except APIError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@versions.command("get")
@click.argument("agent_id")
@click.argument("version_id")
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(["table", "json", "yaml"]),
    default="table",
    help="Output format",
)
@click.pass_context
def get_version(ctx: click.Context, agent_id: str, version_id: str, output_format: str) -> None:
    """Get details of a specific version."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    try:
        with get_client(config_path) as client:
            result = client.get_version(agent_id, version_id)

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
                console.print()
                console.print(f"[bold green]Version {version.number}:[/bold green]")
                console.print(f"  Version ID: {version.id}")
                if version.version_label:
                    console.print(f"  Label: {version.version_label}")
                if version.notes:
                    console.print(f"  Notes: {version.notes}")
                console.print(f"  Created At: {version.created_at}")
                console.print(f"  Created By: {version.created_by}")
                console.print()
                console.print("[bold yellow]Configuration:[/bold yellow]")
                console.print_json(json.dumps(version.config, default=str, indent=2))

    except NotFoundError:
        console.print(f"[red]Resource not found:[/red] Agent {agent_id} or Version {version_id}")
        raise SystemExit(1)
    except APIError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@versions.command("create")
@click.argument("agent_id")
@click.option(
    "--config",
    "-c",
    "config_file",
    required=True,
    type=click.Path(exists=True),
    help="Path to JSON config file",
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
def create_version(
    ctx: click.Context,
    agent_id: str,
    config_file: str,
    version_label: str | None,
    notes: str | None,
    output_format: str,
) -> None:
    """Create a new version for an agent."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    # Load config from file
    try:
        with open(config_file) as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        console.print(f"[red]Invalid JSON in config file:[/red] {e}")
        raise SystemExit(1)

    version_create = VersionCreate(
        config=config,
        version_label=version_label,
        notes=notes,
    )

    try:
        with get_client(config_path) as client:
            result = client.create_version(agent_id, version_create)

            if output_format == "json":
                output_json(result.model_dump(by_alias=True))
            elif output_format == "yaml":
                output_yaml(result.model_dump(by_alias=True))
            else:
                console.print("[green]✓[/green] Version created successfully!")
                console.print(f"  Agent: {result.agent.name}")
                console.print(f"  Version ID: [cyan]{result.version.id}[/cyan]")
                console.print(f"  Version Number: {result.version.number}")
                if result.version.version_label:
                    console.print(f"  Label: {result.version.version_label}")

    except NotFoundError:
        console.print(f"[red]Agent not found:[/red] {agent_id}")
        raise SystemExit(1)
    except APIError as e:
        console.print(f"[red]Error creating version:[/red] {e}")
        raise SystemExit(1)
