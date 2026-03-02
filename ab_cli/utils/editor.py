"""Editor management utilities for ab-cli."""

import os
import platform
import subprocess
from pathlib import Path

from ab_cli.config.settings import ABSettings


def get_editor(config: ABSettings, override: str | None = None) -> str:
    """Determine which text editor to use.

    Priority order:
    1. Command-line override (--editor flag)
    2. Config file setting (config.editor)
    3. $VISUAL environment variable
    4. $EDITOR environment variable
    5. Platform default (vi for Unix, notepad.exe for Windows)

    Args:
        config: ABSettings configuration object.
        override: Optional editor override from command-line flag.

    Returns:
        Editor command string (e.g., 'vim', 'code --wait', 'notepad.exe').
    """
    # Priority 1: Command-line override
    if override:
        return override

    # Priority 2: Config file setting
    if config.editor:
        return config.editor

    # Priority 3: $VISUAL environment variable
    visual = os.environ.get("VISUAL")
    if visual:
        return visual

    # Priority 4: $EDITOR environment variable
    editor = os.environ.get("EDITOR")
    if editor:
        return editor

    # Priority 5: Platform default
    if platform.system() == "Windows":
        return "notepad.exe"
    else:
        # Unix-like systems (Linux, macOS)
        return "vi"


def open_editor(file_path: str | Path, editor_cmd: str) -> int:
    """Open a text editor and wait for it to close.

    This function launches the specified editor with the given file,
    waits for the editor process to complete, and returns the exit code.

    Args:
        file_path: Path to the file to edit.
        editor_cmd: Editor command (may include flags, e.g., 'code --wait').

    Returns:
        Exit code from the editor process (0 for success).

    Raises:
        FileNotFoundError: If the editor command is not found.
        subprocess.SubprocessError: If the editor fails to launch.
    """
    file_path = str(file_path)

    # Split editor command into command and arguments
    # e.g., "code --wait" -> ["code", "--wait"]
    cmd_parts = editor_cmd.split()

    # Construct full command with file path
    full_cmd = cmd_parts + [file_path]

    try:
        # Launch editor and wait for it to complete
        result = subprocess.run(
            full_cmd,
            check=False,  # Don't raise on non-zero exit
        )
        return result.returncode

    except FileNotFoundError as e:
        raise FileNotFoundError(
            f"Editor '{cmd_parts[0]}' not found. "
            f"Please ensure it's installed and in your PATH, "
            f"or specify a different editor with --editor flag or in config.yaml"
        ) from e
    except Exception as e:
        raise subprocess.SubprocessError(f"Failed to launch editor '{editor_cmd}': {e}") from e
