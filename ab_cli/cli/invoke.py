"""CLI commands for agent invocation."""

import json
import sys

import click
import yaml
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from ab_cli.api.client import AgentBuilderClient
from ab_cli.api.exceptions import APIError, NotFoundError
from ab_cli.config.loader import find_config_file, load_config
from ab_cli.models.invocation import (
    ChatMessage,
    InvokeRequest,
    InvokeResponse,
    InvokeTaskRequest,
)

console = Console()
error_console = Console(stderr=True)


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


def format_response(
    response: InvokeResponse, output_format: str = "table", verbose: bool = False
) -> None:
    """Format and display an invocation response."""
    if output_format == "json":
        output_json(response.model_dump())
        return
    elif output_format == "yaml":
        output_yaml(response.model_dump())
        return

    # Format text response (table/default format)
    console.print()
    console.print("[bold cyan]Response:[/bold cyan]")
    console.print(response.response)
    console.print()

    # Display metadata if available
    if response.usage:
        console.print("[dim]Token usage:[/dim]")
        for key, value in response.usage.items():
            console.print(f"  {key}: {value}")

    if response.finish_reason:
        console.print(f"[dim]Finish reason: {response.finish_reason}[/dim]")

    # Display raw response in verbose mode
    if verbose:
        console.print()
        console.print("[bold magenta]Raw API Response:[/bold magenta]")
        console.print_json(response.model_dump_json())


@click.group()
def invoke() -> None:
    """Invoke agents (chat, task, interactive)."""
    pass


