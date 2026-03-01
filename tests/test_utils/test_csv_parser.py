"""Tests for CSV parser utility."""

import tempfile
from pathlib import Path

import pytest

from ab_cli.utils.csv_parser import ChatInput, parse_chat_csv


class TestChatInput:
    """Tests for ChatInput class."""

    def test_init(self) -> None:
        """Test ChatInput initialization."""
        chat_input = ChatInput("msg_001", "Hello world")
        assert chat_input.message_id == "msg_001"
        assert chat_input.message == "Hello world"

    def test_repr(self) -> None:
        """Test ChatInput repr."""
        chat_input = ChatInput("msg_001", "Hello world")
        assert "msg_001" in repr(chat_input)
        assert "Hello world" in repr(chat_input)

    def test_repr_long_message(self) -> None:
        """Test ChatInput repr with long message."""
        long_message = "A" * 100
        chat_input = ChatInput("msg_001", long_message)
        repr_str = repr(chat_input)
        assert "msg_001" in repr_str
        assert "..." in repr_str  # Message is truncated


class TestParseChatCSV:
    """Tests for parse_chat_csv function."""

    def test_single_column_no_header(self) -> None:
        """Test parsing single column CSV without header."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("What is the weather?\n")
            f.write("Tell me a joke\n")
            f.write("Explain quantum physics\n")
            csv_path = f.name

        try:
            inputs = list(parse_chat_csv(csv_path))
            assert len(inputs) == 3
            assert inputs[0].message_id == "0"
            assert inputs[0].message == "What is the weather?"
            assert inputs[1].message_id == "1"
            assert inputs[1].message == "Tell me a joke"
            assert inputs[2].message_id == "2"
            assert inputs[2].message == "Explain quantum physics"
        finally:
            Path(csv_path).unlink()

    def test_two_columns_no_header(self) -> None:
        """Test parsing two column CSV without header."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("msg_001,What is the weather?\n")
            f.write("msg_002,Tell me a joke\n")
            f.write("msg_003,Explain quantum physics\n")
            csv_path = f.name

        try:
            inputs = list(parse_chat_csv(csv_path))
            assert len(inputs) == 3
            assert inputs[0].message_id == "msg_001"
            assert inputs[0].message == "What is the weather?"
            assert inputs[1].message_id == "msg_002"
            assert inputs[1].message == "Tell me a joke"
        finally:
            Path(csv_path).unlink()

    def test_with_header(self) -> None:
        """Test parsing CSV with header row."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("message_id,message\n")
            f.write("msg_001,What is the weather?\n")
            f.write("msg_002,Tell me a joke\n")
            csv_path = f.name

        try:
            inputs = list(parse_chat_csv(csv_path))
            assert len(inputs) == 2
            assert inputs[0].message_id == "msg_001"
            assert inputs[0].message == "What is the weather?"
        finally:
            Path(csv_path).unlink()

    def test_single_column_with_header(self) -> None:
        """Test parsing single column CSV with header."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("message\n")
            f.write("What is the weather?\n")
            f.write("Tell me a joke\n")
            csv_path = f.name

        try:
            inputs = list(parse_chat_csv(csv_path))
            assert len(inputs) == 2
            assert inputs[0].message_id == "0"
            assert inputs[0].message == "What is the weather?"
        finally:
            Path(csv_path).unlink()

    def test_with_quotes(self) -> None:
        """Test parsing CSV with quoted fields containing commas."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write('msg_001,"Hello, how are you?"\n')
            f.write('msg_002,"Tell me about AI, ML, and NLP"\n')
            csv_path = f.name

        try:
            inputs = list(parse_chat_csv(csv_path))
            assert len(inputs) == 2
            assert inputs[0].message == "Hello, how are you?"
            assert inputs[1].message == "Tell me about AI, ML, and NLP"
        finally:
            Path(csv_path).unlink()

    def test_skip_empty_rows(self) -> None:
        """Test that empty rows are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("What is the weather?\n")
            f.write("\n")
            f.write("Tell me a joke\n")
            f.write("   \n")
            f.write("Explain quantum physics\n")
            csv_path = f.name

        try:
            inputs = list(parse_chat_csv(csv_path))
            assert len(inputs) == 3
        finally:
            Path(csv_path).unlink()

    def test_whitespace_trimming(self) -> None:
        """Test that whitespace is trimmed from fields."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("  msg_001  ,  What is the weather?  \n")
            f.write("msg_002,  Tell me a joke\n")
            csv_path = f.name

        try:
            inputs = list(parse_chat_csv(csv_path))
            assert len(inputs) == 2
            assert inputs[0].message_id == "msg_001"
            assert inputs[0].message == "What is the weather?"
        finally:
            Path(csv_path).unlink()

    def test_invalid_column_count(self) -> None:
        """Test error on invalid column count in data rows."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            # Header with 3 columns gets detected and skipped
            f.write("msg_id,message,extra\n")
            # Data row with 3 columns should cause an error
            f.write("msg_001,message_text,extra_column\n")
            csv_path = f.name

        try:
            with pytest.raises(ValueError, match="Expected 1 or 2 columns"):
                list(parse_chat_csv(csv_path))
        finally:
            Path(csv_path).unlink()

    def test_file_not_found(self) -> None:
        """Test error when file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="CSV file not found"):
            list(parse_chat_csv("nonexistent.csv"))

    def test_empty_messages_skipped(self) -> None:
        """Test that rows with empty messages are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("msg_001,What is the weather?\n")
            f.write("msg_002,\n")
            f.write("msg_003,Tell me a joke\n")
            csv_path = f.name

        try:
            inputs = list(parse_chat_csv(csv_path))
            assert len(inputs) == 2
            assert inputs[0].message_id == "msg_001"
            assert inputs[1].message_id == "msg_003"
        finally:
            Path(csv_path).unlink()
