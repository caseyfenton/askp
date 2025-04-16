#!/usr/bin/env python3
"""
File utilities for ASKP.
Contains functions for path formatting, file stats, and generating cat commands.
"""
import os
from pathlib import Path
from typing import Tuple, List, Dict
from rich import print as rprint

def format_path(filepath: str) -> str:
    """Format a file path to use tilde notation.

    Args:
        filepath: The file path to format

    Returns:
        The formatted file path, relative to the current working directory if possible
    """
    # First try to make the path relative to the current directory
    try:
        cwd = os.getcwd()
        rel_path = os.path.relpath(filepath, cwd)
        # If the path doesn't go up directories, return the relative path
        if not rel_path.startswith('..'):
            return rel_path
    except:
        pass  # Fall back to other methods if relative path failed
    
    # Only use tilde if we couldn't make a clean relative path
    # This prevents confusion when paths are in other user directories
    home_dir = os.path.expanduser("~")
    if filepath.startswith(home_dir):
        return filepath.replace(home_dir, "~")
    
    return filepath

def get_file_stats(filepath: str) -> Tuple[int, int]:
    """Get file statistics (size in bytes and line count)."""
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

def generate_cat_commands(results: List[dict], output_dir: str = None) -> Dict[str, List[str]]:
    """
    Generate cat commands for viewing result files.
    
    Args:
        results: List of query result dictionaries
        output_dir: Output directory where results are saved
        
    Returns:
        Dictionary of command groups, each containing a list of cat commands
    """
    if not results:
        return {}
    
    cmd_groups = {"View": [], "JSON": [], "All": []}
    max_lines = 200  # Windsurf context window line limit
    
    # Check if results have saved_path metadata
    for i, res in enumerate(results):
        if not res:
            continue
            
        saved_path = res.get("metadata", {}).get("saved_path", "")
        if saved_path and os.path.exists(saved_path):
            rel_path = format_path(saved_path)
            # Get file size and line count
            _, line_count = get_file_stats(saved_path)
            
            # If file is longer than max_lines, use head command to limit output
            if line_count > max_lines:
                cmd_groups["View"].append(f"head -n {max_lines} {rel_path}")
            else:
                cmd_groups["View"].append(f"cat {rel_path}")
            
            # Check for JSON version
            json_path = saved_path.replace(".md", ".json")
            if os.path.exists(json_path):
                rel_json_path = format_path(json_path)
                _, json_line_count = get_file_stats(json_path)
                
                # If JSON file is longer than max_lines, use head command
                if json_line_count > max_lines:
                    cmd_groups["JSON"].append(f"head -n {max_lines} {rel_json_path}")
                else:
                    cmd_groups["JSON"].append(f"cat {rel_json_path}")
    
    # Add a command for the combined file if it exists
    if output_dir:
        combined_files = [f for f in os.listdir(output_dir) if f.startswith("combined_results_") and f.endswith(".md")]
        for cf in combined_files:
            combined_path = os.path.join(output_dir, cf)
            rel_combined = format_path(combined_path)
            _, combined_line_count = get_file_stats(combined_path)
            
            # If combined file is longer than max_lines, use head command
            if combined_line_count > max_lines:
                cmd_groups["All"].append(f"head -n {max_lines} {rel_combined}")
            else:
                cmd_groups["All"].append(f"cat {rel_combined}")
    
    return cmd_groups