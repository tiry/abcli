"""Common CLI options that can be reused across commands."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import click


def profile_option(f: Callable[..., Any]) -> Callable[..., Any]:
    """Add --profile option to a command or command group."""
    return click.option(
        "--profile",
        type=str,
        help="Configuration profile to use (e.g., dev, staging, prod)",
    )(f)


def config_option(f: Callable[..., Any]) -> Callable[..., Any]:
    """Add --config option to a command or command group."""
    return click.option(
        "-c",
        "--config",
        type=click.Path(exists=True, path_type=Path),
        help="Path to configuration file",
    )(f)
