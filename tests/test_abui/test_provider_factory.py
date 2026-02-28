"""Unit tests for the UI data provider factory."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import streamlit as st

from ab_cli.abui.providers.cli_data_provider import CLIDataProvider
from ab_cli.abui.providers.direct_data_provider import DirectDataProvider
from ab_cli.abui.providers.mock_data_provider import MockDataProvider
from ab_cli.abui.providers.provider_factory import get_data_provider
from ab_cli.config import load_config


# Get test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "data"


def test_provider_respects_config_direct():
    """Test that provider_factory respects config file setting for 'direct'."""
    # Clear any cached provider and env vars
    if "data_provider" in st.session_state:
        del st.session_state.data_provider
    
    # Load real config file with direct provider
    config_path = TEST_DATA_DIR / "config-provider-direct.yaml"
    config = load_config(str(config_path))
    
    # Verify config loaded correctly
    assert config.ui is not None
    assert config.ui.data_provider == "direct"
    
    # Get the data provider WITHOUT any environment variable
    with patch.dict(os.environ, {}, clear=True):
        provider = get_data_provider(config)
    
    # Should get DirectDataProvider based on config
    assert isinstance(provider, DirectDataProvider)
    print(f"✓ Config with 'direct' correctly returns DirectDataProvider")


def test_provider_respects_config_cli():
    """Test that provider_factory respects config file setting for 'cli'."""
    # Clear any cached provider
    if "data_provider" in st.session_state:
        del st.session_state.data_provider
    
    # Load real config file with CLI provider
    config_path = TEST_DATA_DIR / "config-provider-cli.yaml"
    config = load_config(str(config_path))
    
    # Verify config loaded correctly
    assert config.ui is not None
    assert config.ui.data_provider == "cli"
    
    # Get the data provider WITHOUT any environment variable
    with patch.dict(os.environ, {}, clear=True):
        provider = get_data_provider(config)
    
    # Should get CLIDataProvider based on config
    assert isinstance(provider, CLIDataProvider)
    print(f"✓ Config with 'cli' correctly returns CLIDataProvider")


def test_provider_respects_config_mock():
    """Test that provider_factory respects config file setting for 'mock'."""
    # Clear any cached provider
    if "data_provider" in st.session_state:
        del st.session_state.data_provider
    
    # Load real config file with mock provider
    config_path = TEST_DATA_DIR / "config-provider-mock.yaml"
    config = load_config(str(config_path))
    
    # Verify config loaded correctly
    assert config.ui is not None
    assert config.ui.data_provider == "mock"
    
    # Get the data_provider WITHOUT any environment variable
    with patch.dict(os.environ, {}, clear=True):
        provider = get_data_provider(config)
    
    # Should get MockDataProvider based on config
    assert isinstance(provider, MockDataProvider)
    print(f"✓ Config with 'mock' correctly returns MockDataProvider")


def test_env_var_overrides_config():
    """Test that environment variable overrides the config file setting."""
    # Clear any cached provider
    if "data_provider" in st.session_state:
        del st.session_state.data_provider
    
    # Load config with CLI provider
    config_path = TEST_DATA_DIR / "config-provider-cli.yaml"
    config = load_config(str(config_path))
    assert config.ui.data_provider == "cli"
    
    # Set environment variable to override to mock
    with patch.dict(os.environ, {"AB_UI_DATA_PROVIDER": "mock"}, clear=True):
        provider = get_data_provider(config)
    
    # Should get MockDataProvider because env var overrides config
    assert isinstance(provider, MockDataProvider)
    print(f"✓ Environment variable correctly overrides config setting")


def test_provider_priority_no_env_uses_config():
    """Test priority: when no env var is set, config is used."""
    # Clear any cached provider
    if "data_provider" in st.session_state:
        del st.session_state.data_provider
    
    # Load config with direct provider
    config_path = TEST_DATA_DIR / "config-provider-direct.yaml"
    config = load_config(str(config_path))
    
    # Ensure no environment variable is set
    with patch.dict(os.environ, {}, clear=True):
        provider = get_data_provider(config)
    
    # Should use config setting
    assert isinstance(provider, DirectDataProvider)
    print(f"✓ Priority test: config used when no env var")


def test_provider_caching():
    """Test that provider is cached in session state."""
    # Clear any cached provider
    if "data_provider" in st.session_state:
        del st.session_state.data_provider
    
    # Load config
    config_path = TEST_DATA_DIR / "config-provider-mock.yaml"
    config = load_config(str(config_path))
    
    # Get provider twice
    with patch.dict(os.environ, {}, clear=True):
        provider1 = get_data_provider(config)
        provider2 = get_data_provider(config)
    
    # Should be the same instance (cached)
    assert provider1 is provider2
    print(f"✓ Provider is correctly cached in session state")


def test_provider_inheritance_with_profile():
    """Test THE REAL ISSUE: profile inherits data_provider from base config.
    
    This is the exact scenario reported:
    - Base config has ui.data_provider: "direct"
    - Profile overrides API settings but NOT ui.data_provider
    - Expected: provider should still be "direct" (inherited from base)
    - Bug: provider was defaulting to something else
    """
    # Clear any cached provider
    if "data_provider" in st.session_state:
        del st.session_state.data_provider
    
    # Load config with profile (profile does NOT override ui.data_provider)
    from ab_cli.config.loader import load_config_with_profile
    
    config_path = TEST_DATA_DIR / "config-with-provider-and-profiles.yaml"
    
    # Load with "staging" profile
    config = load_config_with_profile(str(config_path), "staging")
    
    # Verify profile was applied (API endpoint changed)
    # Note: config loader may add trailing slash
    assert config.api_endpoint.rstrip("/") == "https://api.staging.com"
    assert config.client_id == "staging-client-id"
    
    # Verify UI config exists and has the provider from base
    assert config.ui is not None, "UI config should exist"
    assert hasattr(config.ui, "data_provider"), "UI config should have data_provider"
    assert config.ui.data_provider == "direct", f"Expected 'direct' but got '{config.ui.data_provider}'"
    
    # Get provider WITHOUT environment variable
    with patch.dict(os.environ, {}, clear=True):
        provider = get_data_provider(config)
    
    # THIS IS THE KEY TEST: should get DirectDataProvider (inherited from base config)
    assert isinstance(provider, DirectDataProvider), (
        f"Expected DirectDataProvider but got {type(provider).__name__}. "
        f"This means provider inheritance from base config is broken!"
    )
    print(f"✓ Profile correctly inherits data_provider='direct' from base config")
