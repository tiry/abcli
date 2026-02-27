"""Version service for business logic.

This service provides version-related operations with business logic
extracted from CLI commands, making it reusable by both CLI and UI.
"""

from uuid import UUID

from ab_cli.api.client import AgentBuilderClient
from ab_cli.models.agent import AgentVersion, VersionList


class VersionService:
    """Service for version operations.

    This service wraps the API client and provides version-related
    business logic that can be used by both CLI and UI components.
    """

    def __init__(self, client: AgentBuilderClient) -> None:
        """Initialize the version service.

        Args:
            client: The API client to use for requests.
        """
        self.client = client

    def list_versions(self, agent_id: str | UUID, limit: int = 10, offset: int = 0) -> VersionList:
        """List all versions of an agent.

        Args:
            agent_id: The agent ID.
            limit: Maximum number of versions to return (default: 10).
            offset: Offset for pagination (default: 0).

        Returns:
            VersionList with version summaries and pagination metadata.

        Raises:
            NotFoundError: If agent not found.
        """
        return self.client.list_versions(agent_id, limit=limit, offset=offset)

    def get_version(self, agent_id: str | UUID, version_id: str | UUID) -> AgentVersion | None:
        """Get a specific version of an agent with full configuration.

        Args:
            agent_id: The agent ID.
            version_id: The version ID.

        Returns:
            AgentVersion with agent metadata and full version configuration,
            or None if not found.
        """
        try:
            return self.client.get_version(agent_id, version_id)
        except Exception:
            # Return None if version not found
            return None

    def create_version(
        self,
        agent_id: str | UUID,
        config: dict,
        version_label: str | None = None,
        notes: str | None = None,
    ) -> AgentVersion:
        """Create a new version for an agent.

        Args:
            agent_id: The agent ID.
            config: The version configuration dictionary.
            version_label: Optional version label.
            notes: Optional version notes.

        Returns:
            AgentVersion with the created version information.

        Raises:
            NotFoundError: If agent not found.
            APIError: If creation fails.
        """
        from ab_cli.models.agent import VersionCreate

        version_create = VersionCreate(config=config, version_label=version_label, notes=notes)
        return self.client.create_version(agent_id, version_create)
