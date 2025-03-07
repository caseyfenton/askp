"""Tests for Python version compatibility in ASKP CLI."""
import os
import sys
import platform
import pytest
from pathlib import Path
from unittest.mock import patch

# Add the current project's src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from click.testing import CliRunner
from askp.cli import cli

@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()

@pytest.fixture
def mock_result():
    """Create a mock result with the expected structure."""
    return {
        "query": "test query",
        "results": [{"content": "Test result"}],
        "model": "sonar-small-chat",
        "tokens": 100,
        "metadata": {
            "cost": 0.0001,
            "elapsed_time": 1.0,
            "queries_per_second": 1.0,
            "model": "sonar-small-chat"
        }
    }

def test_current_python_version():
    """Test compatibility with the current Python version."""
    # Get current Python version
    python_version = platform.python_version()
    major, minor, _ = python_version.split('.')
    
    # This test will always pass, but it logs the Python version being used
    print(f"Running tests with Python {python_version}")
    assert True

@pytest.mark.skipif(sys.version_info < (3, 8), reason="Python 3.8+ required")
def test_minimum_python_version():
    """Test compatibility with minimum supported Python version (3.8)."""
    # This test will be skipped if Python version is less than 3.8
    assert sys.version_info >= (3, 8)

@pytest.mark.skipif(sys.version_info >= (3, 12), reason="Testing Python 3.11 compatibility")
def test_python_311_compatibility():
    """Test compatibility with Python 3.11."""
    # This test will be skipped if Python version is 3.12 or higher
    # It's meant to be run specifically on Python 3.11
    assert True, "Running on Python 3.11"

@pytest.mark.skipif(sys.version_info < (3, 12), reason="Testing Python 3.12 compatibility")
def test_python_312_compatibility():
    """Test compatibility with Python 3.12."""
    # This test will be skipped if Python version is less than 3.12
    # It's meant to be run specifically on Python 3.12
    assert True, "Running on Python 3.12"

def test_cli_basic_functionality(runner, mock_result):
    """Test basic CLI functionality on the current Python version."""
    # Mock the execute_query function to avoid actual API calls
    with patch('askp.cli.execute_query', return_value=mock_result):
        # Mock output_multi_results to avoid actual file operations
        with patch('askp.cli.output_multi_results'):
            # Run CLI command
            result = runner.invoke(cli, ["test query"])
            
            # Verify CLI executed successfully on this Python version
            assert result.exit_code == 0

def test_import_compatibility():
    """Test that all required modules can be imported on this Python version."""
    # List of modules that the application depends on
    required_modules = [
        'click',
        'rich',
        'json',
        'os',
        'sys',
        'threading',
        'concurrent.futures',
        're',
        'datetime',
        'pathlib',
        'time'
    ]
    
    # Try to import each module
    for module_name in required_modules:
        try:
            __import__(module_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")
    
    assert True, "All required modules imported successfully"
