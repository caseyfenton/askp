#!/usr/bin/env python3
"""Tests for utility functions."""
import pytest
from askp.utils import detect_model

def test_detect_model():
    """Test model detection from content and filenames."""
    assert detect_model("using sonar-pro model") == "sonar-pro"
    assert detect_model("pplx-api query") == "pplx"
    assert detect_model("gpt4-omni test") == "gpt4"
    assert detect_model("claude-3.5-sonnet response") == "claude"
    assert detect_model("no model specified") == "sonar"
    assert detect_model("query", "sonar-pro_test.txt") == "sonar-pro"
    assert detect_model("query", "pplx-api_result.md") == "pplx"
    assert detect_model("model: sonar-pro") == "sonar-pro"
    assert detect_model("model: pplx-api") == "pplx"