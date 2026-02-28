"""Tests for profile support in configuration loading."""

from pathlib import Path

import pytest

from ab_cli.config.loader import (
    deep_merge_dicts,
    get_available_profiles,
    load_config_with_profile,
)


# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "profiles"


class TestDeepMergeDicts:
    """Tests for the deep_merge_dicts utility function."""

    def test_simple_override(self) -> None:
        """Test simple value override."""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = deep_merge_dicts(base, override)

        assert result == {"a": 1, "b": 3, "c": 4}

    def test_nested_dict_merge(self) -> None:
        """Test nested dictionary merging."""
        base = {"outer": {"inner1": 1, "inner2": 2}, "other": 3}
        override = {"outer": {"inner2": 20, "inner3": 30}}
        result = deep_merge_dicts(base, override)

        assert result == {"outer": {"inner1": 1, "inner2": 20, "inner3": 30}, "other": 3}

    def test_deep_nested_merge(self) -> None:
        """Test deeply nested dictionary merging."""
        base = {"level1": {"level2": {"level3": {"value": 1, "other": 2}}}}
        override = {"level1": {"level2": {"level3": {"value": 10}}}}
        result = deep_merge_dicts(base, override)

        assert result == {"level1": {"level2": {"level3": {"value": 10, "other": 2}}}}

    def test_list_override(self) -> None:
        """Test that lists are replaced, not merged."""
        base = {"list": [1, 2, 3]}
        override = {"list": [4, 5]}
        result = deep_merge_dicts(base, override)

        assert result == {"list": [4, 5]}

    def test_dict_replaces_non_dict(self) -> None:
        """Test that dict value replaces non-dict value."""
        base = {"key": "string"}
        override = {"key": {"nested": "value"}}
        result = deep_merge_dicts(base, override)

        assert result == {"key": {"nested": "value"}}

    def test_non_dict_replaces_dict(self) -> None:
        """Test that non-dict value replaces dict value."""
        base = {"key": {"nested": "value"}}
        override = {"key": "string"}
        result = deep_merge_dicts(base, override)

        assert result == {"key": "string"}

    def test_empty_override(self) -> None:
        """Test merging with empty override."""
        base = {"a": 1, "b": 2}
        override = {}
        result = deep_merge_dicts(base, override)

        assert result == {"a": 1, "b": 2}

    def test_empty_base(self) -> None:
        """Test merging with empty base."""
        base = {}
        override = {"a": 1, "b": 2}
        result = deep_merge_dicts(base, override)

        assert result == {"a": 1, "b": 2}


class TestGetAvailableProfiles:
    """Tests for getting available profile names."""

    def test_get_profiles_from_config(self) -> None:
        """Test getting profiles from config with profiles."""
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        profiles = get_available_profiles(config_path)

        assert set(profiles) == {"dev", "staging", "prod"}

    def test_no_profiles_section(self) -> None:
        """Test config without profiles section."""
        config_path = TEST_DATA_DIR / "config-no-profiles.yaml"
        profiles = get_available_profiles(config_path)

        assert profiles == []

    def test_profiles_order_preserved(self) -> None:
        """Test that profile order is preserved from YAML."""
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        profiles = get_available_profiles(config_path)

        # YAML should preserve insertion order in Python 3.7+
        assert profiles == ["dev", "staging", "prod"]


