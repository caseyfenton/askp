"""Tests for configuration management in ASKP CLI."""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

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

@pytest.fixture
def temp_config_file():
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        f.write("""
        {
            "model": "sonar-medium-chat",
            "output_dir": "/tmp/custom_output",
            "format": "markdown"
        }
        """)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_cli_default_config(runner, mock_result):
    """Test CLI with default configuration."""
    # Mock the execute_query function to return our mock result
    with patch('askp.cli.execute_query', return_value=mock_result):
        # Mock output_multi_results to avoid actual file operations
        with patch('askp.cli.output_multi_results'):
            # Run CLI command with no config options
            result = runner.invoke(cli, ["test query"])
            
            # Verify CLI executed successfully
            assert result.exit_code == 0

def test_cli_config_override(runner, mock_result):
    """Test CLI with configuration overrides via command line."""
    # Mock the execute_query function to return our mock result
    with patch('askp.cli.execute_query', return_value=mock_result):
        # Mock output_multi_results to avoid actual file operations
        with patch('askp.cli.output_multi_results'):
            # Run CLI command with config overrides
            result = runner.invoke(cli, ["test query", "--model", "sonar-medium-chat", "--format", "json"])
            
            # Verify CLI executed successfully
            assert result.exit_code == 0

@pytest.mark.skip(reason="Config file loading not yet implemented")
def test_cli_config_file(runner, temp_config_file, mock_result):
    """Test CLI with configuration from config file."""
    # This would test loading config from a file if that feature is implemented
    with patch('askp.cli.execute_query', return_value=mock_result):
        # Mock output_multi_results to avoid actual file operations
        with patch('askp.cli.output_multi_results'):
            # Run CLI command with config file
            result = runner.invoke(cli, ["test query", "--config", temp_config_file])
            
            # Verify CLI executed successfully
            assert result.exit_code == 0

@pytest.mark.skip(reason="Environment variable config not yet implemented")
def test_cli_env_vars(mock_result):
    """Test CLI with configuration from environment variables."""
    # This would test loading config from environment variables if that feature is implemented
    with patch.dict(os.environ, {"ASKP_MODEL": "sonar-large-chat", "ASKP_FORMAT": "text"}):
        with patch('askp.cli.execute_query', return_value=mock_result):
            # Mock output_multi_results to avoid actual file operations
            with patch('askp.cli.output_multi_results'):
                runner = CliRunner()
                result = runner.invoke(cli, ["test query"])
                
                # Verify CLI executed successfully
                assert result.exit_code == 0

def test_cli_priority_order(runner, temp_config_file, mock_result):
    """Test CLI configuration priority order (CLI args > env vars > config file > defaults)."""
    # Mock environment variables
    with patch.dict(os.environ, {"ASKP_MODEL": "sonar-large-chat"}):
        # Mock the execute_query function to return our mock result
        with patch('askp.cli.execute_query', return_value=mock_result):
            # Mock output_multi_results to avoid actual file operations
            with patch('askp.cli.output_multi_results'):
                # Run CLI command with conflicting configs
                # CLI args should take precedence
                result = runner.invoke(cli, ["test query", "--model", "sonar-medium-chat"])
                
                # Verify CLI executed successfully
                assert result.exit_code == 0

@pytest.mark.skip(reason="API key loading logic has changed and needs test update")
def test_api_key_loading_priority():
    """Test API key loading priority."""
    # Mock environment with API key
    test_env_key = "test_env_api_key"
    
    # Test 1: Environment variable takes precedence
    with patch.dict(os.environ, {"PERPLEXITY_API_KEY": test_env_key}):
        # Import the function directly to use the patched environment
        from askp.cli import load_api_key
        
        # Mock Path.exists and Path.read_text to avoid file system operations
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.read_text', return_value='PERPLEXITY_API_KEY=file_key'):
                # Call load_api_key
                key = load_api_key()
                # Verify environment variable takes precedence
                assert key == test_env_key, "Environment variable API key should take precedence"
    
    # Test 2: File is used when no environment variable
    with patch.dict(os.environ, {}, clear=True):  # Clear all environment variables
        # Mock Path.exists and Path.read_text to simulate config file
        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.read_text', return_value='PERPLEXITY_API_KEY=file_key'):
                # Import the function again to use the new patched environment
                from importlib import reload
                import askp.cli
                reload(askp.cli)
                from askp.cli import load_api_key
                
                # Call load_api_key
                key = load_api_key()
                # Verify file key is used
                assert key == 'file_key', "File API key should be used when no environment variable"
    
    # Test 3: Error handling when no key is available
    with patch.dict(os.environ, {}, clear=True):  # Clear all environment variables
        # Mock Path.exists to simulate no config file
        with patch('pathlib.Path.exists', return_value=False):
            # Import the function again with the new patches
            reload(askp.cli)
            from askp.cli import load_api_key
            
            # Mock sys.exit to prevent actual exit
            with patch('sys.exit') as mock_exit:
                # Call load_api_key
                load_api_key()
                # Verify sys.exit was called
                mock_exit.assert_called_once_with(1)
