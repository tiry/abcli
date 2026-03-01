"""Tests for JSONL handler utility."""

import json
import tempfile
from pathlib import Path

import pytest

from ab_cli.utils.jsonl_handler import parse_jsonl, write_jsonl_line


class TestParseJSONL:
    """Tests for parse_jsonl function."""

    def test_parse_valid_jsonl(self) -> None:
        """Test parsing valid JSONL file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"field1": "value1", "field2": "value2"}\n')
            f.write('{"field1": "value3", "field2": "value4"}\n')
            f.write('{"field1": "value5", "field2": "value6"}\n')
            jsonl_path = f.name

        try:
            objects = list(parse_jsonl(jsonl_path))
            assert len(objects) == 3
            assert objects[0] == {"field1": "value1", "field2": "value2"}
            assert objects[1] == {"field1": "value3", "field2": "value4"}
            assert objects[2] == {"field1": "value5", "field2": "value6"}
        finally:
            Path(jsonl_path).unlink()

    def test_skip_empty_lines(self) -> None:
        """Test that empty lines are skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"field1": "value1"}\n')
            f.write('\n')
            f.write('{"field1": "value2"}\n')
            f.write('  \n')
            f.write('{"field1": "value3"}\n')
            jsonl_path = f.name

        try:
            objects = list(parse_jsonl(jsonl_path))
            assert len(objects) == 3
        finally:
            Path(jsonl_path).unlink()

    def test_with_nested_objects(self) -> None:
        """Test parsing JSONL with nested objects."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"user": {"name": "Alice", "age": 30}, "active": true}\n')
            f.write('{"user": {"name": "Bob", "age": 25}, "active": false}\n')
            jsonl_path = f.name

        try:
            objects = list(parse_jsonl(jsonl_path))
            assert len(objects) == 2
            assert objects[0]["user"]["name"] == "Alice"
            assert objects[1]["user"]["age"] == 25
        finally:
            Path(jsonl_path).unlink()

    def test_with_arrays(self) -> None:
        """Test parsing JSONL with arrays."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"tags": ["python", "testing"], "count": 2}\n')
            f.write('{"tags": ["javascript", "node"], "count": 2}\n')
            jsonl_path = f.name

        try:
            objects = list(parse_jsonl(jsonl_path))
            assert len(objects) == 2
            assert objects[0]["tags"] == ["python", "testing"]
            assert objects[1]["tags"] == ["javascript", "node"]
        finally:
            Path(jsonl_path).unlink()

    def test_invalid_json(self) -> None:
        """Test error on invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"field1": "value1"}\n')
            f.write('{invalid json}\n')
            jsonl_path = f.name

        try:
            with pytest.raises(json.JSONDecodeError, match="Invalid JSON at line 2"):
                list(parse_jsonl(jsonl_path))
        finally:
            Path(jsonl_path).unlink()

    def test_file_not_found(self) -> None:
        """Test error when file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="JSONL file not found"):
            list(parse_jsonl("nonexistent.jsonl"))

    def test_unicode_content(self) -> None:
        """Test parsing JSONL with Unicode content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            f.write('{"message": "Hello 世界 🌍"}\n')
            f.write('{"message": "Bonjour été ☀️"}\n')
            jsonl_path = f.name

        try:
            objects = list(parse_jsonl(jsonl_path))
            assert len(objects) == 2
            assert objects[0]["message"] == "Hello 世界 🌍"
            assert objects[1]["message"] == "Bonjour été ☀️"
        finally:
            Path(jsonl_path).unlink()


class TestWriteJSONLLine:
    """Tests for write_jsonl_line function."""

    def test_write_single_line(self) -> None:
        """Test writing a single JSONL line."""
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".jsonl", delete=False) as f:
            data = {"field1": "value1", "field2": "value2"}
            write_jsonl_line(f, data)
            jsonl_path = f.name

        try:
            with open(jsonl_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.strip().split("\n")
                assert len(lines) == 1
                parsed = json.loads(lines[0])
                assert parsed == data
        finally:
            Path(jsonl_path).unlink()

    def test_write_multiple_lines(self) -> None:
        """Test writing multiple JSONL lines."""
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".jsonl", delete=False) as f:
            data1 = {"field1": "value1"}
            data2 = {"field1": "value2"}
            data3 = {"field1": "value3"}

            write_jsonl_line(f, data1)
            write_jsonl_line(f, data2)
            write_jsonl_line(f, data3)
            jsonl_path = f.name

        try:
            with open(jsonl_path, encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) == 3
                assert json.loads(lines[0]) == data1
                assert json.loads(lines[1]) == data2
                assert json.loads(lines[2]) == data3
        finally:
            Path(jsonl_path).unlink()

    def test_write_with_nested_objects(self) -> None:
        """Test writing JSONL with nested objects."""
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".jsonl", delete=False) as f:
            data = {
                "user": {"name": "Alice", "age": 30},
                "metadata": {"created": "2024-01-01", "updated": "2024-01-15"},
            }
            write_jsonl_line(f, data)
            jsonl_path = f.name

        try:
            with open(jsonl_path, encoding="utf-8") as f:
                line = f.readline()
                parsed = json.loads(line)
                assert parsed == data
        finally:
            Path(jsonl_path).unlink()

    def test_write_unicode_content(self) -> None:
        """Test writing JSONL with Unicode content."""
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".jsonl", delete=False, encoding="utf-8") as f:
            data = {"message": "Hello 世界 🌍", "emoji": "☀️"}
            write_jsonl_line(f, data)
            jsonl_path = f.name

        try:
            with open(jsonl_path, encoding="utf-8") as f:
                line = f.readline()
                parsed = json.loads(line)
                assert parsed == data
                assert parsed["message"] == "Hello 世界 🌍"
        finally:
            Path(jsonl_path).unlink()

    def test_compact_format(self) -> None:
        """Test that output uses compact format (no extra whitespace)."""
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".jsonl", delete=False) as f:
            data = {"field1": "value1", "field2": "value2"}
            write_jsonl_line(f, data)
            jsonl_path = f.name

        try:
            with open(jsonl_path, encoding="utf-8") as f:
                line = f.readline().strip()
                # Compact format has no spaces after colons or commas
                assert line == '{"field1":"value1","field2":"value2"}'
        finally:
            Path(jsonl_path).unlink()

    def test_newline_in_string_value(self) -> None:
        """Test that newlines within string values are properly escaped."""
        with tempfile.NamedTemporaryFile(mode="w+", suffix=".jsonl", delete=False) as f:
            data = {"message": "Line 1\nLine 2\nLine 3"}
            write_jsonl_line(f, data)
            jsonl_path = f.name

        try:
            # File should have only one line (newlines in value are escaped)
            with open(jsonl_path, encoding="utf-8") as f:
                lines = f.readlines()
                assert len(lines) == 1

                # Parse should work correctly
                parsed = json.loads(lines[0])
                assert parsed["message"] == "Line 1\nLine 2\nLine 3"
        finally:
            Path(jsonl_path).unlink()
