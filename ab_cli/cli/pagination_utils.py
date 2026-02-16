"""Display utilities for pagination in CLI commands."""

import sys
import termios
import tty

from rich.console import Console

from ab_cli.api.pagination import PaginatedResult

console = Console()


def get_single_keypress() -> str:
    """Get a single keypress from the user without requiring Enter.

    Returns:
        The key that was pressed.
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        key = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return key


def show_pagination_info(result: PaginatedResult) -> None:
    """Display pagination information below a table.

    Args:
        result: Paginated result to display info for.
    """
    start = result.offset + 1
    end = result.offset + len(result.agents)

    if result.has_filters:
        # Filtered results - total unknown
        # Build filter description
        filter_parts = []
        if result.agent_type:
            filter_parts.append(f"type: {result.agent_type}")
        if result.name_pattern:
            filter_parts.append(f"name: {result.name_pattern}")

        filter_text = f" (filtered by {', '.join(filter_parts)})" if filter_parts else " (filtered)"
        console.print(f"\nShowing: {start}-{end} of ???{filter_text} | Page size: {result.limit}")
    else:
        # Unfiltered results - show full pagination
        current_page = (result.offset // result.limit) + 1
        total_pages = (
            (result.total_count + result.limit - 1) // result.limit
            if result.total_count and result.total_count > 0
            else 1
        )
        console.print(
            f"\nPage: {current_page}/{total_pages} | "
            f"Showing: {start}-{end} of {result.total_count:,} | "
            f"Page size: {result.limit}"
        )


def show_next_page_command(result: PaginatedResult, use_page: bool = False) -> None:
    """Show the command to run for the next page.

    Args:
        result: Paginated result.
        use_page: Whether to use --page instead of --offset.
    """
    # Check if we're at the end
    if not result.has_more:
        console.print("[dim](End of results)[/dim]")
        return

    # Build next page command
    next_offset = result.offset + result.limit

    if use_page:
        next_page = (next_offset // result.limit) + 1
        cmd = f"ab agents list --page {next_page} -l {result.limit}"
    else:
        cmd = f"ab agents list --offset {next_offset} -l {result.limit}"

    # Add filters if present
    if result.agent_type:
        cmd += f" --type {result.agent_type}"
    if result.name_pattern:
        cmd += f' --name "{result.name_pattern}"'

    console.print(f"Next page: {cmd}")