@invoke.command("chat")
@click.argument("agent_id")
@click.argument("version_id", required=False, default="latest")
@click.option("--message", "-m", help="Message to send")
@click.option("--message-file", type=click.Path(exists=True), help="Read message from file")
@click.option("--stream", "-s", is_flag=True, help="Enable streaming")
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
def chat(
    ctx: click.Context,
    agent_id: str,
    version_id: str,
    message: str | None,
    message_file: str | None,
    stream: bool,
    output_format: str,
    verbose: bool,
) -> None:
    """Invoke agent with a chat message."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    # Get message content from options or file
    if not message and not message_file:
        error_console.print("[red]Error: No message provided[/red]")
        error_console.print("Use --message or --message-file to provide input")
        sys.exit(1)

    if message_file:
        try:
            with open(message_file) as f:
                message = f.read()
        except Exception as e:
            error_console.print(f"[red]Error reading file:[/red] {e}")
            sys.exit(1)

    # Prepare request - ensure message is not None before using it
    # (we've already checked above, but this helps mypy understand)
    if not message:
        error_console.print("[red]Error: No message provided[/red]")
        sys.exit(1)

    messages = [ChatMessage(role="user", content=message)]
    request = InvokeRequest(
        messages=messages, hxqlQuery=None, hybridSearch=None, enableDeepSearch=False
    )

    try:
        with get_client(config_path) as client:
            if stream:
                # Streaming mode
                console.print(f"[dim]Invoking agent {agent_id} with streaming...[/dim]")
                full_response = ""

                with Live(console=console, refresh_per_second=10) as live:
                    try:
                        for event in client.invoke_agent_stream(agent_id, version_id, request):
                            if event.event == "text" and event.data:
                                full_response += event.data
                                live.update(Markdown(full_response))
                            elif event.event == "error" and event.data:
                                raise APIError(event.data)
                    except KeyboardInterrupt:
                        console.print("\n[yellow]Stream interrupted[/yellow]")

                console.print("\n[green]✓[/green] Streaming complete")

            else:
                # Standard mode
                console.print(f"[dim]Invoking agent {agent_id}...[/dim]")
                response = client.invoke_agent(agent_id, version_id, request)
                format_response(response, output_format, verbose)

    except NotFoundError:
        error_console.print(f"[red]Agent not found:[/red] {agent_id}")
        sys.exit(1)
    except APIError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@invoke.command("task")
@click.argument("agent_id")
@click.argument("version_id", required=False, default="latest")
@click.option("--input", "-i", "input_file", required=True, type=click.Path(exists=True))
@click.option("--stream", "-s", is_flag=True, help="Enable streaming")
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
def task(
    ctx: click.Context,
    agent_id: str,
    version_id: str,
    input_file: str,
    stream: bool,
    output_format: str,
    verbose: bool,
) -> None:
    """Invoke task agent with structured input."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None

    # Load input file
    try:
        with open(input_file) as f:
            inputs = json.load(f)
    except json.JSONDecodeError as e:
        error_console.print(f"[red]Invalid JSON in input file:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        error_console.print(f"[red]Error reading input file:[/red] {e}")
        sys.exit(1)

    # Prepare request
    request = InvokeTaskRequest(inputs=inputs)

    try:
        with get_client(config_path) as client:
            if stream:
                # Streaming mode
                console.print(f"[dim]Invoking task agent {agent_id} with streaming...[/dim]")
                full_response = ""

                with Live(console=console, refresh_per_second=10) as live:
                    try:
                        for event in client.invoke_task_stream(agent_id, version_id, request):
                            if event.event == "text" and event.data:
                                full_response += event.data
                                live.update(Markdown(full_response))
                            elif event.event == "error" and event.data:
                                raise APIError(event.data)
                    except KeyboardInterrupt:
                        console.print("\n[yellow]Stream interrupted[/yellow]")

                console.print("\n[green]✓[/green] Streaming complete")

            else:
                # Standard mode
                console.print(f"[dim]Invoking task agent {agent_id}...[/dim]")
                response = client.invoke_task(agent_id, version_id, request)
                format_response(response, output_format, verbose)

    except NotFoundError:
        error_console.print(f"[red]Agent not found:[/red] {agent_id}")
        sys.exit(1)
    except APIError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@invoke.command("interactive")
@click.argument("agent_id")
@click.argument("version_id", required=False, default="latest")
@click.pass_context
def interactive(ctx: click.Context, agent_id: str, version_id: str) -> None:
    """Start interactive chat session (REPL)."""
    config_path = ctx.obj.get("config_path") if ctx.obj else None
    messages: list[ChatMessage] = []  # Chat history

    try:
        with get_client(config_path) as client:
            # Verify agent exists before starting session
            agent = client.get_agent(agent_id, version_id)

            # Setup interactive session
            console.print(
                Panel.fit(
                    f"Interactive session with [bold]{agent.agent.name}[/bold]\n"
                    "Type 'exit' or 'quit' to end, 'clear' to reset history",
                    title="Agent Chat",
                    border_style="cyan",
                )
            )

            # Main REPL loop
            while True:
                try:
                    # Get user input
                    user_input = Prompt.ask("[bold green]You")

                    if user_input.lower() in ("exit", "quit"):
                        console.print("[dim]Session ended.[/dim]")
                        break
                    elif user_input.lower() == "clear":
                        messages = []
                        console.print("[dim]Conversation history cleared.[/dim]")
                        continue
                    elif not user_input.strip():
                        continue

                    # Add user message to history
                    messages.append(ChatMessage(role="user", content=user_input))

                    # Invoke agent
                    request = InvokeRequest(
                        messages=messages, hxqlQuery=None, hybridSearch=None, enableDeepSearch=False
                    )
                    console.print("[bold cyan]Agent[/bold cyan]", end=" ")

                    # Stream response
                    full_response = ""
                    try:
                        for event in client.invoke_agent_stream(agent_id, version_id, request):
                            if event.event == "text" and event.data:
                                console.print(event.data, end="")
                                full_response += event.data
                            elif event.event == "error" and event.data:
                                console.print(f"\n[red]Error: {event.data}[/red]")
                                break
                    except KeyboardInterrupt:
                        console.print("\n[yellow]Response interrupted[/yellow]")
                        continue

                    console.print()  # New line after response

                    # Add response to history
                    if full_response:
                        messages.append(ChatMessage(role="assistant", content=full_response))

                except APIError as e:
                    error_console.print(f"\n[red]Error:[/red] {e}")
                except Exception as e:
                    error_console.print(f"\n[red]Unexpected error:[/red] {e}")

    except NotFoundError:
        error_console.print(f"[red]Agent not found:[/red] {agent_id}")
        sys.exit(1)
    except APIError as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[dim]Session interrupted.[/dim]")
