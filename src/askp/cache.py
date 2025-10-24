"""Cache integration module for askp using sema semantic search."""

import subprocess
import json
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import click

SIMILARITY_THRESHOLD = 0.75
AUTO_USE_THRESHOLD = 0.85
SEMA_TIMEOUT = 5  # seconds


def get_cache_age(file_path: Path) -> str:
    """Get human-readable age of a file.

    Args:
        file_path: Path to the file

    Returns:
        Human-readable age string like "2 hours ago" or "3 days ago"
    """
    try:
        mtime = file_path.stat().st_mtime
        age_seconds = datetime.now().timestamp() - mtime

        # Convert to appropriate units
        if age_seconds < 3600:  # Less than 1 hour
            minutes = int(age_seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif age_seconds < 86400:  # Less than 1 day
            hours = int(age_seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(age_seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
    except Exception:
        return "unknown age"


def check_sema_cache(query: str) -> Optional[list[dict]]:
    """Check sema cache for semantically similar queries.

    Args:
        query: The search query to look up

    Returns:
        List of results with keys: path, score, age (top 5, score >= 0.75)
        None if no results, sema not installed, or error occurs
    """
    try:
        # Run sema with timeout
        result = subprocess.run(
            ["sema", "--raw", query],
            capture_output=True,
            text=True,
            timeout=SEMA_TIMEOUT
        )

        if result.returncode != 0:
            return None

        # Parse JSON output
        try:
            raw_results = json.loads(result.stdout)
        except json.JSONDecodeError:
            return None

        # Filter by score threshold and transform results
        filtered_results = []
        for item in raw_results:
            score = item.get("score", 0)
            if score >= SIMILARITY_THRESHOLD:
                path = Path(item.get("path", ""))
                filtered_results.append({
                    "path": str(path),
                    "score": score,
                    "age": get_cache_age(path) if path.exists() else "unknown"
                })

        # Sort by score descending and return top 5
        filtered_results.sort(key=lambda x: x["score"], reverse=True)
        return filtered_results[:5] if filtered_results else None

    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        # sema not installed
        return None
    except Exception:
        return None


def format_cache_results(results: list[dict]) -> str:
    """Format cache results for display.

    Args:
        results: List of cache result dictionaries

    Returns:
        Formatted string for display
    """
    if not results:
        return ""

    lines = [f"🎯 Found {len(results)} cached result{'s' if len(results) != 1 else ''}:"]

    for i, result in enumerate(results, 1):
        filename = Path(result["path"]).name
        score = result["score"]
        age = result["age"]
        lines.append(f"  {i}. {filename} (score: {score:.0%}, age: {age})")

    lines.append("\n💡 Use --no-cache to bypass cache and make a fresh API call")

    return "\n".join(lines)


def should_use_cache(results: list[dict], no_cache: bool) -> tuple[bool, str]:
    """Determine whether to use cached results.

    Args:
        results: List of cache results
        no_cache: Whether cache is explicitly disabled

    Returns:
        Tuple of (should_use: bool, reason: str)
    """
    if no_cache:
        return (False, "Cache bypassed by --no-cache flag")

    if not results:
        return (False, "No cache results available")

    best_score = results[0]["score"]

    if best_score >= AUTO_USE_THRESHOLD:
        return (True, f"Auto-using high confidence cache (score: {best_score:.0%})")

    if best_score >= SIMILARITY_THRESHOLD:
        # Check if we're in a non-interactive terminal
        if not sys.stdin.isatty():
            # Non-interactive mode (cron, automation, etc.)
            # Auto-use cache for good matches (>=0.80), skip for lower scores
            if best_score >= 0.80:
                return (True, f"Auto-using cache in non-interactive mode (score: {best_score:.0%})")
            else:
                return (False, f"Score too low for auto-use in non-interactive mode ({best_score:.0%})")

        # Interactive mode - show results and prompt user
        click.echo(format_cache_results(results))
        click.echo()

        try:
            use_cache = click.confirm(
                f"Use cached result (best match: {best_score:.0%})?",
                default=True
            )

            if use_cache:
                return (True, "User selected cached result")
            else:
                return (False, "User declined cached result")
        except click.Abort:
            # User pressed Ctrl+C
            return (False, "User cancelled prompt")

    return (False, f"Low confidence score: {best_score:.0%}")
