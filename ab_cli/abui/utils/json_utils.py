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

    # Find all potential JSON objects in the text by finding all { and } pairs
    # We'll try to parse each complete JSON object, preferring those at the end
    potential_jsons: list[tuple[int, str]] = []
    
    # Find all starting positions of { or [
    json_starts = []
    for i, c in enumerate(text):
        if c in "{[":
            json_starts.append((i, c))
    
    if not json_starts:
        if verbose:
            print("No JSON markers found in the text")
        return None

    # For each start position, try to find the matching end
    for start_idx, start_char in json_starts:
        possible_json = text[start_idx:]
        stack = []
        json_end = -1
        
        # Track brackets/braces to find balanced JSON
        for i, c in enumerate(possible_json):
            if c in "{[":
                stack.append(c)
            elif c == "}" and stack and stack[-1] == "{":
                stack.pop()
                if not stack:
                    json_end = i + 1
                    break
            elif c == "]" and stack and stack[-1] == "[":
                stack.pop()
                if not stack:
                    json_end = i + 1
                    break
        
        if json_end > 0:
            json_str = possible_json[:json_end]
            potential_jsons.append((start_idx, json_str))
    
    if not potential_jsons:
        if verbose:
            print("No complete JSON objects found")
        return None
    
    # Try parsing JSON objects from the END of the text first (most likely to be the CLI output)
    # Sort by starting position, descending (later in text = higher priority)
    potential_jsons.sort(key=lambda x: x[0], reverse=True)
    
    for start_pos, json_str in potential_jsons:
        try:
            parsed = json.loads(json_str)
            if verbose:
                print(f"Successfully parsed JSON starting at position {start_pos}")
            return cast(dict[str, Any], parsed)
        except json.JSONDecodeError:
            if verbose:
                print(f"Failed to parse JSON at position {start_pos}")
            continue
    
    if verbose:
        print("All JSON parsing attempts failed")
    
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
