#!/usr/bin/env python3
"""
BGRun integration for ASKP.
Contains notification functions for BGRun integration.
"""

import shutil
import os
import subprocess
from pathlib import Path
from typing import Optional

# Check if BGRun integration is enabled
# By default, disable BGRun for PyPI installations
ASKP_ENABLE_BGRUN = os.environ.get("ASKP_ENABLE_BGRUN", "0").lower() in ("1", "true", "yes", "on")

def is_bgrun_available() -> bool:
    """Check if bgrun is available in PATH and if integration is enabled."""
    if not ASKP_ENABLE_BGRUN:
        return False
    return shutil.which("bgrun") is not None

def get_bgrun_path() -> Optional[str]:
    """Return the path to bgrun, either from PATH or standard locations."""
    if not ASKP_ENABLE_BGRUN:
        return None
    bgrun_path = shutil.which("bgrun")
    if bgrun_path:
        return bgrun_path
    fallback_paths = ["/usr/local/bin/bgrun", "/usr/bin/bgrun"]
    for path in fallback_paths:
        p = Path(path)
        if p.exists() and os.access(path, os.X_OK):
            return path
    return None

def notify_query_completed(query: str, saved_path: str, model: str, tokens: int, cost: float) -> bool:
    """Notify BGRun about query completion."""
    if not ASKP_ENABLE_BGRUN:
        return False
    bgrun = get_bgrun_path()
    if not bgrun:
        return False
    try:
        result = subprocess.run([bgrun, "notify-query", query, saved_path, model, str(tokens), str(cost)])
        return result.returncode == 0
    except Exception:
        return False

def notify_multi_query_completed(num_queries: int, combined_file: str, tokens: int, cost: float) -> bool:
    """Notify BGRun about multi-query completion."""
    if not ASKP_ENABLE_BGRUN:
        return False
    bgrun = get_bgrun_path()
    if not bgrun:
        return False
    try:
        result = subprocess.run([bgrun, "notify-multi-query", str(num_queries), combined_file, str(tokens), str(cost)])
        return result.returncode == 0
    except Exception:
        return False

def update_askp_status_widget(query_count: int, total_cost: float, elapsed: float) -> bool:
    """Update BGRun status widget with ASKP stats."""
    if not ASKP_ENABLE_BGRUN:
        return False
    bgrun = get_bgrun_path()
    if not bgrun:
        return False
    try:
        result = subprocess.run([bgrun, "update-widget", str(query_count), str(total_cost), str(elapsed)])
        return result.returncode == 0
    except Exception:
        return False
