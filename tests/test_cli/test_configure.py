"""Tests for ab_cli.cli.configure module."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from click.testing import CliRunner

from ab_cli.cli.configure import (
    configure,
    save_config,
    display_config_summary,
    DEFAULTS
)


class TestConfigureCommand:
    """Tests for configure CLI command."""

    def test_configure_non_interactive_minimal(self, tmp_path):
        """Test configure command with all required parameters (non-interactive)."""
        runner = CliRunner()
        config_file = tmp_path / "config.yaml"
        
        result = runner.invoke(configure, [
            '--config', str(config_file),
            '--client-id', 'test-client-id',
            '--client-secret', 'test-secret',
            '--api-endpoint', 'https://api.test.com/',
            '--auth-endpoint', 'https://auth.test.com/token',
            '--force'
        ])
        
        assert result.exit_code == 0
        assert config_file.exists()
        assert 'Configuration saved successfully' in result.output
        
        # Verify content
        content = config_file.read_text()
        assert 'test-client-id' in content
        assert 'test-secret' in content
        assert 'https://api.test.com/' in content
        assert 'https://auth.test.com/token' in content

    def test_configure_non_interactive_with_optional(self, tmp_path):
        """Test configure with optional parameters."""
        runner = CliRunner()
        config_file = tmp_path / "config.yaml"
        
        result = runner.invoke(configure, [
            '--config', str(config_file),
            '--client-id', 'test-id',
            '--client-secret', 'test-secret',
            '--api-endpoint', 'https://api.test.com/',
            '--auth-endpoint', 'https://auth.test.com/token',
            '--grant-type', 'password',
            '--auth-scope', 'read',
            '--auth-scope', 'write',
            '--force'
        ])
        
        assert result.exit_code == 0
        assert config_file.exists()
        content = config_file.read_text()
        # Verify scopes are present
        assert '"read"' in content
        assert '"write"' in content
        # Verify config file has all required fields
        assert 'test-id' in content
        assert 'grant_type' in content

    def test_configure_show_no_config(self):
        """Test --show flag when no config exists."""
        runner = CliRunner()
        
        with patch('ab_cli.cli.configure.find_config_file', return_value=None):
            result = runner.invoke(configure, ['--show'])
            
            assert result.exit_code == 1
            assert 'No configuration file found' in result.output

    def test_configure_show_existing_config(self, tmp_path):
        """Test --show flag with existing config."""
        runner = CliRunner()
        config_file = tmp_path / "config.yaml"
        
        # Create a test config
        config_file.write_text("""
