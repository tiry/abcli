"""Unit tests for the UI data provider factory."""

import os
from dataclasses import dataclass
from unittest.mock import patch

import pytest
import streamlit as st

from ab_cli.abui.providers.cli_data_provider import CLIDataProvider
from ab_cli.abui.providers.mock_data_provider import MockDataProvider
from ab_cli.abui.providers.provider_factory import get_data_provider


# Define test dataclasses
@dataclass
class UISettings:
    data_provider: str = "cli"
    mock_data_dir: str = None
    

@dataclass
class DummyConfig:
    environment_id: str = "dummy-env-id"
    client_id: str = "dummy-client-id"
    client_secret: str = "dummy-client-secret"
    verbose: bool = True
    ui: UISettings = None


def create_dummy_config(provider_type="cli"):
    """Create a dummy configuration for testing.
    
    Args:
        provider_type: The data provider to use (cli or mock)
        
    Returns:
        A dummy configuration object
    """
    # Create the config with UI settings
    config = DummyConfig()
    config.ui = UISettings(data_provider=provider_type)
    return config


def test_get_provider_cli():
    """Test that get_data_provider returns a CLIDataProvider when configured for CLI."""
    # Clear any cached provider
    if "data_provider" in st.session_state:
        del st.session_state.data_provider
    
    # Create a dummy config with CLI provider
    config = create_dummy_config("cli")
    
    # Get the data provider
    with patch.dict(os.environ, {}, clear=True):  # Clear any environment variables
        provider = get_data_provider(config)
    
    # Verify the provider type
    assert isinstance(provider, CLIDataProvider)
    assert provider.__class__.__name__ == "CLIDataProvider"


def test_get_provider_mock():
    """Test that get_data_provider returns a MockDataProvider when configured for mock."""
    # Clear any cached provider
    if "data_provider" in st.session_state:
        del st.session_state.data_provider
    
    # Create a dummy config with mock provider
    config = create_dummy_config("mock")
    
    # Get the data provider
    with patch.dict(os.environ, {}, clear=True):  # Clear any environment variables
        provider = get_data_provider(config)
    
    # Verify the provider type
    assert isinstance(provider, MockDataProvider)
    assert provider.__class__.__name__ == "MockDataProvider"


def test_get_provider_env_override():
    """Test that environment variable overrides the configuration."""
    # Clear any cached provider
    if "data_provider" in st.session_state:
        del st.session_state.data_provider
    
    # Create a dummy config with CLI provider
    config = create_dummy_config("cli")
    
    # Set the environment variable to override to mock
    with patch.dict(os.environ, {"AB_UI_DATA_PROVIDER": "mock"}, clear=True):
        # Get the data provider
        provider = get_data_provider(config)
    
    # Verify the provider was overridden to mock
    assert isinstance(provider, MockDataProvider)
    assert provider.__class__.__name__ == "MockDataProvider"


def test_provider_basic_methods():
    """Test that the providers implement the expected methods."""
    # Clear any cached provider
    if "data_provider" in st.session_state:
        del st.session_state.data_provider
    
    # Create a mock provider
    config = create_dummy_config("mock")
    provider = get_data_provider(config)
    
    # Verify the provider has the expected methods
    assert hasattr(provider, "get_agents")
    assert hasattr(provider, "get_models")
    assert hasattr(provider, "get_guardrails")
    
    # Test basic functionality (should not throw exceptions)
    agents = provider.get_agents()
    assert isinstance(agents, list)
    
    models = provider.get_models()
    assert isinstance(models, list)
    
    guardrails = provider.get_guardrails()
    assert isinstance(guardrails, list)