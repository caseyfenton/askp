#!/usr/bin/env python3
"""
Fix for output directory handling in askp.
Simply ensures perplexity_results directory exists in the current working directory.
"""
from pathlib import Path

def ensure_output_dir():
    """Create the perplexity_results directory in the current working directory."""
    output_dir = Path.cwd() / "perplexity_results"
    output_dir.mkdir(exist_ok=True)
    print(f"Output directory created at: {output_dir}")
    return output_dir

if __name__ == "__main__":
    ensure_output_dir()
