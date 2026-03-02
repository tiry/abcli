"""Tests for editor utility functions."""

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ab_cli.config.settings import ABSettings
from ab_cli.utils.editor import get_editor, open_editor


class TestGetEditor:
    """Test the get_editor function."""

    def test_override_takes_priority(self):
        """Test that command-line override has highest priority."""
        config = ABSettings(
            client_id="test",
            client_secret="secret",
            editor="vim",
        )
        result = get_editor(config, override="emacs")
        assert result == "emacs"

    def test_config_file_setting(self):
        """Test that config file setting is used when no override."""
        config = ABSettings(
            client_id="test",
            client_secret="secret",
            editor="nano",
        )
        result = get_editor(config, override=None)
        assert result == "nano"

    def test_visual_env_var(self, monkeypatch):
        """Test that $VISUAL is used when config is not set."""
        monkeypatch.setenv("VISUAL", "code")
        monkeypatch.delenv("EDITOR", raising=False)

        config = ABSettings(
            client_id="test",
            client_secret="secret",
        )
        result = get_editor(config, override=None)
        assert result == "code"

    def test_editor_env_var(self, monkeypatch):
        """Test that $EDITOR is used when $VISUAL is not set."""
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.setenv("EDITOR", "vim")

        config = ABSettings(
            client_id="test",
            client_secret="secret",
        )
        result = get_editor(config, override=None)
        assert result == "vim"

    def test_platform_default_unix(self, monkeypatch):
        """Test platform default for Unix systems."""
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.delenv("EDITOR", raising=False)

        config = ABSettings(
            client_id="test",
            client_secret="secret",
        )

        with patch("platform.system", return_value="Darwin"):  # macOS
            result = get_editor(config, override=None)
            assert result == "vi"

        with patch("platform.system", return_value="Linux"):
            result = get_editor(config, override=None)
            assert result == "vi"

    def test_platform_default_windows(self, monkeypatch):
        """Test platform default for Windows."""
        monkeypatch.delenv("VISUAL", raising=False)
        monkeypatch.delenv("EDITOR", raising=False)

        config = ABSettings(
            client_id="test",
            client_secret="secret",
        )

        with patch("platform.system", return_value="Windows"):
            result = get_editor(config, override=None)
            assert result == "notepad.exe"

    def test_priority_order(self, monkeypatch):
        """Test that priority order is respected."""
        monkeypatch.setenv("VISUAL", "visual-editor")
        monkeypatch.setenv("EDITOR", "editor-fallback")

        # Override beats everything
        config = ABSettings(
            client_id="test",
            client_secret="secret",
            editor="config-editor",
        )
        assert get_editor(config, override="override-editor") == "override-editor"

        # Config beats environment
        assert get_editor(config, override=None) == "config-editor"

        # VISUAL beats EDITOR
        config_no_editor = ABSettings(
            client_id="test",
            client_secret="secret",
        )
        assert get_editor(config_no_editor, override=None) == "visual-editor"


class TestOpenEditor:
    """Test the open_editor function."""

    def test_open_editor_success(self, tmp_path):
        """Test successful editor invocation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = open_editor(test_file, "vim")

            assert result == 0
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert args == ["vim", str(test_file)]

    def test_open_editor_with_flags(self, tmp_path):
        """Test editor invocation with command flags."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            result = open_editor(test_file, "code --wait")

            assert result == 0
            args = mock_run.call_args[0][0]
            assert args == ["code", "--wait", str(test_file)]

    def test_open_editor_not_found(self, tmp_path):
        """Test error when editor is not found."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("Editor not found")

            with pytest.raises(FileNotFoundError) as exc_info:
                open_editor(test_file, "nonexistent-editor")

            assert "nonexistent-editor" in str(exc_info.value)
            assert "not found" in str(exc_info.value)

    def test_open_editor_failure(self, tmp_path):
        """Test editor returning non-zero exit code."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)

            result = open_editor(test_file, "vim")

            assert result == 1

    def test_open_editor_subprocess_error(self, tmp_path):
        """Test subprocess error handling."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.SubprocessError("Failed to launch")

            with pytest.raises(subprocess.SubprocessError) as exc_info:
                open_editor(test_file, "vim")

            assert "Failed to launch" in str(exc_info.value)
