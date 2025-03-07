"""Tests for ASKP CLI output formatting."""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

# Add the current project's src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from click.testing import CliRunner
import pytest
from askp.cli import cli, format_text, format_markdown, output_multi_results

@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()

@pytest.fixture
def mock_result():
    """Create a mock result that matches the actual format from search_perplexity."""
    return {
        'query': 'test query',
        'results': [{'content': 'Result 1'}, {'content': 'Result 2'}],
        'model': 'sonar-small-chat',
        'tokens': 100,
        'bytes': 500,
        'metadata': {
            'model': 'sonar-small-chat',
            'tokens': 100,
            'cost': 0.0001,
            'num_results': 2,
            'verbose': False,
            'elapsed_time': 5.0,
            'queries_per_second': 0.2,
            'file_path': '/path/to/test_result.md'
        },
        'model_info': {
            'id': 'sonar-small-chat',
            'model': 'sonar-small-chat',
            'cost_per_million': 1.0,
            'reasoning': False
        },
        'tokens_used': 100,
        'citations': []
    }

@pytest.fixture
def mock_deep_research_results():
    """Create mock results for deep research mode."""
    results = []
    for i in range(5):
        result = {
            'query': f'research query {i}',
            'results': [{'content': f'Research Result {i}'}],
            'model': 'sonar-pro',
            'tokens': 100,
            'bytes': 500,
            'metadata': {
                'model': 'sonar-pro',
                'tokens': 100,
                'cost': 0.0001,
                'num_results': 1,
                'verbose': False,
                'elapsed_time': 10.0,
                'queries_per_second': 0.5,
                'file_path': f'/path/to/component_{i:03d}.json'
            },
            'model_info': {
                'id': 'sonar-pro',
                'model': 'sonar-pro',
                'cost_per_million': 1.0,
                'reasoning': False
            },
            'tokens_used': 100,
            'citations': []
        }
        results.append(result)
    return results

def test_output_multi_results_markdown(mock_deep_research_results, tmp_path):
    """Test output formatting for multiple results in markdown format."""
    # Setup
    options = {
        'format': 'markdown',
        'output_dir': str(tmp_path),
        'model': 'sonar-pro',
        'deep': False,
        'verbose': False
    }
    
    # Mock open to avoid actually writing files
    with patch('builtins.open', MagicMock()):
        # Mock click.echo to capture output
        with patch('click.echo') as mock_echo:
            # Call function
            output_multi_results(mock_deep_research_results, options)
            
            # Verify output format
            assert mock_echo.call_count > 0
            # Check that the output contains the expected format
            output_str = ''.join([call.args[0] for call in mock_echo.call_args_list if isinstance(call.args[0], str)])
            assert '5 topics' in output_str
            assert '2,500B' in output_str
            assert '500t' in output_str
            assert '$0.0005' in output_str

def test_output_multi_results_deep_research(mock_deep_research_results, tmp_path):
    """Test output formatting for deep research mode."""
    # Setup
    options = {
        'format': 'markdown',
        'output_dir': str(tmp_path),
        'model': 'sonar-pro',
        'deep': True,
        'verbose': False,
        'research_overview': 'Test research topic'
    }
    
    # Mock open to avoid actually writing files
    with patch('builtins.open', MagicMock()):
        # Mock click.echo to capture output
        with patch('click.echo') as mock_echo:
            # Call function
            output_multi_results(mock_deep_research_results, options)
            
            # Verify output format
            assert mock_echo.call_count > 0
            # Check that the output contains the expected format
            output_str = ''.join([call.args[0] for call in mock_echo.call_args_list if isinstance(call.args[0], str)])
            assert 'Synthesizing 5 topics... deep research finished.' in output_str
            assert '5 topics' in output_str
            assert '2,500B' in output_str
            assert '500t' in output_str
            assert '$0.0005' in output_str
            assert 'component_000.json' in output_str

def test_output_multi_results_quiet_mode(mock_deep_research_results, tmp_path):
    """Test output formatting with quiet mode enabled."""
    # Setup
    options = {
        'format': 'markdown',
        'output_dir': str(tmp_path),
        'model': 'sonar-pro',
        'deep': True,
        'verbose': False,
        'quiet': True,
        'research_overview': 'Test research topic'
    }
    
    # Mock open to avoid actually writing files
    with patch('builtins.open', MagicMock()):
        # Mock click.echo to capture output
        with patch('click.echo') as mock_echo:
            # Call function
            output_multi_results(mock_deep_research_results, options)
            
            # Verify no output was produced
            assert mock_echo.call_count == 0

def test_output_multi_results_verbose_mode(mock_deep_research_results, tmp_path):
    """Test output formatting with verbose mode enabled."""
    # Setup
    options = {
        'format': 'markdown',
        'output_dir': str(tmp_path),
        'model': 'sonar-pro',
        'deep': True,
        'verbose': True,
        'research_overview': 'Test research topic'
    }
    
    # Mock open to avoid actually writing files
    with patch('builtins.open', MagicMock()):
        # Mock rich.console.Console.print to capture output
        with patch('rich.console.Console.print') as mock_print:
            # Call function
            output_multi_results(mock_deep_research_results, options)
            
            # Verify rich output was produced
            assert mock_print.call_count > 0

