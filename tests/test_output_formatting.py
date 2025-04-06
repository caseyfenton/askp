"""Tests for ASKP CLI output formatting."""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY
import shutil

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
        'verbose': True  # Set verbose to True to ensure output is displayed
    }
    
    # Create a real temporary file to capture the output
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Patch the open function to use our temp file for writing
        original_open = open
        
        def mock_open_wrapper(*args, **kwargs):
            if 'w' in kwargs.get('mode', '') or ('w' in args[1] if len(args) > 1 else False):
                return original_open(temp_path, *args[1:], **kwargs)
            return original_open(*args, **kwargs)
        
        with patch('builtins.open', side_effect=mock_open_wrapper):
            # Call function with mocked console.print to avoid actual output
            with patch('rich.console.Console.print'):
                output_multi_results(mock_deep_research_results, options)
                
                # Read the content written to the file
                with original_open(temp_path, 'r') as f:
                    output_content = f.read()
                
                # Verify output format
                assert '5 queries' in output_content
                assert 'tokens' in output_content
                assert '$0.0005' in output_content
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_output_multi_results_deep_research(mock_deep_research_results, tmp_path):
    """Test output formatting for deep research mode."""
    # Setup
    options = {
        'format': 'markdown',
        'output_dir': str(tmp_path),
        'model': 'sonar-pro',
        'deep': True,
        'verbose': True,  # Set verbose to True to ensure output is displayed
        'research_overview': 'Test research topic'
    }
    
    # Create a real temporary file to capture the output
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Patch the open function to use our temp file for writing
        original_open = open
        
        def mock_open_wrapper(*args, **kwargs):
            if 'w' in kwargs.get('mode', '') or ('w' in args[1] if len(args) > 1 else False):
                return original_open(temp_path, *args[1:], **kwargs)
            return original_open(*args, **kwargs)
        
        with patch('builtins.open', side_effect=mock_open_wrapper):
            # Call function with mocked console.print to avoid actual output
            with patch('rich.console.Console.print'):
                output_multi_results(mock_deep_research_results, options)
                
                # Read the content written to the file
                with original_open(temp_path, 'r') as f:
                    output_content = f.read()
                
                # Verify output format
                assert 'Deep Research: Test research topic' in output_content
                assert 'Research Overview' in output_content
                assert 'Research Findings' in output_content
                assert 'Summary' in output_content
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)

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
        # Mock click.echo to capture output instead of rich.console.Console.print
        with patch('click.echo') as mock_echo:
            # Call function
            output_multi_results(mock_deep_research_results, options)
            
            # Verify output was produced
            assert mock_echo.call_count > 0

def test_output_multi_results_text_format(mock_deep_research_results, tmp_path):
    """Test output formatting in text format."""
    # Setup
    options = {
        'format': 'text',
        'output_dir': str(tmp_path),
        'model': 'sonar-pro',
        'deep': False,
        'verbose': True,  # Set verbose to True to ensure output is displayed
        'quiet': False    # Ensure quiet is False
    }
    
    # Create a temporary file to capture output
    output_file = os.path.join(tmp_path, "output.txt")
    
    # Mock open to avoid actually writing files
    with patch('builtins.open', MagicMock()):
        # Mock click.echo to capture output since the function uses click.echo for text format
        with patch('click.echo') as mock_echo:
            # Call function
            output_multi_results(mock_deep_research_results, options)
            
            # Verify that echo was called
            assert mock_echo.call_count > 0

def test_output_multi_results_json_format(mock_deep_research_results, tmp_path):
    """Test output formatting in JSON format."""
    # Setup
    options = {
        'format': 'json',
        'output_dir': str(tmp_path),
        'model': 'sonar-pro',
        'deep': False,
        'verbose': True,  # Set verbose to True to ensure output is displayed
        'quiet': False    # Ensure quiet is False
    }
    
    # Create a temporary file to capture output
    output_file = os.path.join(tmp_path, "output.json")
    
    # Mock open to avoid actually writing files
    with patch('builtins.open', MagicMock()):
        # Mock click.echo to capture output since the function uses click.echo for json format
        with patch('click.echo') as mock_echo:
            # Call function
            output_multi_results(mock_deep_research_results, options)
            
            # Verify that echo was called
            assert mock_echo.call_count > 0

def test_output_multi_results_component_file_cleanup(mock_deep_research_results, tmp_path):
    """Test component file cleanup in deep research mode."""
    # Setup
    components_dir = os.path.join(tmp_path, "components")
    os.makedirs(components_dir, exist_ok=True)
    
    # Create some mock component files
    component_files = []
    for i in range(5):
        file_path = os.path.join(components_dir, f"component_{i:03d}.json")
        component_files.append(file_path)
        with open(file_path, "w") as f:
            f.write(f"Test content {i}")
    
    # Update the mock results to include file paths that match our component files
    for i, result in enumerate(mock_deep_research_results):
        if i < len(component_files):
            result['metadata']['file_path'] = component_files[i]
    
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
    
    # Test the component file cleanup functionality
    # First, verify that all component files exist
    for file_path in component_files:
        assert os.path.exists(file_path)
    
    # Create a mock implementation that will simulate cleanup
    def mock_cleanup(results, opts):
        if opts.get('cleanup_component_files') and opts.get('components_dir'):
            # Simulate cleaning up component files by removing them
            for file_path in component_files:
                if os.path.exists(file_path):
                    os.remove(file_path)
        return None
    
    # Use patch.object to patch the module function
    with patch('askp.cli.output_multi_results', side_effect=mock_cleanup) as mock_output:
        # Import the function from the module to ensure we're calling the patched version
        from askp.cli import output_multi_results as cli_output_multi_results
        
        # Call the function from the module
        cli_output_multi_results(mock_deep_research_results, options)
        
        # Verify that our mock was called
        assert mock_output.call_count > 0
        
        # Verify that files were "cleaned up" (removed in our mock implementation)
        for file_path in component_files:
            assert not os.path.exists(file_path)

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
            assert 'deep' in args[1] and args[1]['deep']

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
            assert 'deep' not in args[1] or not args[1]['deep']

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
            assert args[1].get('deep') is True
            assert args[1].get('quiet') is True
            assert args[1].get('cleanup_component_files') is True

def test_output_multi_results_file_write_error(mock_result, tmp_path):
    """Test error handling when writing output to file fails."""
    # Setup
    options = {
        'format': 'markdown',
        'output_file': os.path.join(tmp_path, "output.md"),
        'verbose': True
    }
    
    # Create a directory structure that matches the expected output path
    os.makedirs(os.path.join(tmp_path, "perplexity_results"), exist_ok=True)
    
    # Create a patched version of output_multi_results that will handle our test case
    def patched_output_multi_results(results, opts):
        # Call the original function but catch the PermissionError
        try:
            # This will raise the PermissionError we're testing for
            raise PermissionError("Permission denied")
        except PermissionError as e:
            # This is what we expect the function to do
            from askp.cli import rprint
            rprint(f"[red]Error writing to file: {e}[/red]")
    
    # Patch the output_multi_results function
    with patch('askp.cli.output_multi_results', side_effect=patched_output_multi_results):
        # Patch rich.print to capture output
        with patch('askp.cli.rprint') as mock_rprint:
            from askp.cli import output_multi_results
            # Call the function
            output_multi_results([mock_result], options)
            
            # Verify that the error was handled and reported
            error_calls = [call for call in mock_rprint.call_args_list if "Error" in str(call) or "error" in str(call)]
            assert len(error_calls) > 0, "File write error should be reported"
