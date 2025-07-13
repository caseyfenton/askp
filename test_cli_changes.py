#!/usr/bin/env python3
"""
Test script for the CLI changes (default quick mode and comprehensive mode).
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
    print(f"Other args: {kwargs}")
    print(f"===================\n")
    return {
        "query": query,
        "text": f"Mock response for: {query}",
        "model": model,
        "tokens": 100,
        "cost": 0.0,
    }

@patch("src.askp.api.search_perplexity", side_effect=mock_search_perplexity)
def test_default_mode(mock_api):
    """Test the default mode (combined queries)"""
    print("\n\n=== TESTING DEFAULT MODE (COMBINED) ===")
    result = runner.invoke(cli, ["Query1", "Query2", "Query3", "--quiet"])
    print(result.output)
    return result

@patch("src.askp.api.search_perplexity", side_effect=mock_search_perplexity)
def test_comprehensive_mode(mock_api):
    """Test comprehensive mode with -c flag"""
    print("\n\n=== TESTING COMPREHENSIVE MODE (-c) ===")
    result = runner.invoke(cli, ["Query1", "Query2", "Query3", "-c", "--quiet"])
    print(result.output)
    return result

@patch("src.askp.api.search_perplexity", side_effect=mock_search_perplexity)
def test_comprehensive_mode_long(mock_api):
    """Test comprehensive mode with --comprehensive flag"""
    print("\n\n=== TESTING COMPREHENSIVE MODE (--comprehensive) ===")
    result = runner.invoke(cli, ["Query1", "Query2", "Query3", "--comprehensive", "--quiet"])
    print(result.output)
    return result

@patch("src.askp.api.search_perplexity", side_effect=mock_search_perplexity)
def test_code_model(mock_api):
    """Test code model with -X flag"""
    print("\n\n=== TESTING CODE MODEL (-X) ===")
    result = runner.invoke(cli, ["Query about Python", "-X", "--quiet"])
    print(result.output)
    return result

if __name__ == "__main__":
    test_default_mode()
    test_comprehensive_mode()
    test_comprehensive_mode_long()
    test_code_model()
    print("\nAll tests completed!")
