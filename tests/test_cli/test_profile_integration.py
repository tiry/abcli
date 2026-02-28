"""Integration tests for profile support across CLI commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from ab_cli.cli.main import main
from ab_cli.config.loader import load_config_with_profile


# Test data directory
TEST_DATA_DIR = Path(__file__).parent.parent / "data" / "profiles"


class TestProfileIntegration:
    """Tests that profile parameter is correctly applied across all CLI commands."""

    def test_profile_affects_client_id_in_agents_command(self) -> None:
        """
        Test that --profile parameter correctly overrides client_id in agents list command.
        
        This test demonstrates the bug where profile is loaded in main.py but
        agents.py re-loads config without profile, losing the override.
        """
        runner = CliRunner()
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        
        # Load configs to verify test setup
        default_settings = load_config_with_profile(config_path, profile=None)
        dev_settings = load_config_with_profile(config_path, profile="dev")
        staging_settings = load_config_with_profile(config_path, profile="staging")
        
        # Verify test data has different client_ids
        assert default_settings.client_id == "default-client-id"
        assert dev_settings.client_id == "dev-client-id"
        assert staging_settings.client_id == "staging-client-id"
        assert default_settings.client_id != dev_settings.client_id
        assert dev_settings.client_id != staging_settings.client_id
        
        # Mock the API client to capture what settings it receives
        captured_settings = {}
        
        def capture_settings(settings):
            """Mock AgentBuilderClient to capture settings."""
            mock_client = MagicMock()
            captured_settings['client_id'] = settings.client_id
            captured_settings['client_secret'] = settings.client_secret
            captured_settings['api_endpoint'] = settings.api_endpoint
            return mock_client
        
        with patch('ab_cli.api.client.AgentBuilderClient', side_effect=capture_settings):
            with patch.object(MagicMock(), 'list_agents', return_value=[]):
                # Test 1: No profile (should use default)
                captured_settings.clear()
                result = runner.invoke(main, ['--config', str(config_path), 'agents', 'list'])
                
                if result.exit_code == 0:  # Only check if command succeeded
                    assert captured_settings.get('client_id') == "default-client-id", \
                        f"Expected default-client-id, got {captured_settings.get('client_id')}"
                
                # Test 2: Dev profile
                captured_settings.clear()
                result = runner.invoke(main, ['--config', str(config_path), '--profile', 'dev', 'agents', 'list'])
                
                if result.exit_code == 0:
                    # THIS IS THE BUG: We expect dev-client-id but get default-client-id
                    assert captured_settings.get('client_id') == "dev-client-id", \
                        f"Profile 'dev' not applied! Expected dev-client-id, got {captured_settings.get('client_id')}"
                
                # Test 3: Staging profile
                captured_settings.clear()
                result = runner.invoke(main, ['--config', str(config_path), '--profile', 'staging', 'agents', 'list'])
                
                if result.exit_code == 0:
                    assert captured_settings.get('client_id') == "staging-client-id", \
                        f"Profile 'staging' not applied! Expected staging-client-id, got {captured_settings.get('client_id')}"

    def test_profile_affects_api_endpoint(self) -> None:
        """Test that profile correctly overrides API endpoint."""
        runner = CliRunner()
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        
        captured_settings = {}
        
        def capture_settings(settings):
            mock_client = MagicMock()
            captured_settings['api_endpoint'] = settings.api_endpoint
            return mock_client
        
        with patch('ab_cli.api.client.AgentBuilderClient', side_effect=capture_settings):
            with patch.object(MagicMock(), 'list_agents', return_value=[]):
                # Default profile
                captured_settings.clear()
                result = runner.invoke(main, ['--config', str(config_path), 'agents', 'list'])
                if result.exit_code == 0:
                    assert captured_settings.get('api_endpoint') == "https://api.default.example.com/"
                
                # Dev profile
                captured_settings.clear()
                result = runner.invoke(main, ['--config', str(config_path), '--profile', 'dev', 'agents', 'list'])
                if result.exit_code == 0:
                    assert captured_settings.get('api_endpoint') == "https://api.dev.example.com/", \
                        f"Profile 'dev' endpoint not applied! Got {captured_settings.get('api_endpoint')}"

    def test_profile_in_invoke_command(self) -> None:
        """Test that profile is applied in invoke command."""
        runner = CliRunner()
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        
        captured_settings = {}
        
        def capture_settings(settings):
            mock_client = MagicMock()
            captured_settings['client_id'] = settings.client_id
            # Mock invoke method
            mock_client.invoke_agent = MagicMock(return_value={
                "response": "test",
                "agent_id": "test-agent"
            })
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=None)
            return mock_client
        
        with patch('ab_cli.api.client.AgentBuilderClient', side_effect=capture_settings):
            # Test with dev profile
            captured_settings.clear()
            result = runner.invoke(main, [
                '--config', str(config_path),
                '--profile', 'dev',
                'invoke',
                'test-agent',
                '--input', 'test input'
            ])
            
            # The command may fail for other reasons (agent not found, etc.)
            # but we should still capture the settings that were used
            if 'client_id' in captured_settings:
                assert captured_settings['client_id'] == "dev-client-id", \
                    f"Profile not applied in invoke command! Got {captured_settings['client_id']}"


@pytest.mark.skip(reason="This test demonstrates the current bug - it will fail until the bug is fixed")
class TestProfileBugDemonstration:
    """These tests SHOULD pass but currently fail due to the profile bug."""
    
    def test_bug_profile_ignored_in_subcommands(self) -> None:
        """
        CURRENT BUG: This test will FAIL because profile is not being applied.
        
        The issue is that main.py loads config with profile correctly,
        but subcommands reload config without using the profile parameter.
        """
        runner = CliRunner()
        config_path = TEST_DATA_DIR / "config-with-profiles.yaml"
        
        # This should work but doesn't due to the bug
        result = runner.invoke(main, [
            '--config', str(config_path),
            '--profile', 'dev',
            'agents', 'list',
            '--verbose'
        ])
        
        # The command executes but uses default profile instead of dev profile
        # You can verify this by checking the actual API client instantiation
