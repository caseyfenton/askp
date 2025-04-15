#!/usr/bin/env python3
"""File utilities for ASKP CLI."""
import os
from pathlib import Path
from typing import Tuple, List
from rich import print as rprint

def format_path(filepath: str) -> str:
    """Format a file path to use tilde notation.
    Example: /Users/username/CascadeProjects/askp/file.txt -> ~/askp/file.txt"""
    home = str(Path.home())
    if filepath.startswith(home):
        rel = filepath[len(home):]
        if '/CascadeProjects/' in filepath:
            parts = rel.split('/CascadeProjects/', 1)
            if len(parts) > 1:
                proj = parts[1].split('/', 1)
                return f"~/{proj[0]}/{proj[1]}" if len(proj)>1 else f"~/{proj[0]}"
        return "~" + rel
    return filepath

def get_file_stats(filepath: str) -> Tuple[int, int]:
    """Return (size in bytes, number of lines) for a given file."""
    if not os.path.exists(filepath): return (0, 0)
    try:
        size = os.path.getsize(filepath)
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f: 
            lines = sum(1 for _ in f)
        return (size, lines)
    except Exception as e:
        rprint(f"[yellow]Warning: Could not get stats for {filepath}: {e}[/yellow]"); return (0, 0)

def generate_cat_commands(files: List[str]) -> List[str]:
    """Generate a list of cat commands for existing file paths."""
    return [f"cat {f}" for f in files if os.path.exists(f)]