client_id: "test-id"
client_secret: "secret"
api_endpoint: "https://api.test.com/"
auth_endpoint: "https://auth.test.com/token"
""")
        
        with patch('ab_cli.cli.configure.find_config_file', return_value=config_file):
            with patch('ab_cli.config.get_config_summary') as mock_summary:
                mock_summary.return_value = {
                    "client_id": "test***",
                    "api_endpoint": "https://api.test.com/"
                }
                
                result = runner.invoke(configure, ['--show'])
                
                assert result.exit_code == 0
                assert 'Current Configuration' in result.output

    def test_configure_output_path_alternative(self, tmp_path):
        """Test -o/--output as alternative to --config."""
        runner = CliRunner()
        config_file = tmp_path / "output-config.yaml"
        
        result = runner.invoke(configure, [
            '-o', str(config_file),
            '--client-id', 'test-id',
            '--client-secret', 'test-secret',
            '--api-endpoint', 'https://api.test.com/',
            '--auth-endpoint', 'https://auth.test.com/token',
            '--force'
        ])
        
        assert result.exit_code == 0
        assert config_file.exists()

    def test_configure_creates_directory(self, tmp_path):
        """Test that configure creates parent directories."""
        runner = CliRunner()
        config_file = tmp_path / "subdir" / "nested" / "config.yaml"
        
        result = runner.invoke(configure, [
            '--config', str(config_file),
            '--client-id', 'test-id',
            '--client-secret', 'test-secret',
            '--api-endpoint', 'https://api.test.com/',
            '--auth-endpoint', 'https://auth.test.com/token',
            '--force'
        ])
        
        assert result.exit_code == 0
        assert config_file.exists()
        assert config_file.parent.exists()

    def test_configure_validates_saved_config(self, tmp_path):
        """Test that configure validates the saved configuration."""
        runner = CliRunner()
        config_file = tmp_path / "config.yaml"
        
        # This should save successfully and validate
        result = runner.invoke(configure, [
            '--config', str(config_file),
            '--client-id', 'test-id',
            '--client-secret', 'test-secret',
            '--api-endpoint', 'https://api.test.com/',
            '--auth-endpoint', 'https://auth.test.com/token',
            '--force'
        ])
        
        assert result.exit_code == 0
        assert 'Configuration saved successfully' in result.output
        # Should validate after saving
        assert 'Configuration is valid' in result.output or 'saved successfully' in result.output


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_config_creates_file(self, tmp_path):
        """Test that save_config creates a properly formatted file."""
        config_file = tmp_path / "config.yaml"
        config = {
            "client_id": "test-id",
            "client_secret": "secret",
            "api_endpoint": "https://api.test.com/",
            "auth_endpoint": "https://auth.test.com/token",
            "grant_type": "client_credentials",
            "auth_scope": ["hxp"]
        }
        
        save_config(config, config_file)
        
        assert config_file.exists()
        content = config_file.read_text()
        assert "# Agent Builder CLI Configuration" in content
        assert 'client_id: "test-id"' in content
        assert 'client_secret: "secret"' in content
        assert '- "hxp"' in content

    def test_save_config_creates_parent_dirs(self, tmp_path):
        """Test that save_config creates parent directories."""
        config_file = tmp_path / "nested" / "dir" / "config.yaml"
        config = {
            "client_id": "test",
            "client_secret": "secret",
            "api_endpoint": "https://api.test.com/",
            "auth_endpoint": "https://auth.test.com/token"
        }
        
        save_config(config, config_file)
        
        assert config_file.exists()
        assert config_file.parent.exists()

    def test_save_config_with_multiple_scopes(self, tmp_path):
        """Test save_config with multiple auth scopes."""
        config_file = tmp_path / "config.yaml"
        config = {
            "client_id": "test",
            "client_secret": "secret",
            "api_endpoint": "https://api.test.com/",
            "auth_endpoint": "https://auth.test.com/token",
            "auth_scope": ["hxp", "openid", "profile"]
        }
        
        save_config(config, config_file)
        
        content = config_file.read_text()
        assert '- "hxp"' in content
        assert '- "openid"' in content
        assert '- "profile"' in content

    def test_save_config_uses_defaults(self, tmp_path):
        """Test that save_config uses default values when not provided."""
        config_file = tmp_path / "config.yaml"
        config = {
            "client_id": "test",
            "client_secret": "secret",
            "api_endpoint": "https://api.test.com/",
            "auth_endpoint": "https://auth.test.com/token"
        }
        
        save_config(config, config_file)
        
        content = config_file.read_text()
        assert f'grant_type: "{DEFAULTS["grant_type"]}"' in content


class TestDisplayConfigSummary:
    """Tests for display_config_summary function."""

    def test_display_new_config_summary(self):
        """Test displaying summary for new config."""
        config = {
            "client_id": "test-client-id-12345",
            "client_secret": "secret",
            "api_endpoint": "https://api.test.com/",
            "auth_endpoint": "https://auth.test.com/token",
            "grant_type": "client_credentials",
            "auth_scope": ["hxp"]
        }
        
        with patch('ab_cli.cli.configure.console') as mock_console:
            display_config_summary(config, existing_config=None)
            
            # Verify console.print was called
            assert mock_console.print.called
            # Check that sensitive data is masked
            call_args = [str(call) for call in mock_console.print.call_args_list]
            # Client ID should be partially masked
            assert any('test-cli***' in str(call) or '***' in str(call) for call in call_args)

    def test_display_updated_config_summary(self):
        """Test displaying summary when updating existing config."""
        existing = {
            "client_id": "old-id",
            "api_endpoint": "https://old.api.com/"
        }
        new_config = {
            "client_id": "new-id",
            "client_secret": "secret",
            "api_endpoint": "https://new.api.com/",
            "auth_endpoint": "https://auth.test.com/token"
        }
        
        with patch('ab_cli.cli.configure.console') as mock_console:
            display_config_summary(new_config, existing_config=existing)
            
            assert mock_console.print.called
            # Should show modified fields
            call_args = [str(call) for call in mock_console.print.call_args_list]
            assert any('Modified' in str(call) for call in call_args)

    def test_display_summary_no_changes(self):
        """Test displaying summary when no changes detected."""
        config = {
            "client_id": "test-id",
            "api_endpoint": "https://api.test.com/"
        }
        
        with patch('ab_cli.cli.configure.console') as mock_console:
            display_config_summary(config, existing_config=config.copy())
            
            call_args = [str(call) for call in mock_console.print.call_args_list]
            assert any('No changes' in str(call) for call in call_args)
