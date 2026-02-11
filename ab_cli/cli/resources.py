"""CLI commands for listing models and guardrails."""

import json

import click
import yaml
from rich.console import Console
from rich.table import Table

from ab_cli.api.client import AgentBuilderClient
from ab_cli.api.exceptions import APIError
from ab_cli.config.loader import find_config_file, load_config

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
def resources() -> None:
    """Manage resources (list models, guardrails)."""
    pass


@resources.command("models")
@click.option("--agent-type", "-t", help="Filter by agent type (tool, rag, task)")
@click.option("--limit", "-l", default=50, help="Maximum number of models to return")
@click.option("--offset", "-o", default=0, help="Offset for pagination")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json", "yaml"]),
              default="table", help="Output format")
@click.pass_context
def list_models(ctx: click.Context, agent_type: str | None, limit: int, offset: int, output_format: str) -> None:
    """List supported LLM models.

    If --agent-type is specified, only models compatible with that agent type are returned.
    """
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    try:
        with get_client(config_path) as client:
            result = client.list_models(agent_type=agent_type, limit=limit, offset=offset)

            if output_format == "json":
                output_json(result.model_dump(by_alias=True))
            elif output_format == "yaml":
                output_yaml(result.model_dump(by_alias=True))
            else:
                # Table format
                table = Table(title=f"LLM Models ({result.pagination.total_items} total)")
                table.add_column("ID", style="cyan", no_wrap=True)
                table.add_column("Name", style="green")
                table.add_column("Badge", style="magenta")
                table.add_column("Agent Types", style="yellow")
                table.add_column("Regions")
                table.add_column("Deprecated")

                for model in result.models:
                    agent_types = ", ".join(model.agent_types)
                    regions = ", ".join(model.regions[:3]) + ("..." if len(model.regions) > 3 else "")
                    deprecated = "Yes" if model.deprecation_status.deprecated else "No"

                    table.add_row(
                        model.id,
                        model.name,
                        model.badge,
                        agent_types,
                        regions,
                        deprecated,
                    )

                console.print(table)

                # Show extra model details if there are models
                if result.models and output_format == "table":
                    model = result.models[0]
                    console.print("\n[bold]Capabilities:[/bold]")
                    caps_table = Table(show_header=False)
                    caps_table.add_column("Capability")
                    caps_table.add_column("Value")

                    for key, value in model.capabilities.items():
                        caps_table.add_row(key, str(value))

                    console.print(caps_table)
                    console.print("\nFor more details, use: [bold]--format json[/bold]")

    except APIError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@resources.command("guardrails")
@click.option("--limit", "-l", default=50, help="Maximum number of guardrails to return")
@click.option("--offset", "-o", default=0, help="Offset for pagination")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "json", "yaml"]),
              default="table", help="Output format")
@click.pass_context
def list_guardrails(ctx: click.Context, limit: int, offset: int, output_format: str) -> None:
    """List supported guardrails."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    try:
        with get_client(config_path) as client:
            result = client.list_guardrails(limit=limit, offset=offset)

            if output_format == "json":
                output_json(result.model_dump(by_alias=True))
            elif output_format == "yaml":
                output_yaml(result.model_dump(by_alias=True))
            else:
                # Table format
                table = Table(title=f"Guardrails ({result.pagination.total_items} total)")
                table.add_column("Name", style="cyan")
                table.add_column("Description")

                for guardrail in result.guardrails:
                    table.add_row(guardrail.name, guardrail.description)

                console.print(table)

    except APIError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
