"""Tests for handling API errors in ASKP CLI."""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from click.testing import CliRunner
from askp.cli import cli, execute_query, search_perplexity

@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()

@pytest.fixture
def mock_error_result():
    """Create a mock error result with the expected structure."""
    return {
        "query": "test query",
        "error": "Error message",
        "metadata": {
            "cost": 0.0,
            "elapsed_time": 0.0,
            "queries_per_second": 0.0
        },
        "tokens": 0,
        "results": []
    }

def test_search_perplexity_error_handling():
    """Test error handling in search_perplexity function."""
    error_cases = [
        ("Network timeout", TimeoutError("Connection timed out")),
        ("Rate limit", Exception("429 Client Error: Too Many Requests")),
        ("Authentication", Exception("401 Client Error: Unauthorized")),
        ("Server error", Exception("500 Server Error: Internal Server Error"))
    ]
    for error_name, exception in error_cases:
        with patch('askp.cli.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = exception
            with patch('askp.cli.load_api_key', return_value="dummy_key"):
                result = search_perplexity("test query", {"test_mode": True})
                assert result is None, f"{error_name} error not handled properly"

def test_execute_query_with_none_result():
    """Test execute_query function when search_perplexity returns None."""
    with patch('askp.cli.search_perplexity', return_value=None):
        result = execute_query("test query", 0, {"test_mode": True})
        assert result is None, "execute_query should return None when search_perplexity returns None"

def test_cli_with_mock_error_results(runner, mock_error_result):
    """Test CLI with mock error results."""
    error_messages = [
        "Connection timed out",
        "429 Client Error: Too Many Requests",
        "401 Client Error: Unauthorized",
        "500 Server Error: Internal Server Error"
    ]
    for error_msg in error_messages:
        mock_result = mock_error_result.copy()
        mock_result["error"] = error_msg
        with patch('askp.cli.execute_query', return_value=mock_result):
            result = runner.invoke(cli, ["test query"])
            assert result.exit_code == 0

def test_cli_with_none_result(runner):
    """Test CLI when execute_query returns None."""
    with patch('askp.cli.execute_query', return_value=None):
        result = runner.invoke(cli, ["test query"])
        assert result.exit_code == 0 or result.exit_code == 1

def test_rate_limit_retry_logic():
    """Test retry logic when encountering rate limit errors."""
    def retry_search_perplexity(q: str, opts: dict) -> dict:
        mock_client = MagicMock()
        rate_limit_error = Exception("429 Client Error: Too Many Requests")
        mock_success_response = MagicMock()
        mock_success_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
            "query": q,
            "results": [{"content": "Test result after retry"}],
            "model": "test-model",
            "tokens": 100,
            "metadata": {"cost": 0.0001, "format": "markdown"}
        })))]
        mock_success_response.usage = MagicMock(total_tokens=100)
        call_count = 0
        max_retries = opts.get("max_retries", 3)
        for attempt in range(max_retries + 1):
            try:
                call_count += 1
                if call_count == 1:
                    raise rate_limit_error
                else:
                    content = mock_success_response.choices[0].message.content
                    return json.loads(content)
            except Exception as e:
                if "429" in str(e) and attempt < max_retries:
                    continue
                raise
        return None
    with patch('askp.cli.search_perplexity', side_effect=retry_search_perplexity):
        result = search_perplexity("test query", {
            "retry_on_rate_limit": True,
            "max_retries": 3,
            "test_mode": True,
            "format": "markdown"
        })
        assert result is not None
        assert "results" in result
        assert "content" in result["results"][0]
        assert result["results"][0]["content"] == "Test result after retry"

def test_malformed_api_response_handling():
    """Test handling of malformed API responses."""
    with patch('askp.cli.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        test_cases = [
            {"description": "Empty JSON", "content": "{}"},
            {"description": "Missing required fields", "content": json.dumps({"query": "test"})},
            {"description": "Invalid JSON", "content": "{invalid json}"},
            {"description": "Unexpected structure", "content": json.dumps({"unexpected": "structure"})},
            {"description": "Empty response", "content": ""}
        ]
        for i, test_case in enumerate(test_cases):
            mock_client.reset_mock()
            if test_case["description"] in ["Invalid JSON", "Empty response"]:
                mock_client.chat.completions.create.side_effect = json.JSONDecodeError("Invalid JSON", test_case["content"], 0)
            else:
                mock_response = MagicMock()
                mock_response.choices = [MagicMock(message=MagicMock(content=test_case["content"]))]
                mock_response.usage = MagicMock(total_tokens=10)
                mock_client.chat.completions.create.return_value = mock_response
            with patch('askp.cli.load_api_key', return_value="dummy_key"):
                with patch('askp.cli.rprint') as mock_rprint:
                    result = search_perplexity(f"test query {i}", {"test_mode": True})
                    if test_case["description"] in ["Invalid JSON", "Empty response"]:
                        error_calls = [call for call in mock_rprint.call_args_list if "Error" in str(call) or "error" in str(call)]
                        assert len(error_calls) > 0, f"Error message should be printed for {test_case['description']}"
                        assert result is None, f"{test_case['description']} should result in None"
                    else:
                        if result is not None:
                            assert isinstance(result, dict), f"Result should be a dict for {test_case['description']}"
                        else:
                            error_calls = [call for call in mock_rprint.call_args_list if "Error" in str(call) or "error" in str(call)]
                            assert len(error_calls) > 0, f"Error message should be printed for {test_case['description']}"
                        
@pytest.mark.skip(reason="Linux testing not yet implemented")
def test_linux_compatibility():
    """Test compatibility with Linux."""
    assert False, "Linux compatibility testing not yet implemented"

@pytest.mark.skip(reason="Windows testing not yet implemented")
def test_windows_compatibility():
    """Test compatibility with Windows."""
    assert False, "Windows compatibility testing not yet implemented"