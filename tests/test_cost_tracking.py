"""Tests for cost tracking functionality."""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
import pytest
from askp.cost_tracking import (
    format_cost,
    format_date,
    format_date_range,
    estimate_token_count,
    detect_model,
    get_project_from_path
)

@pytest.fixture
def temp_cost_log(tmp_path):
    """Create a temporary cost log file."""
    log_file = tmp_path / "costs.jsonl"
    entries = [
        {
            "timestamp": "2025-02-24T10:00:00",
            "model": "sonar",
            "token_count": 1000,
            "cost": 0.001,
            "project": "test-project"
        },
        {
            "timestamp": "2025-02-24T11:00:00",
            "model": "sonar-pro",
            "token_count": 2000,
            "cost": 0.002,
            "project": "test-project"
        }
    ]
    with open(log_file, "w") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return log_file

def test_format_cost():
    """Test cost formatting."""
    assert format_cost(1.23456) == "$1.23"
    assert format_cost(0.00123) == "$0.0012"
    assert format_cost(0.1) == "$0.10"

def test_format_date():
    """Test date formatting."""
    date = datetime(2025, 2, 24, 10, 0, 0)
    assert format_date(date) == "Feb 24 2025"

def test_format_date_range():
    """Test date range formatting."""
    start = datetime(2025, 2, 24)
    end = datetime(2025, 2, 25)
    assert format_date_range(start, end) == "Feb 24 - 25 2025 (2D)"

def test_estimate_token_count():
    """Test token count estimation."""
    assert estimate_token_count("Hello world") > 0
    code = "def test(): return x + y"
    assert estimate_token_count(code) > len(code) / 4

def test_detect_model():
    """Test model detection."""
    assert detect_model("using sonar model", "test.txt") == "sonar"
    assert detect_model("sonar-pro query", "test.txt") == "sonar-pro"

def test_get_project_from_path():
    """Test project detection from paths."""
    tmp_dir = Path("/tmp/test-project")
    tmp_dir.mkdir(parents=True, exist_ok=True)
    wd_file = tmp_dir / ".working_directory"
    wd_file.write_text("test-project")
    assert get_project_from_path(str(tmp_dir)) == "test-project"
    assert get_project_from_path("/projects/my-project/src") == "my-project"
    assert get_project_from_path("/cascadeprojects/test/src") == "test"
    assert get_project_from_path("/tmp/random/path") is None