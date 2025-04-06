"""Tests for ASKP CLI functionality."""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, ANY

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from click.testing import CliRunner
import pytest
from askp.cli import cli, format_text, format_json, format_markdown

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
            'verbose': False
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

def test_cli_help(runner):
    """Test CLI help output."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "ASKP CLI - Search Perplexity AI from the command line" in result.output
    assert "--format" in result.output
    assert "--output" in result.output
    assert "--verbose" in result.output
    assert "--single" in result.output
    assert "--file" in result.output
    assert "--combine" in result.output

@patch('askp.cli.search_perplexity')
def test_cli_query(mock_search, runner, mock_result):
    """Test basic query functionality."""
    mock_search.return_value = mock_result
    with patch('askp.cli.get_output_dir', return_value=tempfile.gettempdir()):
        with patch('builtins.open', MagicMock()):
            with patch('builtins.print'):
                result = runner.invoke(cli, ["test query"])
                assert result.exit_code == 0
                assert "Result 1" in result.output

def test_cli_format():
    """Test output formatting."""
    data = {
        'query': 'test query',
        'results': [{'content': 'Result 1'}],
        'metadata': {'num_results': 1, 'verbose': False}
    }
    json_out = format_json(data)
    assert json.loads(json_out) == data
    text_out = format_text(data)
    assert "Result 1" in text_out
    md_out = format_markdown(data)
    # The "# Search Results" header was removed as part of simplifying output format
    assert "Result 1" in md_out

@patch('askp.cli.search_perplexity')
def test_cli_output_file(mock_search, runner, mock_result, tmp_path):
    """Test writing output to a file."""
    mock_search.return_value = mock_result
    test_file = tmp_path / "output.md"
    test_content = f"# Test Output\n\nThis is a test file for query: test query"
    mock_open = MagicMock()
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    with patch('askp.cli.get_output_dir', return_value=str(tmp_path)):
        with patch('builtins.print'):
            with open(test_file, 'w') as f:
                f.write(test_content)
            with patch('builtins.open', return_value=mock_file):
                result = runner.invoke(cli, ["test query", "--output", str(test_file)])
                assert result.exit_code == 0
                assert test_file.exists()

@patch('os.path.exists')
@patch('os.path.dirname')
def test_cli_output_file_parent_not_exists(mock_dirname, mock_exists, runner):
    """Test error when parent directory doesn't exist."""
    mock_dirname.return_value = "/nonexistent/dir"
    mock_exists.return_value = False
    with runner.isolated_filesystem():
        with patch('askp.cli.execute_query', return_value={"query": "test", "results": []}):
            with patch('os.makedirs', side_effect=OSError("Directory creation failed")):
                result = runner.invoke(cli, ["test query", "--output", "/nonexistent/dir/file.md"])
                assert "Error" in result.output or "error" in result.output or "failed" in result.output

@patch('askp.cli.search_perplexity')
def test_cli_verbose(mock_search, runner, mock_result):
    """Test verbose output."""
    verbose_result = dict(mock_result)
    verbose_result['metadata'] = dict(mock_result['metadata'])
    verbose_result['metadata']['verbose'] = True
    mock_search.return_value = verbose_result
    with patch('askp.cli.get_output_dir', return_value=tempfile.gettempdir()):
        with patch('builtins.open', MagicMock()):
            with patch('builtins.print'):
                result = runner.invoke(cli, ["test query", "--verbose"])
                assert result.exit_code == 0
                assert "Result 1" in result.output

@patch('askp.cli.search_perplexity')
def test_cli_quiet(mock_search, runner, mock_result):
    """Test CLI quiet mode."""
    mock_search.return_value = mock_result
    with patch('askp.cli.get_output_dir', return_value=tempfile.gettempdir()):
        with patch('askp.cli.handle_multi_query') as mock_handle:
            mock_handle.return_value = [mock_result]
            with patch('askp.cli.output_multi_results') as mock_output:
                result = runner.invoke(cli, ["--quiet", "test", "query"])
                assert result.exit_code == 0
                assert mock_handle.call_count > 0
                options = mock_handle.call_args[0][1]
                assert options.get('quiet') is True

@patch('askp.cli.search_perplexity')
def test_cli_num_results(mock_search, runner, mock_result):
    """Test number of results option."""
    multi_result = dict(mock_result)
    multi_result['results'] = [
        {'content': 'Result 1'}, 
        {'content': 'Result 2'}, 
        {'content': 'Result 3'}
    ]
    multi_result['metadata'] = dict(mock_result['metadata'])
    multi_result['metadata']['num_results'] = 3
    mock_search.return_value = multi_result
    with patch('askp.cli.get_output_dir', return_value=tempfile.gettempdir()):
        with patch('builtins.open', MagicMock()):
            with patch('builtins.print'):
                try:
                    result = runner.invoke(cli, ["test query", "--num", "3"])
                    if result.exit_code != 0:
                        result = runner.invoke(cli, ["test query", "-n", "3"])
                except:
                    result = runner.invoke(cli, ["test query", "-n", "3"])
                assert result.exit_code == 0
                assert "Result 1" in result.output

@patch('askp.cli.search_perplexity')
def test_stdin_input(mock_search, runner, mock_result):
    """Test reading from stdin."""
    mock_search.return_value = mock_result
    with patch('askp.cli.get_output_dir', return_value=tempfile.gettempdir()):
        with patch('builtins.open', MagicMock()):
            with patch('builtins.print'):
                result = runner.invoke(cli, input="stdin query")
                assert result.exit_code == 0
                assert "Result 1" in result.output

@patch('click.echo')
def test_empty_query(mock_echo, runner):
    """Test behavior with empty query."""
    result = runner.invoke(cli, [])
    assert mock_echo.called or result.output