"""Tests for ab_cli.cli.client_utils module."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from ab_cli.cli.client_utils import get_client_with_error_handling
from ab_cli.config.exceptions import ConfigurationError


class TestGetClientWithErrorHandling:
    """Tests for get_client_with_error_handling function."""

    def test_get_client_with_valid_config(self):
        """Test getting client with valid configuration."""
        with patch('ab_cli.cli.client_utils.find_config_file') as mock_find, \
             patch('ab_cli.cli.client_utils.load_config') as mock_load, \
             patch('ab_cli.cli.client_utils.AgentBuilderClient') as mock_client:
            
            mock_settings = Mock()
            mock_find.return_value = 'config.yaml'
            mock_load.return_value = mock_settings
            mock_client_instance = Mock()
            mock_client.return_value = mock_client_instance
            
            result = get_client_with_error_handling()
            
            assert result == mock_client_instance
            mock_find.assert_called_once()
            mock_load.assert_called_once_with('config.yaml')
            mock_client.assert_called_once_with(mock_settings)

    def test_get_client_with_custom_config_path(self):
        """Test getting client with custom config path."""
        with patch('ab_cli.cli.client_utils.load_config') as mock_load, \
             patch('ab_cli.cli.client_utils.AgentBuilderClient') as mock_client:
            
            mock_settings = Mock()
            mock_load.return_value = mock_settings
            mock_client_instance = Mock()
            mock_client.return_value = mock_client_instance
            
            result = get_client_with_error_handling(config_path='/custom/config.yaml')
            
            assert result == mock_client_instance
            mock_load.assert_called_once_with('/custom/config.yaml')
            mock_client.assert_called_once_with(mock_settings)

    def test_get_client_no_config_file_found(self):
        """Test error handling when no config file is found."""
        with patch('ab_cli.cli.client_utils.find_config_file') as mock_find, \
             patch('ab_cli.cli.client_utils.error_console') as mock_console:
            
            mock_find.return_value = None
            
            with pytest.raises(SystemExit) as exc_info:
                get_client_with_error_handling()
            
            assert exc_info.value.code == 1
            mock_find.assert_called_once()
            # Verify error message was printed
            assert mock_console.print.called
            # Check that helpful message about 'ab configure' was printed
            print_calls = [str(call) for call in mock_console.print.call_args_list]
            assert any('ab configure' in str(call) for call in print_calls)

    def test_get_client_configuration_error(self):
        """Test error handling when configuration is invalid."""
        with patch('ab_cli.cli.client_utils.find_config_file') as mock_find, \
             patch('ab_cli.cli.client_utils.load_config') as mock_load, \
             patch('ab_cli.cli.client_utils.error_console') as mock_console:
            
            mock_find.return_value = 'config.yaml'
            mock_load.side_effect = ConfigurationError("Invalid configuration: missing client_id")
            
            with pytest.raises(SystemExit) as exc_info:
                get_client_with_error_handling()
            
            assert exc_info.value.code == 1
            mock_load.assert_called_once_with('config.yaml')
            # Verify error message was printed
            assert mock_console.print.called
            print_calls = [str(call) for call in mock_console.print.call_args_list]
            # Check that error message and help text were printed
            assert any('Configuration error' in str(call) for call in print_calls)
            assert any('ab configure' in str(call) for call in print_calls)

    def test_get_client_custom_path_configuration_error(self):
        """Test error handling with custom path and invalid config."""
        with patch('ab_cli.cli.client_utils.load_config') as mock_load, \
             patch('ab_cli.cli.client_utils.error_console') as mock_console:
            
            mock_load.side_effect = ConfigurationError("Invalid auth endpoint")
            
            with pytest.raises(SystemExit) as exc_info:
                get_client_with_error_handling(config_path='/custom/config.yaml')
            
            assert exc_info.value.code == 1
            mock_load.assert_called_once_with('/custom/config.yaml')
            assert mock_console.print.called
