"""CSV parsing utilities for chat input files."""

import csv
from collections.abc import Iterator
from pathlib import Path


class ChatInput:
    """Represents a single chat input from CSV."""

    def __init__(self, message_id: str, message: str):
        """Initialize chat input.

        Args:
            message_id: Unique identifier for the message
            message: The message content
        """
        self.message_id = message_id
        self.message = message

    def __repr__(self) -> str:
        return f"ChatInput(message_id='{self.message_id}', message='{self.message[:50]}...')"


def parse_chat_csv(file_path: str | Path) -> Iterator[ChatInput]:
    """Parse a CSV file containing chat messages.

    Supports two formats:
    1. Single column: message only (message_id = row index)
    2. Two columns: message_id, message

    Auto-detects headers by checking if first row contains "message".

    Args:
        file_path: Path to the CSV file

    Yields:
        ChatInput objects with message_id and message

    Raises:
        ValueError: If CSV format is invalid
        FileNotFoundError: If file doesn't exist
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    with open(path, encoding="utf-8") as f:
        # Peek at first line to check for header
        first_line = f.readline()
        f.seek(0)  # Reset to start

        # Check if first line contains "message" (case-insensitive)
        has_header = "message" in first_line.lower()

        # Create CSV reader
        reader = csv.reader(f)

        # Skip header if present
        if has_header:
            next(reader)

        # Process rows
        for index, row in enumerate(reader):
            # Skip empty rows
            if not row or not any(cell.strip() for cell in row):
                continue

            # Strip whitespace from all fields
            row = [cell.strip() for cell in row]

            if len(row) == 1:
                # Single column: message only
                message_id = str(index)
                message = row[0]
            elif len(row) == 2:
                # Two columns: message_id, message
                message_id = row[0]
                message = row[1]
            else:
                raise ValueError(
                    f"Invalid CSV format at row {index + (2 if has_header else 1)}: "
                    f"Expected 1 or 2 columns, got {len(row)}"
                )

            if not message:
                # Skip rows with empty messages
                continue

            yield ChatInput(message_id=message_id, message=message)
