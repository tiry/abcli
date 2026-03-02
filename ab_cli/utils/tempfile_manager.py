"""Temporary file management utilities for ab-cli."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any


def create_agent_edit_tempfile(
    agent_id: str,
    version_label: str,
    config: dict[str, Any],
) -> Path:
    """Create a temporary JSON file for agent editing.

    The file contains the version label and config in an editable format.
    File is created in the system temp directory with a descriptive name.

    Args:
        agent_id: Agent ID (used in filename).
        version_label: Current version label (will be incremented).
        config: Agent configuration dict.

    Returns:
        Path to the created temporary file.
    """
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"ab-agent-edit-{agent_id}-{timestamp}.json"

    # Get system temp directory
    temp_dir = Path(tempfile.gettempdir())
    temp_file = temp_dir / filename

    # Prepare data structure for editing
    edit_data = {
        "versionLabel": version_label,
        "config": config,
    }

    # Write JSON to temp file with pretty formatting
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(edit_data, f, indent=2, ensure_ascii=False)
        f.write("\n")  # Add trailing newline

    return temp_file


def read_agent_edit_tempfile(temp_file: Path) -> tuple[str, dict[str, Any]]:
    """Read and parse the edited temporary file.

    Args:
        temp_file: Path to the temporary file.

    Returns:
        Tuple of (version_label, config).

    Raises:
        json.JSONDecodeError: If the file contains invalid JSON.
        KeyError: If required fields are missing.
        FileNotFoundError: If the temp file doesn't exist.
    """
    with open(temp_file, encoding="utf-8") as f:
        data = json.load(f)

    # Validate required fields
    if "versionLabel" not in data:
        raise KeyError("Missing required field: 'versionLabel'")
    if "config" not in data:
        raise KeyError("Missing required field: 'config'")

    version_label = data["versionLabel"]
    config = data["config"]

    # Basic validation
    if not isinstance(version_label, str) or not version_label:
        raise ValueError("versionLabel must be a non-empty string")
    if not isinstance(config, dict):
        raise ValueError("config must be a dictionary")

    return version_label, config


def cleanup_tempfile(temp_file: Path, keep: bool = False) -> None:
    """Clean up (delete) the temporary file.

    Args:
        temp_file: Path to the temporary file.
        keep: If True, don't delete the file (for debugging).
    """
    if keep:
        return

    try:
        if temp_file.exists():
            temp_file.unlink()
    except Exception:
        # Silently ignore cleanup errors
        pass
