"""Tests for temporary file management utilities."""

import json
from pathlib import Path

import pytest

from ab_cli.utils.tempfile_manager import (
    cleanup_tempfile,
    create_agent_edit_tempfile,
    read_agent_edit_tempfile,
)


class TestCreateAgentEditTempfile:
    """Test the create_agent_edit_tempfile function."""

    def test_creates_file_with_correct_structure(self):
        """Test that temp file is created with correct JSON structure."""
        agent_id = "test-agent-123"
        version_label = "v1.0"
        config = {
            "llmModelId": "gpt-4",
            "systemPrompt": "You are a helpful assistant",
        }

        temp_file = create_agent_edit_tempfile(agent_id, version_label, config)

        try:
            assert temp_file.exists()
            assert temp_file.name.startswith("ab-agent-edit-test-agent-123-")
            assert temp_file.name.endswith(".json")

            # Read and verify content
            with open(temp_file, "r") as f:
                data = json.load(f)

            assert data["versionLabel"] == version_label
            assert data["config"] == config
        finally:
            cleanup_tempfile(temp_file)

    def test_file_has_pretty_formatting(self):
        """Test that JSON is formatted for easy editing."""
        agent_id = "test"
        version_label = "v1.0"
        config = {"key": "value"}

        temp_file = create_agent_edit_tempfile(agent_id, version_label, config)

        try:
            content = temp_file.read_text()
            # Pretty-printed JSON should have newlines
            assert "\n" in content
            # Should have indentation
            assert "  " in content
        finally:
            cleanup_tempfile(temp_file)

    def test_handles_complex_config(self):
        """Test handling of complex nested configuration."""
        agent_id = "complex-agent"
        version_label = "v2.5"
        config = {
            "llmModelId": "gpt-4",
            "systemPrompt": "Test",
            "tools": [
                {"name": "tool1", "params": {"key": "value"}},
                {"name": "tool2", "params": {"nested": {"deep": "value"}}},
            ],
            "inferenceConfig": {
                "temperature": 0.7,
                "maxTokens": 4000,
            },
        }

        temp_file = create_agent_edit_tempfile(agent_id, version_label, config)

        try:
            with open(temp_file, "r") as f:
                data = json.load(f)

            assert data["config"] == config
        finally:
            cleanup_tempfile(temp_file)


class TestReadAgentEditTempfile:
    """Test the read_agent_edit_tempfile function."""

    def test_reads_valid_file(self, tmp_path):
        """Test reading a valid edited file."""
        test_file = tmp_path / "test-edit.json"
        data = {
            "versionLabel": "v2.0",
            "config": {
                "llmModelId": "gpt-4",
                "systemPrompt": "Updated prompt",
            },
        }

        with open(test_file, "w") as f:
            json.dump(data, f)

        version_label, config = read_agent_edit_tempfile(test_file)

        assert version_label == "v2.0"
        assert config == data["config"]

    def test_rejects_missing_version_label(self, tmp_path):
        """Test that missing versionLabel raises KeyError."""
        test_file = tmp_path / "invalid.json"
        data = {"config": {"key": "value"}}

        with open(test_file, "w") as f:
            json.dump(data, f)

        with pytest.raises(KeyError) as exc_info:
            read_agent_edit_tempfile(test_file)

        assert "versionLabel" in str(exc_info.value)

    def test_rejects_missing_config(self, tmp_path):
        """Test that missing config raises KeyError."""
        test_file = tmp_path / "invalid.json"
        data = {"versionLabel": "v1.0"}

        with open(test_file, "w") as f:
            json.dump(data, f)

        with pytest.raises(KeyError) as exc_info:
            read_agent_edit_tempfile(test_file)

        assert "config" in str(exc_info.value)

    def test_rejects_invalid_json(self, tmp_path):
        """Test that invalid JSON raises JSONDecodeError."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            read_agent_edit_tempfile(test_file)

    def test_rejects_empty_version_label(self, tmp_path):
        """Test that empty versionLabel raises ValueError."""
        test_file = tmp_path / "invalid.json"
        data = {
            "versionLabel": "",
            "config": {"key": "value"},
        }

        with open(test_file, "w") as f:
            json.dump(data, f)

        with pytest.raises(ValueError) as exc_info:
            read_agent_edit_tempfile(test_file)

        assert "non-empty string" in str(exc_info.value)

    def test_rejects_non_dict_config(self, tmp_path):
        """Test that non-dict config raises ValueError."""
        test_file = tmp_path / "invalid.json"
        data = {
            "versionLabel": "v1.0",
            "config": "not a dict",
        }

        with open(test_file, "w") as f:
            json.dump(data, f)

        with pytest.raises(ValueError) as exc_info:
            read_agent_edit_tempfile(test_file)

        assert "dictionary" in str(exc_info.value)

    def test_file_not_found(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        test_file = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            read_agent_edit_tempfile(test_file)


class TestCleanupTempfile:
    """Test the cleanup_tempfile function."""

    def test_deletes_file(self, tmp_path):
        """Test that file is deleted."""
        test_file = tmp_path / "temp.json"
        test_file.write_text("test")

        assert test_file.exists()
        cleanup_tempfile(test_file)
        assert not test_file.exists()

    def test_keeps_file_when_requested(self, tmp_path):
        """Test that file is kept when keep=True."""
        test_file = tmp_path / "temp.json"
        test_file.write_text("test")

        cleanup_tempfile(test_file, keep=True)
        assert test_file.exists()

    def test_handles_nonexistent_file(self, tmp_path):
        """Test that cleanup doesn't fail on nonexistent file."""
        test_file = tmp_path / "nonexistent.json"

        # Should not raise
        cleanup_tempfile(test_file)

    def test_silently_handles_cleanup_errors(self, tmp_path):
        """Test that cleanup errors are silently ignored."""
        test_file = tmp_path / "test.json"
        test_file.write_text("test")

        # Make file readonly to cause deletion error
        test_file.chmod(0o444)

        # Should not raise even though deletion might fail
        cleanup_tempfile(test_file)


class TestEndToEndWorkflow:
    """Test the complete edit workflow."""

    def test_create_edit_read_cleanup(self):
        """Test the complete workflow: create → edit → read → cleanup."""
        # Step 1: Create temp file
        agent_id = "workflow-test"
        original_version = "v1.0"
        original_config = {
            "llmModelId": "gpt-4",
            "systemPrompt": "Original prompt",
        }

        temp_file = create_agent_edit_tempfile(
            agent_id, original_version, original_config
        )

        try:
            assert temp_file.exists()

            # Step 2: Simulate editing (modify the file)
            with open(temp_file, "r") as f:
                data = json.load(f)

            data["versionLabel"] = "v1.1"
            data["config"]["systemPrompt"] = "Updated prompt"

            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)

            # Step 3: Read back the changes
            new_version, new_config = read_agent_edit_tempfile(temp_file)

            assert new_version == "v1.1"
            assert new_config["systemPrompt"] == "Updated prompt"
            assert new_config["llmModelId"] == "gpt-4"  # Unchanged

        finally:
            # Step 4: Cleanup
            cleanup_tempfile(temp_file)
            assert not temp_file.exists()
