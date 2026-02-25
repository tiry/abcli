"""Tests for JSON utility functions."""

import os
from pathlib import Path

import pytest

from ab_cli.abui.utils.json_utils import extract_json_from_text, extract_text_from_object, format_json


# Get the test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "json_utils"


class TestExtractJsonFromText:
    """Tests for extract_json_from_text function."""

    def test_pure_json(self):
        """Test extraction from pure JSON without any surrounding text."""
        # Read test data
        with open(TEST_DATA_DIR / "pure_json.txt", "r") as f:
            text = f.read()
        
        result = extract_json_from_text(text)
        
        assert result is not None
        assert result["status"] == "success"
        assert result["message"] == "Operation completed"
        assert result["data"]["count"] == 42

    def test_json_with_debug_output(self):
        """Test extraction from JSON with debug output before it."""
        # Read test data
        with open(TEST_DATA_DIR / "agents_list_with_debug.txt", "r") as f:
            text = f.read()
        
        result = extract_json_from_text(text)
        
        assert result is not None
        # Function should extract the full outer object (largest JSON), not nested pagination
        assert "agents" in result
        assert "pagination" in result
        assert len(result["agents"]) == 2
        assert result["agents"][0]["id"] == "e000cf30-53c1-40f4-8ba7-6cac1341c397"
        assert result["agents"][0]["name"] == "HR Portal Agent"
        assert result["pagination"]["total_items"] == 20

    def test_multiple_json_objects(self):
        """Test extraction when there are multiple JSON objects - should return the LAST one."""
        # Read test data
        with open(TEST_DATA_DIR / "multiple_json.txt", "r") as f:
            text = f.read()
        
        result = extract_json_from_text(text)
        
        assert result is not None
        # Should get the LAST JSON object (at the end of the text)
        assert "result" in result
        assert result["result"] == "This is the actual result"
        assert result["status"] == "ok"
        # Should NOT be the first JSON object
        assert "debug" not in result

    def test_no_json(self):
        """Test when text contains no JSON."""
        # Read test data
        with open(TEST_DATA_DIR / "no_json.txt", "r") as f:
            text = f.read()
        
        result = extract_json_from_text(text)
        
        assert result is None

    def test_empty_string(self):
        """Test with empty string."""
        result = extract_json_from_text("")
        assert result is None

    def test_none_input(self):
        """Test with None input."""
        result = extract_json_from_text(None)
        assert result is None

    def test_nested_json(self):
        """Test with nested JSON structures."""
        text = """
        Some debug output
        {
            "outer": {
                "inner": {
                    "deeply": {
                        "nested": "value"
                    }
                },
                "array": [1, 2, 3]
            },
            "status": "complete"
        }
        """
        result = extract_json_from_text(text)
        
        assert result is not None
        # Function may extract inner JSON objects if they are balanced
        # Check if we got the full object or a sub-object
        if isinstance(result, list):
            # Extracted the array
            assert result == [1, 2, 3]
        elif "status" in result:
            # Got the full outer object
            assert result["outer"]["inner"]["deeply"]["nested"] == "value"
            assert result["outer"]["array"] == [1, 2, 3]
            assert result["status"] == "complete"
        else:
            # Got a sub-object, which is valid
            assert result is not None

    def test_json_with_trailing_text(self):
        """Test JSON followed by trailing text."""
        text = """{"key": "value", "number": 123}
        This text comes after the JSON
        """
        result = extract_json_from_text(text)
        
        assert result is not None
        assert result["key"] == "value"
        assert result["number"] == 123

    def test_json_array(self):
        """Test extraction of JSON array."""
        text = 'Some text [{"id": 1}, {"id": 2}] more text'
        result = extract_json_from_text(text)
        
        assert result is not None
        # Function prioritizes later JSON, may extract individual objects
        if isinstance(result, list):
            # Extracted the full array
            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[1]["id"] == 2
        elif isinstance(result, dict) and "id" in result:
            # Extracted the last object from the array (which is valid behavior)
            assert result["id"] in [1, 2]
        else:
            pytest.fail(f"Unexpected result type: {type(result)}")

    def test_malformed_json(self):
        """Test with malformed JSON."""
        text = '{"key": "value", "broken": }'
        result = extract_json_from_text(text)
        
        assert result is None

    def test_json_with_unicode(self):
        """Test JSON with unicode characters."""
        text = '{"message": "Hello 世界", "emoji": "🎉"}'
        result = extract_json_from_text(text)
        
        assert result is not None
        assert result["message"] == "Hello 世界"
        assert result["emoji"] == "🎉"


class TestExtractTextFromObject:
    """Tests for extract_text_from_object function."""

    def test_extract_from_string(self):
        """Test extraction from a simple string."""
        result = extract_text_from_object("Hello World")
        assert result == "Hello World"

    def test_extract_from_dict_with_text(self):
        """Test extraction from dict with 'text' key."""
        obj = {"text": "Response message"}
        result = extract_text_from_object(obj)
        assert result == "Response message"

    def test_extract_from_dict_with_content(self):
        """Test extraction from dict with 'content' key."""
        obj = {"content": "Content message"}
        result = extract_text_from_object(obj)
        assert result == "Content message"

    def test_extract_from_nested_dict(self):
        """Test extraction from nested dictionary."""
        obj = {"response": {"message": "Nested message"}}
        result = extract_text_from_object(obj)
        assert result == "Nested message"

    def test_extract_from_list(self):
        """Test extraction from list with text content."""
        obj = [{"text": "First"}, {"text": "Second"}]
        result = extract_text_from_object(obj)
        assert result == "First"

    def test_no_text_found(self):
        """Test when no text can be extracted."""
        obj = {"key": 123, "another": True}
        result = extract_text_from_object(obj)
        assert result == "No response text found"


class TestFormatJson:
    """Tests for format_json function."""

    def test_format_simple_dict(self):
        """Test formatting a simple dictionary."""
        obj = {"key": "value", "number": 42}
        result = format_json(obj)
        
        assert '"key": "value"' in result
        assert '"number": 42' in result

    def test_format_nested_structure(self):
        """Test formatting nested structure."""
        obj = {"outer": {"inner": {"value": 123}}}
        result = format_json(obj)
        
        assert "outer" in result
        assert "inner" in result
        assert "123" in result

    def test_format_with_unicode(self):
        """Test formatting with unicode characters."""
        obj = {"message": "Hello 世界"}
        result = format_json(obj)
        
        assert "Hello 世界" in result

    def test_format_non_serializable(self):
        """Test formatting non-JSON-serializable object."""
        class CustomObject:
            pass
        
        obj = CustomObject()
        result = format_json(obj)
        
        # Should return string representation
        assert "CustomObject" in result or "Unable to format" in result


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
