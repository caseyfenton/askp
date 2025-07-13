#!/usr/bin/env python3
"""
Test script for the new output formatting and debug behavior.
This script patches the API call to avoid actual API usage.
"""
import sys
from unittest.mock import patch
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.askp.cli import cli
import click
from click.testing import CliRunner

# Create a runner
runner = CliRunner()

# Patch the search_perplexity function to avoid actual API calls
def mock_search_perplexity(*args, **kwargs):
    query = args[0] if args else kwargs.get("query", "No query")
    model = kwargs.get("model", "default-model")
    print(f"\n=== MOCK API CALL ===")
    print(f"Query: {query}")
    print(f"Model: {model}")
    print(f"===================\n")
    return {
        "query": query,
        "text": f"Mock response for: {query}",
        "model": model,
        "tokens": 100,
        "cost": 0.0,
    }

@patch("src.askp.api.search_perplexity", side_effect=mock_search_perplexity)
def test_without_debug(mock_api):
    """Test without debug flag - should not show API key debug info"""
    print("\n\n=== TESTING WITHOUT DEBUG FLAG ===")
    result = runner.invoke(cli, ["What is the capital of France?", "--quiet"])
    print(result.output)
    return result

@patch("src.askp.api.search_perplexity", side_effect=mock_search_perplexity)
def test_with_debug(mock_api):
    """Test with debug flag - should show API key debug info"""
    print("\n\n=== TESTING WITH DEBUG FLAG ===")
    result = runner.invoke(cli, ["What is the capital of France?", "--debug", "--quiet"])
    print(result.output)
    return result

@patch("src.askp.api.search_perplexity", side_effect=mock_search_perplexity)
def test_model_format(mock_api):
    """Test model/temperature format - should be on one line"""
    print("\n\n=== TESTING MODEL/TEMP FORMAT ===")
    result = runner.invoke(cli, ["What is the capital of France?", "--quiet"])
    print(result.output)
    return result

@patch("src.askp.api.search_perplexity", side_effect=mock_search_perplexity)
def test_code_model_flag(mock_api):
    """Test code model with -X flag"""
    print("\n\n=== TESTING CODE MODEL (-X) ===")
    result = runner.invoke(cli, ["What is the capital of France?", "-X", "--quiet"])
    print(result.output)
    return result

if __name__ == "__main__":
    print("Testing output formatting and debug behavior...")
    test_without_debug()
    test_with_debug()
    test_model_format()
    test_code_model_flag()
    print("\nAll tests completed!")
