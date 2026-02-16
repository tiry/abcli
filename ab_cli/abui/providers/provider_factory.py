"""Factory for creating data providers."""

import os
from typing import Any

import streamlit as st

from ab_cli.abui.providers.cli_data_provider import CLIDataProvider
from ab_cli.abui.providers.data_provider import DataProvider
from ab_cli.abui.providers.mock_data_provider import MockDataProvider


def get_data_provider(config: Any) -> DataProvider:
    """Get the appropriate data provider based on configuration.

    Args:
        config: Application configuration

    Returns:
        DataProvider instance
    """
    # Default to CLI provider if not specified
    provider_type = "cli"

    # Check config for provider type
    # Handle Pydantic model where ui might be None
    if (
        config
        and hasattr(config, "ui")
        and config.ui is not None
        and hasattr(config.ui, "data_provider")
    ):
        provider_type = config.ui.data_provider

    # Also check environment variable (for easier testing)
    if os.environ.get("AB_UI_DATA_PROVIDER"):
        provider_type = os.environ.get("AB_UI_DATA_PROVIDER", "").lower()

    # Create provider based on type
    # Check for verbose flag in the following order:
    # 1. Streamlit session state (set from command line --verbose)
    # 2. Config object
    verbose = False

    # First check Streamlit session state if available
    if hasattr(st, "session_state") and "verbose" in st.session_state:
        verbose = st.session_state.verbose

    # Fall back to config if not set in session state
    if not verbose:
        verbose = (
            getattr(config, "verbose", False)
            or hasattr(config, "ui")
            and getattr(config.ui, "verbose", False)
        )

    # Log which provider we're using
    if verbose:
        print(f"Data provider type from config: {provider_type}")

    if provider_type.lower() == "mock":
        if verbose:
            print("Using Mock data provider")
        return MockDataProvider(config)
    else:
        # Default to CLI provider
        if verbose:
            print("Using CLI data provider")
        return CLIDataProvider(config, verbose)
