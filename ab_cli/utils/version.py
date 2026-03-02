"""Version manipulation utilities for ab-cli."""

import re


def increment_version(version: str) -> str:
    """Increment the last numeric component of a version string.

    This function finds the last number in a version string and increments it.
    It handles various version formats flexibly.

    Examples:
        >>> increment_version("v1.0")
        'v1.1'
        >>> increment_version("v2.5")
        'v2.6'
        >>> increment_version("v1.0.3")
        'v1.0.4'
        >>> increment_version("1.2.3")
        '1.2.4'
        >>> increment_version("release-5")
        'release-6'
        >>> increment_version("v1.9")
        'v1.10'
        >>> increment_version("no-numbers")
        'no-numbers.1'

    Args:
        version: Version string to increment.

    Returns:
        Incremented version string.
    """
    # Find the last number in the string
    match = re.search(r"(\d+)(?!.*\d)", version)
    if match:
        # Get the number and its position
        num = int(match.group(1))
        start, end = match.span()
        # Increment and replace
        return version[:start] + str(num + 1) + version[end:]
    else:
        # No number found, append ".1"
        return version + ".1"
