"""JSON utility functions for the Agent Builder UI."""

import json
import re
from typing import Any, cast


def extract_json_from_text(text: str, verbose: bool = False) -> dict[str, Any] | None:
    """Extract JSON content from text that might include non-JSON content.

    Args:
        text: Text that might contain JSON
        verbose: Whether to print verbose output

    Returns:
        Parsed JSON object or None if no valid JSON found
    """
    if not text:
        if verbose:
            print("No text to parse")
        return None

    # First try direct parsing
    try:
        return cast(dict[str, Any], json.loads(text))
    except json.JSONDecodeError:
        if verbose:
            print("Direct JSON parsing failed, trying to extract JSON content")

    # Try to find JSON content in the text
    # Look for the first occurrence of { or [
    json_start = -1
    for i, c in enumerate(text):
        if c in "{[":
            json_start = i
            break

    if json_start == -1:
        if verbose:
            print("No JSON markers found in the text")
        return None

    # Extract text from the first JSON marker
    possible_json = text[json_start:]

    # Try to find where JSON content ends
    # This is more complex as we need to respect nesting
    stack = []
    json_end = -1

    # In case there are multiple JSON objects, try to find balanced braces
    for i, c in enumerate(possible_json):
        if c in "{[":
            stack.append(c)
        elif c == "}" and stack and stack[-1] == "{" or c == "]" and stack and stack[-1] == "[":
            stack.pop()
            if not stack:
                json_end = i + 1
                break

    if json_end == -1:
        # Couldn't find balanced ending, try a simpler approach
        closing_brace = possible_json.rfind("}")
        closing_bracket = possible_json.rfind("]")
        json_end = max(closing_brace, closing_bracket) + 1

    if json_end <= 0:
        if verbose:
            print("Couldn't find JSON end markers")
        return None

    json_str = possible_json[:json_end]

    if verbose:
        print(f"Extracted JSON string: {json_str}")

    try:
        return cast(dict[str, Any], json.loads(json_str))
    except json.JSONDecodeError as e:
        if verbose:
            print(f"Failed to parse JSON: {e}")

        # More aggressive approach - try using regex
        json_pattern = r"(\{.*\}|\[.*\])"
        try:
            # Look for the largest JSON-like pattern in the text
            matches = list(re.finditer(json_pattern, text, re.DOTALL))
            if matches:
                # Sort by length, descending
                matches.sort(key=lambda m: len(m.group(0)), reverse=True)

                # Try each match, starting with the largest
                for match in matches:
                    try:
                        json_str = match.group(0)
                        if verbose:
                            print(f"Found potential JSON: {json_str[:100]}...")
                        return cast(dict[str, Any], json.loads(json_str))
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            if verbose:
                print(f"Error extracting JSON with regex: {e}")

        return None


def extract_text_from_object(obj: Any) -> str:
    """Recursively extract text from nested objects.

    Args:
        obj: Object to extract text from

    Returns:
        Extracted text or empty string if no text found
    """
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        if "text" in obj:
            return cast(str, obj["text"])
        if "content" in obj:
            content_text = extract_text_from_object(obj["content"])
            if content_text:
                return content_text
        for k, v in obj.items():
            if k.lower() in ["message", "response", "answer", "text"]:
                result = extract_text_from_object(v)
                if result:
                    return result
    if isinstance(obj, list):
        for item in obj:
            result = extract_text_from_object(item)
            if result:
                return result
    # Default to empty string if no text could be found
    return "No response text found"


def format_json(obj: Any) -> str:
    """Format JSON object for display.

    This function takes any JSON-serializable object and returns a nicely formatted
    string representation suitable for display. It handles special cases like nested
    structures and ensures consistent spacing.

    Args:
        obj: JSON-serializable object

    Returns:
        Formatted JSON string
    """
    # Use json.dumps with standard formatting options
    try:
        return json.dumps(obj, indent=2, sort_keys=False, ensure_ascii=False)
    except (TypeError, ValueError):
        # If the object can't be JSON-serialized, try to convert it to a string
        try:
            return str(obj)
        except Exception:
            return "Unable to format object as JSON"
