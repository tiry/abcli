"""Tests for ab_cli.cli.pagination_utils module."""

import pytest
from unittest.mock import Mock, patch, call

from ab_cli.cli.pagination_utils import (
    get_single_keypress,
    show_pagination_info,
    show_next_page_command
)
from ab_cli.api.pagination import PaginatedResult


class TestGetSingleKeypress:
    """Tests for get_single_keypress function."""

    def test_get_single_keypress_space(self):
        """Test getting space key press."""
        with patch('ab_cli.cli.pagination_utils.sys.stdin') as mock_stdin, \
             patch('ab_cli.cli.pagination_utils.termios') as mock_termios, \
             patch('ab_cli.cli.pagination_utils.tty') as mock_tty:
            
            mock_stdin.fileno.return_value = 0
            mock_stdin.read.return_value = ' '
            mock_termios.tcgetattr.return_value = ['old', 'settings']
            
            result = get_single_keypress()
            
            assert result == ' '
            mock_termios.tcsetattr.assert_called_once()
            mock_tty.setraw.assert_called_once()

    def test_get_single_keypress_q(self):
        """Test getting 'q' key press."""
        with patch('ab_cli.cli.pagination_utils.sys.stdin') as mock_stdin, \
             patch('ab_cli.cli.pagination_utils.termios') as mock_termios, \
             patch('ab_cli.cli.pagination_utils.tty') as mock_tty:
            
            mock_stdin.fileno.return_value = 0
            mock_stdin.read.return_value = 'q'
            mock_termios.tcgetattr.return_value = ['old', 'settings']
            
            result = get_single_keypress()
            
            assert result == 'q'


class TestShowPaginationInfo:
    """Tests for show_pagination_info function."""

    def test_show_unfiltered_pagination_first_page(self):
        """Test showing pagination info for first page without filters."""
        with patch('ab_cli.cli.pagination_utils.console') as mock_console:
            result = PaginatedResult(
                agents=[{"id": f"agent-{i}"} for i in range(10)],
                offset=0,
                limit=10,
                total_count=50,
                has_filters=False,
                agent_type=None,
                name_pattern=None
            )
            
            show_pagination_info(result)
            
            # Check that console.print was called
            assert mock_console.print.called
            call_args = str(mock_console.print.call_args)
            assert "Page: 1/5" in call_args
            assert "1-10 of 50" in call_args
            assert "Page size: 10" in call_args

    def test_show_unfiltered_pagination_middle_page(self):
        """Test showing pagination info for middle page."""
        with patch('ab_cli.cli.pagination_utils.console') as mock_console:
            result = PaginatedResult(
                agents=[{"id": f"agent-{i}"} for i in range(10)],
                offset=20,
                limit=10,
                total_count=50,
                has_filters=False,
                agent_type=None,
                name_pattern=None
            )
            
            show_pagination_info(result)
            
            call_args = str(mock_console.print.call_args)
            assert "Page: 3/5" in call_args
            assert "21-30 of 50" in call_args

    def test_show_filtered_pagination_by_type(self):
        """Test showing pagination info for filtered results by type."""
        with patch('ab_cli.cli.pagination_utils.console') as mock_console:
            result = PaginatedResult(
                agents=[{"id": f"agent-{i}"} for i in range(5)],
                offset=0,
                limit=10,
                total_count=None,
                has_filters=True,
                agent_type="rag",
                name_pattern=None
            )
            
            show_pagination_info(result)
            
            call_args = str(mock_console.print.call_args)
            assert "1-5 of ???" in call_args
            assert "type: rag" in call_args
            assert "Page size: 10" in call_args

    def test_show_filtered_pagination_by_name(self):
        """Test showing pagination info for filtered results by name."""
        with patch('ab_cli.cli.pagination_utils.console') as mock_console:
            result = PaginatedResult(
                agents=[{"id": f"agent-{i}"} for i in range(3)],
                offset=0,
                limit=10,
                total_count=None,
                has_filters=True,
                agent_type=None,
                name_pattern="calculator"
            )
            
            show_pagination_info(result)
            
            call_args = str(mock_console.print.call_args)
            assert "1-3 of ???" in call_args
            assert "name: calculator" in call_args

    def test_show_filtered_pagination_by_both(self):
        """Test showing pagination info for filtered results by type and name."""
        with patch('ab_cli.cli.pagination_utils.console') as mock_console:
            result = PaginatedResult(
                agents=[{"id": f"agent-{i}"} for i in range(2)],
                offset=0,
                limit=10,
                total_count=None,
                has_filters=True,
                agent_type="tool",
                name_pattern="calc"
            )
            
            show_pagination_info(result)
            
            call_args = str(mock_console.print.call_args)
            assert "1-2 of ???" in call_args
            assert "type: tool" in call_args
            assert "name: calc" in call_args


