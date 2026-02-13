"""Audit utilities for recording API payloads."""

import datetime
import json
import os
import pathlib
from typing import Any


def save_payload(
    operation_name: str, payload: dict[str, Any], config_path: str | None = None
) -> str:
    """Save an API payload to the audit directory.

    Args:
        operation_name: The name of the operation (e.g., create_agent, update_agent)
        payload: The API payload to save
        config_path: Optional path to the config file, used to determine the audit directory
                    If not provided, uses the current directory

    Returns:
        Path to the saved audit file
    """
    # Determine the base directory (either from config file or current directory)
    base_dir = os.path.dirname(os.path.abspath(config_path)) if config_path else os.getcwd()

    # Create the audit directory if it doesn't exist
    audit_dir = os.path.join(base_dir, "audit")
    os.makedirs(audit_dir, exist_ok=True)

    # Generate a timestamp for the filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create the filename
    filename = f"{operation_name}_{timestamp}.json"
    file_path = os.path.join(audit_dir, filename)

    # Save the payload
    with open(file_path, "w") as f:
        json.dump(payload, f, indent=2)

    return file_path


def get_audit_dir(config_path: str | None = None) -> pathlib.Path:
    """Get the path to the audit directory.

    Args:
        config_path: Optional path to the config file, used to determine the audit directory
                    If not provided, uses the current directory

    Returns:
        Path to the audit directory
    """
    # Determine the base directory (either from config file or current directory)
    base_dir = os.path.dirname(os.path.abspath(config_path)) if config_path else os.getcwd()

    # Return the audit directory path
    return pathlib.Path(os.path.join(base_dir, "audit"))