class TestLoadConfigWithProfile:
    """Tests for loading configuration with profile support."""

    def test_load_without_profile(self) -> None:
        """Test loading config without specifying a profile (default)."""
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        settings = load_config_with_profile(config_path, profile=None)

        # Should use default values
        assert settings.client_id == "default-client-id"
        assert settings.client_secret == "default-client-secret"
        assert settings.api_endpoint == "https://api.default.example.com/"
        assert settings.timeout == 30.0
        assert settings.max_retries == 3

    def test_load_dev_profile(self) -> None:
        """Test loading with dev profile."""
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        settings = load_config_with_profile(config_path, profile="dev")

        # Should override with dev values
        assert settings.client_id == "dev-client-id"
        assert settings.client_secret == "dev-client-secret"
        assert settings.api_endpoint == "https://api.dev.example.com/"
        assert settings.auth_endpoint == "https://auth.dev.example.com/token"
        assert settings.timeout == 60.0
        # Unspecified values should use default
        assert settings.max_retries == 3

    def test_load_staging_profile(self) -> None:
        """Test loading with staging profile."""
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        settings = load_config_with_profile(config_path, profile="staging")

        assert settings.client_id == "staging-client-id"
        assert settings.client_secret == "staging-client-secret"
        assert settings.api_endpoint == "https://api.staging.example.com/"
        assert settings.max_retries == 5
        # Unspecified timeout should use default
        assert settings.timeout == 30.0

    def test_load_prod_profile(self) -> None:
        """Test loading with prod profile."""
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        settings = load_config_with_profile(config_path, profile="prod")

        assert settings.client_id == "prod-client-id"
        assert settings.timeout == 45.0
        assert settings.max_retries == 5
        assert settings.default_output_format == "json"

    def test_profile_overrides_base(self) -> None:
        """Test that profile values override base configuration."""
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        
        # Load default
        default_settings = load_config_with_profile(config_path, profile=None)
        assert default_settings.client_id == "default-client-id"
        
        # Load dev profile
        dev_settings = load_config_with_profile(config_path, profile="dev")
        assert dev_settings.client_id == "dev-client-id"
        
        # Confirm override worked
        assert dev_settings.client_id != default_settings.client_id

    def test_profile_partial_override(self) -> None:
        """Test that unspecified profile values use base config."""
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        settings = load_config_with_profile(config_path, profile="dev")

        # dev profile doesn't specify max_retries, should use default
        assert settings.max_retries == 3
        # dev profile doesn't specify default_output_format, should use default
        assert settings.default_output_format == "table"

    def test_nested_config_merge(self) -> None:
        """Test deep merge for nested configuration (ui, pagination)."""
        config_path = TEST_DATA_DIR / "config-nested-override.yaml"
        
        # Load default
        default_settings = load_config_with_profile(config_path, profile=None)
        assert default_settings.ui is not None
        assert default_settings.ui.data_provider == "cli"
        assert default_settings.ui.mock_data_dir == "/default/path"
        assert default_settings.timeout == 30.0
        
        # Load test profile with nested override
        test_settings = load_config_with_profile(config_path, profile="test")
        assert test_settings.ui is not None
        assert test_settings.ui.data_provider == "direct"  # Overridden
        assert test_settings.ui.mock_data_dir == "/test/path"  # Overridden
        assert test_settings.timeout == 90.0  # Overridden
        # Pagination should remain from base
        assert test_settings.pagination is not None
        assert test_settings.pagination.max_filter_pages == 10

    def test_invalid_profile_name(self) -> None:
        """Test error when requesting non-existent profile."""
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        
        with pytest.raises(ValueError, match="Profile 'nonexistent' not found"):
            load_config_with_profile(config_path, profile="nonexistent")

    def test_config_without_profiles(self) -> None:
        """Test that configs without profiles section work normally."""
        config_path = TEST_DATA_DIR / "config-no-profiles.yaml"
        
        # Should work without profile
        settings = load_config_with_profile(config_path, profile=None)
        assert settings.client_id == "test-client-id"
        
        # Should fail with profile (no profiles defined)
        with pytest.raises(ValueError, match="Profile 'dev' not found"):
            load_config_with_profile(config_path, profile="dev")

    def test_profiles_not_included_in_settings(self) -> None:
        """Test that profiles section is not included in settings object."""
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        settings = load_config_with_profile(config_path, profile="dev")

        # profiles field should be None (not populated from config)
        assert settings.profiles is None


class TestProfilePrecedence:
    """Tests for profile precedence and environment variable interaction."""

    def test_profile_precedence_order(self) -> None:
        """Test that profile values override base config values."""
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        
        # Base config
        base = load_config_with_profile(config_path, profile=None)
        
        # Profile should override
        profiled = load_config_with_profile(config_path, profile="dev")
        
        assert base.api_endpoint != profiled.api_endpoint
        assert profiled.api_endpoint == "https://api.dev.example.com/"

    def test_multiple_profiles_isolated(self) -> None:
        """Test that loading different profiles gives different configs."""
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        
        dev = load_config_with_profile(config_path, profile="dev")
        staging = load_config_with_profile(config_path, profile="staging")
        prod = load_config_with_profile(config_path, profile="prod")
        
        # All should have different endpoints
        assert dev.api_endpoint != staging.api_endpoint
        assert staging.api_endpoint != prod.api_endpoint
        assert dev.api_endpoint != prod.api_endpoint


