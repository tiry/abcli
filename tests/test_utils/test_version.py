"""Tests for version utility functions."""

import pytest

from ab_cli.utils.version import increment_version


class TestIncrementVersion:
    """Test the increment_version function."""

    def test_increment_simple_version(self):
        """Test incrementing simple version formats."""
        assert increment_version("v1.0") == "v1.1"
        assert increment_version("v2.5") == "v2.6"
        assert increment_version("v1.9") == "v1.10"

    def test_increment_semantic_version(self):
        """Test incrementing semantic version formats."""
        assert increment_version("v1.0.3") == "v1.0.4"
        assert increment_version("1.2.3") == "1.2.4"
        assert increment_version("2.10.99") == "2.10.100"

    def test_increment_with_prefix(self):
        """Test incrementing versions with text prefixes."""
        assert increment_version("release-5") == "release-6"
        assert increment_version("version-10") == "version-11"
        assert increment_version("v-1-2-3") == "v-1-2-4"

    def test_increment_no_numbers(self):
        """Test incrementing strings with no numbers."""
        assert increment_version("no-numbers") == "no-numbers.1"
        assert increment_version("alpha") == "alpha.1"
        assert increment_version("") == ".1"

    def test_increment_complex_formats(self):
        """Test incrementing complex version formats."""
        assert increment_version("2024.01.15") == "2024.01.16"
        assert increment_version("1.0-beta.3") == "1.0-beta.4"
        assert increment_version("v1.0.0-rc.2") == "v1.0.0-rc.3"

    def test_increment_last_number_only(self):
        """Test that only the last number is incremented."""
        assert increment_version("v1.2.3") == "v1.2.4"
        assert increment_version("5.10.99.1") == "5.10.99.2"

    def test_increment_with_trailing_text(self):
        """Test incrementing versions with trailing non-numeric text."""
        # Since we increment the LAST number, trailing text is preserved
        assert increment_version("v1.0-alpha") == "v1.1-alpha"
        assert increment_version("1.2.3-beta") == "1.2.4-beta"
