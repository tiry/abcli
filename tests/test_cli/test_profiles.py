"""Tests for profiles CLI command."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from ab_cli.cli.profiles import profiles


# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "profiles"


@pytest.fixture
def runner() -> CliRunner:
    """Create a CLI test runner."""
    return CliRunner()


class TestProfilesList:
    """Tests for 'ab profiles list' command."""

    def test_list_profiles_with_profiles(self, runner: CliRunner) -> None:
        """Test listing profiles when profiles are defined."""
        config_path = str(TEST_DATA_DIR / "config-with-profiles.yaml")
        result = runner.invoke(profiles, ["list", "-c", config_path])

        assert result.exit_code == 0
        assert "dev" in result.output
        assert "staging" in result.output
        assert "prod" in result.output
        assert "Found 3 profile(s)" in result.output

    def test_list_profiles_no_profiles(self, runner: CliRunner) -> None:
        """Test listing profiles when no profiles are defined."""
        config_path = str(TEST_DATA_DIR / "config-no-profiles.yaml")
        result = runner.invoke(profiles, ["list", "-c", config_path])

        assert result.exit_code == 0
        assert "No profiles defined" in result.output
        assert "To add profiles" in result.output

    def test_list_profiles_no_config_file(self, runner: CliRunner) -> None:
        """Test listing profiles when config file doesn't exist."""
        result = runner.invoke(profiles, ["list", "-c", "nonexistent.yaml"])

        # Click will handle the path validation and exit before reaching our code
        assert result.exit_code != 0

    def test_list_profiles_shows_usage_hints(self, runner: CliRunner) -> None:
        """Test that list command shows usage hints."""
        config_path = str(TEST_DATA_DIR / "config-with-profiles.yaml")
        result = runner.invoke(profiles, ["list", "-c", config_path])

        assert result.exit_code == 0
        assert "ab --profile dev" in result.output
        assert "ab --profile staging" in result.output
        assert "ab --profile prod" in result.output


class TestProfilesShow:
    """Tests for 'ab profiles show' command."""

    def test_show_dev_profile(self, runner: CliRunner) -> None:
        """Test showing dev profile configuration."""
        config_path = str(TEST_DATA_DIR / "config-with-profiles.yaml")
        result = runner.invoke(profiles, ["show", "dev", "-c", config_path])

        assert result.exit_code == 0
        assert "Profile: dev" in result.output
        # Client IDs are redacted, check for partial match
        assert "dev-" in result.output or "..." in result.output
        assert "https://api.dev.example.com/" in result.output
        assert "timeout" in result.output.lower()
        assert "60.0s" in result.output  # Dev profile timeout

    def test_show_staging_profile(self, runner: CliRunner) -> None:
        """Test showing staging profile configuration."""
        config_path = str(TEST_DATA_DIR / "config-with-profiles.yaml")
        result = runner.invoke(profiles, ["show", "staging", "-c", config_path])

        assert result.exit_code == 0
        assert "Profile: staging" in result.output
        # Check for API endpoint instead of redacted client_id
        assert "https://api.staging.example.com/" in result.output

    def test_show_prod_profile(self, runner: CliRunner) -> None:
        """Test showing prod profile configuration."""
        config_path = str(TEST_DATA_DIR / "config-with-profiles.yaml")
        result = runner.invoke(profiles, ["show", "prod", "-c", config_path])

        assert result.exit_code == 0
        assert "Profile: prod" in result.output
        # Check for API endpoint instead of redacted client_id
        assert "https://api.prod.example.com/" in result.output
        assert "45.0s" in result.output  # Prod profile timeout

    def test_show_default_profile(self, runner: CliRunner) -> None:
        """Test showing default (base) configuration without profile name."""
        config_path = str(TEST_DATA_DIR / "config-with-profiles.yaml")
        result = runner.invoke(profiles, ["show", "-c", config_path])

        assert result.exit_code == 0
        assert "default (base configuration)" in result.output
        # Check for API endpoint instead of redacted client_id
        assert "https://api.default.example.com/" in result.output
        assert "30.0s" in result.output  # Default timeout

    def test_show_invalid_profile(self, runner: CliRunner) -> None:
        """Test showing a profile that doesn't exist."""
        config_path = str(TEST_DATA_DIR / "config-with-profiles.yaml")
        result = runner.invoke(profiles, ["show", "nonexistent", "-c", config_path])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()
        assert "Available profiles:" in result.output

    def test_show_profile_redacts_secrets(self, runner: CliRunner) -> None:
        """Test that show command redacts sensitive information."""
        config_path = str(TEST_DATA_DIR / "config-with-profiles.yaml")
        result = runner.invoke(profiles, ["show", "dev", "-c", config_path])

        assert result.exit_code == 0
        # client_secret should be redacted
        assert "********" in result.output
        # client_id should be partially redacted
        assert "..." in result.output

    def test_show_profile_shows_usage_example(self, runner: CliRunner) -> None:
        """Test that show command displays usage examples."""
        config_path = str(TEST_DATA_DIR / "config-with-profiles.yaml")
        result = runner.invoke(profiles, ["show", "dev", "-c", config_path])

        assert result.exit_code == 0
        assert "To use this profile" in result.output
        assert "ab --profile dev" in result.output

    def test_show_nested_config_merge(self, runner: CliRunner) -> None:
        """Test showing profile with nested config overrides."""
        config_path = str(TEST_DATA_DIR / "config-nested-override.yaml")
        result = runner.invoke(profiles, ["show", "test", "-c", config_path])

        assert result.exit_code == 0
        assert "Profile: test" in result.output
        # Should show overridden UI config
        assert "direct" in result.output or "Direct" in result.output
        # Should show overridden timeout
        assert "90.0s" in result.output


class TestProfilesCommand:
    """Tests for main profiles command group."""

    def test_profiles_help(self, runner: CliRunner) -> None:
        """Test profiles command help output."""
        result = runner.invoke(profiles, ["--help"])

        assert result.exit_code == 0
        assert "Manage configuration profiles" in result.output
        assert "list" in result.output
        assert "show" in result.output

    def test_profiles_list_help(self, runner: CliRunner) -> None:
        """Test profiles list subcommand help."""
        result = runner.invoke(profiles, ["list", "--help"])

        assert result.exit_code == 0
        assert "List all available profiles" in result.output

    def test_profiles_show_help(self, runner: CliRunner) -> None:
        """Test profiles show subcommand help."""
        result = runner.invoke(profiles, ["show", "--help"])

        assert result.exit_code == 0
        assert "Show merged configuration" in result.output


class TestProfilesEdgeCases:
    """Tests for edge cases and error handling."""

    def test_show_profile_from_config_without_profiles(self, runner: CliRunner) -> None:
        """Test showing a profile when config has no profiles section."""
        config_path = str(TEST_DATA_DIR / "config-no-profiles.yaml")
        result = runner.invoke(profiles, ["show", "dev", "-c", config_path])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_show_default_from_config_without_profiles(self, runner: CliRunner) -> None:
        """Test showing default config when no profiles section exists."""
        config_path = str(TEST_DATA_DIR / "config-no-profiles.yaml")
        result = runner.invoke(profiles, ["show", "-c", config_path])

        assert result.exit_code == 0
        assert "default (base configuration)" in result.output
        # Check for API endpoint instead of redacted client_id
        assert "https://api.test.example.com/" in result.output