def test_output_multi_results_text_format(mock_deep_research_results, tmp_path):
    """Test output formatting in text format."""
    # Setup
    options = {
        'format': 'text',
        'output_dir': str(tmp_path),
        'model': 'sonar-pro',
        'deep': False,
        'verbose': False
    }
    
    # Mock open to avoid actually writing files
    with patch('builtins.open', MagicMock()):
        # Mock click.echo to capture output
        with patch('click.echo') as mock_echo:
            # Call function
            output_multi_results(mock_deep_research_results, options)
            
            # Verify output format
            assert mock_echo.call_count > 0
            # Check that the output contains the expected format
            output_str = ''.join([call.args[0] for call in mock_echo.call_args_list if isinstance(call.args[0], str)])
            assert '5 topics' in output_str
            assert '2,500B' in output_str
            assert '500t' in output_str
            assert '$0.0005' in output_str

def test_output_multi_results_json_format(mock_deep_research_results, tmp_path):
    """Test output formatting in JSON format."""
    # Setup
    options = {
        'format': 'json',
        'output_dir': str(tmp_path),
        'model': 'sonar-pro',
        'deep': False,
        'verbose': False
    }
    
    # Mock open to avoid actually writing files
    with patch('builtins.open', MagicMock()):
        # Mock click.echo to capture output
        with patch('click.echo') as mock_echo:
            # Call function
            output_multi_results(mock_deep_research_results, options)
            
            # Verify output format
            assert mock_echo.call_count > 0

def test_output_multi_results_component_file_cleanup(mock_deep_research_results, tmp_path):
    """Test component file cleanup in deep research mode."""
    # Setup
    components_dir = os.path.join(tmp_path, "components")
    os.makedirs(components_dir, exist_ok=True)
    
    # Create some mock component files
    for i in range(5):
        with open(os.path.join(components_dir, f"component_{i:03d}.json"), "w") as f:
            f.write(f"Test content {i}")
    
    options = {
        'format': 'markdown',
        'output_dir': str(tmp_path),
        'components_dir': components_dir,
        'model': 'sonar-pro',
        'deep': True,
        'verbose': False,
        'cleanup_component_files': True,
        'research_overview': 'Test research topic'
    }
    
    # Mock shutil.move to avoid actually moving files
    with patch('shutil.move') as mock_move:
        # Call function
        output_multi_results(mock_deep_research_results, options)
        
        # Verify that move was called for each component file
        assert mock_move.call_count == 5

def test_cli_deep_research_output(runner, mock_deep_research_results):
    """Test CLI output for deep research mode."""
    # Mock handle_deep_research to return our mock results
    with patch('askp.cli.handle_deep_research', return_value=mock_deep_research_results):
        # Mock output_multi_results to avoid actual output
        with patch('askp.cli.output_multi_results') as mock_output:
            # Run CLI command with deep research flag
            result = runner.invoke(cli, ["test query", "--deep"])
            
            # Verify CLI executed successfully
            assert result.exit_code == 0
            
            # Verify output_multi_results was called with the right parameters
            mock_output.assert_called_once()
            args, kwargs = mock_output.call_args
            assert args[0] == mock_deep_research_results
            assert kwargs.get('deep') is True

def test_cli_multi_query_output(runner, mock_result):
    """Test CLI output for multiple queries."""
    # Mock handle_multi_query to return a list of our mock results
    with patch('askp.cli.handle_multi_query', return_value=[mock_result, mock_result]):
        # Mock output_multi_results to avoid actual output
        with patch('askp.cli.output_multi_results') as mock_output:
            # Run CLI command with multiple queries
            result = runner.invoke(cli, ["query1", "query2"])
            
            # Verify CLI executed successfully
            assert result.exit_code == 0
            
            # Verify output_multi_results was called with the right parameters
            mock_output.assert_called_once()
            args, kwargs = mock_output.call_args
            assert len(args[0]) == 2
            assert kwargs.get('deep') is False

def test_cli_combined_flags(runner, mock_deep_research_results):
    """Test CLI with combined flags (deep research + quiet + cleanup)."""
    # Mock handle_deep_research to return our mock results
    with patch('askp.cli.handle_deep_research', return_value=mock_deep_research_results):
        # Mock output_multi_results to avoid actual output
        with patch('askp.cli.output_multi_results') as mock_output:
            # Run CLI command with multiple flags
            result = runner.invoke(cli, ["test query", "--deep", "--quiet", "--cleanup-component-files"])
            
            # Verify CLI executed successfully
            assert result.exit_code == 0
            
            # Verify output_multi_results was called with the right parameters
            mock_output.assert_called_once()
            args, kwargs = mock_output.call_args
            assert args[0] == mock_deep_research_results
            assert kwargs.get('deep') is True
            assert kwargs.get('quiet') is True
            assert kwargs.get('cleanup_component_files') is True
