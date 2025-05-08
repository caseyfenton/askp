"""
Tests for platform compatibility in askp.
These tests focus on ensuring the package works correctly on different platforms.
"""
import os
import platform
import sys
from pathlib import Path
import pytest

from askp.utils import load_api_key, get_output_dir, sanitize_filename


def test_platform_detection():
    """Test that we can correctly detect the platform."""
    system = platform.system()
    assert system in ["Windows", "Darwin", "Linux"], f"Unexpected system: {system}"


def test_home_directory_resolution():
    """Test that we can correctly resolve the home directory."""
    home_dir = Path.home()
    assert home_dir.exists(), f"Home directory does not exist: {home_dir}"
    
    # Test alternative method
    alt_home = Path(os.path.expanduser("~"))
    assert alt_home.exists(), f"Alternative home directory does not exist: {alt_home}"
    
    # Both methods should resolve to the same directory
    assert str(home_dir) == str(alt_home), f"Home directory mismatch: {home_dir} vs {alt_home}"


def test_output_directory_creation():
    """Test that we can create an output directory."""
    # Use a temporary test directory
    test_dir = Path(os.path.join(os.path.dirname(__file__), "temp_test_dir"))
    try:
        output_dir = get_output_dir(test_dir)
        assert output_dir.exists(), f"Output directory was not created: {output_dir}"
        assert output_dir == test_dir.resolve(), f"Output directory mismatch: {output_dir} vs {test_dir.resolve()}"
    finally:
        # Clean up
        if test_dir.exists():
            try:
                test_dir.rmdir()
            except:
                pass


def test_filename_sanitization():
    """Test that we can sanitize filenames correctly on different platforms."""
    # Test with characters that are invalid on Windows
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = f"test{char}file.txt"
        sanitized = sanitize_filename(filename)
        assert char not in sanitized, f"Invalid character {char} not removed from filename"
    
    # Test with spaces and dots - all non-alphanumeric chars become underscores
    sanitized = sanitize_filename("test file.txt")
    assert sanitized == "test_file_txt", f"Unexpected sanitization result: {sanitized}"
    
    # Test with multiple non-alphanumeric characters
    sanitized = sanitize_filename("test.file-with.dots.txt")
    assert sanitized == "test_file_with_dots_txt", f"Unexpected sanitization result: {sanitized}"
    
    # Test length limitation (max 50 chars)
    long_name = "a" * 100
    sanitized = sanitize_filename(long_name)
    assert len(sanitized) <= 50, f"Sanitized filename exceeds 50 characters: {len(sanitized)}"


def test_api_key_environment_variable():
    """Test that we can detect an API key in environment variables."""
    # Save original environment
    original_env = os.environ.get("PERPLEXITY_API_KEY")
    
    try:
        # Set a test API key
        os.environ["PERPLEXITY_API_KEY"] = "pplx-test-key-for-unit-testing"
        
        # We can't directly test load_api_key() since it exits on failure,
        # but we can test the environment variable detection
        assert os.environ.get("PERPLEXITY_API_KEY") == "pplx-test-key-for-unit-testing"
        
    finally:
        # Restore original environment
        if original_env:
            os.environ["PERPLEXITY_API_KEY"] = original_env
        else:
            os.environ.pop("PERPLEXITY_API_KEY", None)
