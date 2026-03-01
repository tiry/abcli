"""JSONL file handling utilities."""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any


def parse_jsonl(file_path: str | Path) -> Iterator[dict[str, Any]]:
    """Parse a JSONL file line by line.

    Args:
        file_path: Path to the JSONL file

    Yields:
        Parsed JSON objects (dicts)

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If a line contains invalid JSON
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"JSONL file not found: {file_path}")

    with open(path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            # Skip empty lines
            line = line.strip()
            if not line:
                continue

            try:
                obj = json.loads(line)
                yield obj
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON at line {line_num}: {e.msg}", e.doc, e.pos
                ) from e


def write_jsonl_line(file_handle: Any, data: dict[str, Any]) -> None:
    """Write a single JSON object as a line to a JSONL file.

    Args:
        file_handle: Open file handle (in write or append mode)
        data: Dictionary to write as JSON

    Note:
        - Properly escapes newlines within JSON strings
        - Writes a complete JSON object on a single line
        - Flushes after write for immediate persistence
    """
    # Convert to JSON string (compact format)
    json_line = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    # Write line with newline
    file_handle.write(json_line + "\n")

    # Flush to ensure it's written to disk
    file_handle.flush()
