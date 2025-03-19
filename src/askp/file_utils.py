#!/usr/bin/env python3
"""File utilities for ASKP CLI."""
import os
from pathlib import Path
from typing import Tuple, List
from rich import print as rprint

def format_path(filepath: str) -> str:
    """Format a file path to use tilde notation.
    
    Replaces the user's home directory with a tilde (~) followed by the project path.
    Example: /Users/username/CascadeProjects/askp/file.txt -> ~/askp/file.txt
    
    Args:
        filepath: The full file path
        
    Returns:
        Formatted path with tilde notation
    """
    home = str(Path.home())
    if filepath.startswith(home):
        # Extract the project name from the path after CascadeProjects
        rel_path = filepath[len(home):]
        if '/CascadeProjects/' in filepath:
            parts = rel_path.split('/CascadeProjects/', 1)
            if len(parts) > 1:
                project_parts = parts[1].split('/', 1)
                if len(project_parts) > 1:
                    return f"~/{project_parts[0]}/{project_parts[1]}"
                return f"~/{project_parts[0]}"
        return "~" + rel_path
    return filepath

def get_file_stats(filepath: str) -> Tuple[int, int]:
    """Get file statistics (size in bytes and line count).
    
    Args:
        filepath: Path to the file
        
    Returns:
        Tuple of (size_in_bytes, line_count)
    """
    if not os.path.exists(filepath):
        return (0, 0)
    try:
        size = os.path.getsize(filepath)
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            lines = sum(1 for _ in f)
        return (size, lines)
    except Exception as e:
        rprint(f"[yellow]Warning: Could not get stats for {filepath}: {e}[/yellow]")
        return (0, 0)

def generate_cat_commands(files: List[str]) -> List[str]:
    """Generate cat commands for a list of files.
    
    Args:
        files: List of file paths
        
    Returns:
        List of cat commands
    """
    commands = []
    for f in files:
        if os.path.exists(f):
            commands.append(f"cat {f}")
    return commands
