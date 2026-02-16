"""Pagination utilities for API operations."""

import re
from dataclasses import dataclass

from ab_cli.api.client import AgentBuilderClient
from ab_cli.config.settings import ABSettings
from ab_cli.models.agent import Agent


@dataclass
class PaginatedResult:
    """Result of a paginated fetch operation."""

    agents: list[Agent]
    offset: int
    limit: int
    total_count: int | None  # None if filters applied
    has_filters: bool
    agent_type: str | None
    name_pattern: str | None
    pages_fetched: int = 1

    @property
    def has_more(self) -> bool:
        """Check if more results are available."""
        if self.total_count is None:
            # With filters, assume more if we got a full page
            return len(self.agents) == self.limit
        return self.offset + len(self.agents) < self.total_count


def fetch_agents_paginated(
    client: AgentBuilderClient,
    settings: ABSettings | None = None,
    offset: int = 0,
    limit: int = 50,
    page: int | None = None,
    agent_type: str | None = None,
    name_pattern: str | None = None,
) -> PaginatedResult:
    """Fetch agents with pagination and optional client-side filtering.

    This function handles:
    - Converting page number to offset
    - Fetching from API
    - Client-side filtering (with max_filter_pages limit)
    - Returning ready-to-use results

    Args:
        client: API client instance.
        settings: Application settings (for max_filter_pages). Optional, uses defaults if not provided.
        offset: Starting offset (0-based).
        limit: Number of results to return.
        page: Page number (1-based, alternative to offset).
        agent_type: Filter by agent type (tool, rag, task).
        name_pattern: Filter by name (supports substring and wildcards).

    Returns:
        PaginatedResult with agents and metadata.
    """
    # Convert page to offset if provided
    if page is not None:
        offset = (page - 1) * limit

    has_filters = bool(agent_type or name_pattern)

    # Without filters: simple single-page fetch
    if not has_filters:
        result = client.list_agents(limit=limit, offset=offset)
        return PaginatedResult(
            agents=result.agents,
            offset=offset,
            limit=limit,
            total_count=result.pagination.total_items,
            has_filters=False,
            agent_type=None,
            name_pattern=None,
        )

    # With filters: fetch multiple pages until we have enough matches
    max_filter_pages = 10  # Default
    if settings and settings.pagination:
        max_filter_pages = settings.pagination.max_filter_pages

    filtered_agents: list[Agent] = []
    server_offset = offset
    server_limit = limit
    pages_fetched = 0

    while len(filtered_agents) < limit and pages_fetched < max_filter_pages:
        result = client.list_agents(limit=server_limit, offset=server_offset)

        # Apply filters
        for agent in result.agents:
            if _matches_filters(agent, agent_type, name_pattern):
                filtered_agents.append(agent)
                if len(filtered_agents) >= limit:
                    break

        pages_fetched += 1

        # Check if more data available from server
        if len(result.agents) < server_limit:
            break  # No more data from server

        server_offset += server_limit

    # Truncate to requested limit
    filtered_agents = filtered_agents[:limit]

    return PaginatedResult(
        agents=filtered_agents,
        offset=offset,
        limit=limit,
        total_count=None,  # Unknown with filters
        has_filters=True,
        agent_type=agent_type,
        name_pattern=name_pattern,
        pages_fetched=pages_fetched,
    )


def _matches_filters(agent: Agent, agent_type: str | None, name_pattern: str | None) -> bool:
    """Check if an agent matches the given filters.

    Args:
        agent: Agent to check.
        agent_type: Type filter (if any).
        name_pattern: Name pattern filter (if any).

    Returns:
        True if agent matches all filters.
    """
    # Type filter
    if agent_type and agent.type != agent_type:
        return False

    # Name filter
    if name_pattern:
        # Convert wildcard pattern to regex if needed
        if name_pattern.startswith("*") or name_pattern.endswith("*"):
            pattern = name_pattern.replace("*", ".*")
            try:
                regex = re.compile(pattern, re.IGNORECASE)
                if not regex.search(agent.name):
                    return False
            except re.error:
                # Fall back to substring match
                name_lower = name_pattern.replace("*", "").lower()
                if name_lower not in agent.name.lower():
                    return False
        else:
            # Simple substring match (case-insensitive)
            if name_pattern.lower() not in agent.name.lower():
                return False

    return True