class TestShowNextPageCommand:
    """Tests for show_next_page_command function."""

    def test_show_next_page_with_more_results(self):
        """Test showing next page command when more results exist."""
        with patch('ab_cli.cli.pagination_utils.console') as mock_console:
            result = PaginatedResult(
                agents=[{"id": f"agent-{i}"} for i in range(10)],
                offset=0,
                limit=10,
                total_count=50,
                has_filters=False,
                agent_type=None,
                name_pattern=None
            )
            
            show_next_page_command(result)
            
            call_args = str(mock_console.print.call_args)
            assert "ab agents list --offset 10 -l 10" in call_args

    def test_show_next_page_with_page_flag(self):
        """Test showing next page command using --page flag."""
        with patch('ab_cli.cli.pagination_utils.console') as mock_console:
            result = PaginatedResult(
                agents=[{"id": f"agent-{i}"} for i in range(10)],
                offset=20,
                limit=10,
                total_count=50,
                has_filters=False,
                agent_type=None,
                name_pattern=None
            )
            
            show_next_page_command(result, use_page=True)
            
            call_args = str(mock_console.print.call_args)
            assert "ab agents list --page 4 -l 10" in call_args

    def test_show_next_page_with_type_filter(self):
        """Test showing next page command with type filter."""
        with patch('ab_cli.cli.pagination_utils.console') as mock_console:
            result = PaginatedResult(
                agents=[{"id": f"agent-{i}"} for i in range(10)],
                offset=0,
                limit=10,
                total_count=50,
                has_filters=True,
                agent_type="rag",
                name_pattern=None
            )
            
            show_next_page_command(result)
            
            call_args = str(mock_console.print.call_args)
            assert "--type rag" in call_args

    def test_show_next_page_with_name_filter(self):
        """Test showing next page command with name filter."""
        with patch('ab_cli.cli.pagination_utils.console') as mock_console:
            result = PaginatedResult(
                agents=[{"id": f"agent-{i}"} for i in range(10)],
                offset=0,
                limit=10,
                total_count=50,
                has_filters=True,
                agent_type=None,
                name_pattern="calculator"
            )
            
            show_next_page_command(result)
            
            call_args = str(mock_console.print.call_args)
            assert '--name "calculator"' in call_args

    def test_show_next_page_with_both_filters(self):
        """Test showing next page command with both filters."""
        with patch('ab_cli.cli.pagination_utils.console') as mock_console:
            result = PaginatedResult(
                agents=[{"id": f"agent-{i}"} for i in range(10)],
                offset=0,
                limit=10,
                total_count=50,
                has_filters=True,
                agent_type="tool",
                name_pattern="calc"
            )
            
            show_next_page_command(result)
            
            call_args = str(mock_console.print.call_args)
            assert "--type tool" in call_args
            assert '--name "calc"' in call_args

    def test_show_next_page_at_end(self):
        """Test showing message when at end of results."""
        with patch('ab_cli.cli.pagination_utils.console') as mock_console:
            # At end: offset=45, 5 agents, total=50 -> has_more = (45 + 5 < 50) = False
            result = PaginatedResult(
                agents=[{"id": f"agent-{i}"} for i in range(5)],
                offset=45,
                limit=10,
                total_count=50,
                has_filters=False,
                agent_type=None,
                name_pattern=None
            )
            
            # Verify has_more is False for this scenario
            assert result.has_more is False
            
            show_next_page_command(result)
            
            call_args = str(mock_console.print.call_args)
            assert "End of results" in call_args
