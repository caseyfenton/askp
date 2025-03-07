"""Tests for ASKD CLI multi-query functionality."""
import json
import os
import sys
from pathlib import Path

# Add the current project's src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner
from askp.cli import (
    cli, handle_multi_query, execute_query, 
    output_multi_results
)

@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()

@pytest.fixture
def mock_result():
    """Create a mock query result."""
    return {
        'query': 'test query',
        'results': [{'content': 'test content'}],
        'model': 'test-model',
        'tokens': 100,
        'bytes': 200,
        'metadata': {
            'model': 'test-model',
            'tokens': 100,
            'cost': 0.0001,
            'num_results': 1,
            'verbose': True
        },
        'tokens_used': 100,
        'model_info': {
            'id': 'test-model',
            'model': 'test-model',
            'cost_per_million': 1.0,
            'reasoning': False
        }
    }

@patch('askp.cli.execute_query')
@patch('askp.cli.handle_multi_query')
def test_cli_multi_flag(mock_handle_multi, mock_execute_query, runner):
    """Test CLI with multi-query mode (default)."""
    mock_handle_multi.return_value = [
        {
            'query': 'query1', 
            'results': [{'content': 'content1'}],
            'metadata': {'verbose': False}
        },
        {
            'query': 'query2', 
            'results': [{'content': 'content2'}],
            'metadata': {'verbose': False}
        }
    ]
    
    # The default is multi-query mode, so we don't need a special flag
    result = runner.invoke(cli, ["query1", "query2"])
    assert result.exit_code == 0
    
    # handle_multi_query should be called, not execute_query directly from CLI
    assert mock_handle_multi.call_count == 1
    
    # But execute_query is called from within handle_multi_query
    # We're not testing that here as it's covered by test_handle_multi_query

@patch('askp.cli.handle_multi_query')
def test_cli_file_input(mock_handle_multi, runner, tmp_path):
    """Test CLI with file input."""
    mock_handle_multi.return_value = [
        {
            'query': 'query1', 
            'results': [{'content': 'content1'}], 
            'metadata': {'verbose': False, 'cost': 0.001},
            'tokens': 100,
            'tokens_used': 100
        },
        {
            'query': 'query2', 
            'results': [{'content': 'content2'}], 
            'metadata': {'verbose': False, 'cost': 0.001},
            'tokens': 100,
            'tokens_used': 100
        }
    ]
    
    # Create a test file with queries
    query_file = tmp_path / "queries.txt"
    query_file.write_text("query1\nquery2\nquery3")
    
    result = runner.invoke(cli, ["-i", str(query_file)])
    assert result.exit_code == 0
    mock_handle_multi.assert_called_once()
    # First argument should be a list of queries from the file
    args = mock_handle_multi.call_args[0][0]
    assert len(args) == 3
    assert "query1" in args
    assert "query2" in args
    assert "query3" in args

@patch('askp.cli.search_perplexity')
def test_process_query(mock_search):
    """Test execute_query function."""
    mock_search.return_value = {
        'query': 'test', 
        'results': [{'content': 'content'}],
        'metadata': {'verbose': False, 'cost': 0.001},
        'model': 'test-model',
        'tokens': 100,
        'tokens_used': 100,
        'model_info': {
            'id': 'test-model',
            'model': 'test-model',
            'cost_per_million': 1.0,
            'reasoning': False
        }
    }
    
    result = execute_query("test query", 0, {}, MagicMock())
    assert result is not None
    mock_search.assert_called_once_with("test query", {})

@patch('askp.cli.execute_query')
def test_handle_multi_query(mock_process):
    """Test handle_multi_query function."""
    mock_result = {
        'query': 'test', 
        'results': [{'content': 'content'}],
        'metadata': {'verbose': False, 'cost': 0.001},
        'tokens': 100,
        'tokens_used': 100
    }
    mock_process.return_value = mock_result
    
    results = handle_multi_query(["query1", "query2", "query3"], {})
    assert len(results) == 3
    assert mock_process.call_count == 3

@patch('askp.cli.execute_query')
@patch('askp.cli.get_output_dir')
@patch('builtins.print')
def test_handle_multi_query_deep_research(mock_print, mock_get_output_dir, mock_process):
    """Test handle_multi_query function with deep research mode."""
    mock_result = {
        'query': 'test', 
        'results': [{'content': 'content'}],
        'metadata': {'verbose': False, 'cost': 0.001},
        'tokens': 100,
        'tokens_used': 100
    }
    mock_process.return_value = mock_result
    mock_get_output_dir.return_value = "/test/output/dir"
    
    # Reset mock_print to clear any previous calls
    mock_print.reset_mock()
    
    # Test with deep research mode enabled
    results = handle_multi_query(["query1", "query2", "query3"], {"deep": True})
    assert len(results) == 3
    assert mock_process.call_count == 3
    
    # Verify that summary output (total cost/tokens) is not printed in deep research mode
    # But we still expect some initial messages
    summary_calls = [call for call in mock_print.call_args_list if "Totals |" in str(call)]
    assert len(summary_calls) == 0
    
    # Reset mocks
    mock_print.reset_mock()
    mock_process.reset_mock()
    
    # Test with deep research mode disabled
    results = handle_multi_query(["query1", "query2", "query3"], {"deep": False})
    assert len(results) == 3
    assert mock_process.call_count == 3
    
    # Verify that summary output is printed when not in deep research mode
    summary_calls = [call for call in mock_print.call_args_list if "Totals |" in str(call)]
    assert len(summary_calls) > 0
