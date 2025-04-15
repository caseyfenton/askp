#!/usr/bin/env python3
"""
Code-check helper for ASKP.
Contains the handle_code_check function that processes a file for code-check mode.
"""
import os, sys
from pathlib import Path
from rich import print as rprint
from askp.utils import format_size

def handle_code_check(code_file: str, query_text: list, single_mode: bool, quiet: bool) -> list:
    """
    Reads a file with a progress indicator; truncates if file exceeds MAX_CODE_SIZE;
    detects language based on file extension and returns a list of queries with the code snippet.
    """
    MAX_CODE_SIZE = 60 * 1024  # 60KB
    try:
        code_path = Path(code_file)
        file_size = code_path.stat().st_size
        from rich.console import Console
        console = Console()
        with console.status(f"Reading {code_file}...", spinner="dots"):
            with open(code_file, "r", encoding="utf-8", errors="replace") as f:
                code_content = f.read(MAX_CODE_SIZE)
                if file_size > MAX_CODE_SIZE and not quiet:
                    rprint(f"[yellow]Warning: File size ({format_size(file_size)}) exceeds limit. "
                           f"Truncating to {format_size(MAX_CODE_SIZE)} (~12K tokens).[/yellow]")
        lang = {".py": "python", ".js": "javascript", ".ts": "typescript", ".java": "java",
                ".cpp": "cpp", ".c": "c", ".rb": "ruby", ".go": "go", ".rs": "rust"}.get(code_path.suffix.lower(), "")
        code_block = f"```{lang}\n{code_content}\n```" if lang else f"```\n{code_content}\n```"
        queries = []
        if query_text:
            base = " ".join(query_text) if single_mode else None
            if base:
                queries.append(f"{base}\n\nCODE FROM {code_path.name}:\n{code_block}")
            else:
                queries.append(f"Review this code for issues, bugs, or improvements:\n\nCODE FROM {code_path.name}:\n{code_block}")
        else:
            queries.append(f"Review this code for issues, bugs, or improvements:\n\nCODE FROM {code_path.name}:\n{code_block}")
        if not quiet:
            rprint(f"[blue]Code check mode: Analyzing {code_path.name} (size: {format_size(file_size)})[/blue]")
        return queries
    except Exception as e:
        rprint(f"[red]Error reading code file {code_file}: {e}[/red]")
        sys.exit(1)