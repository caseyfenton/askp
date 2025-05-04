#!/usr/bin/env python3
"""
Utility functions for ASKP.
Contains functions for formatting sizes, sanitizing filenames, API key loading, model info, and path handling.
"""
import os
import re
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Union

def format_size(s: int) -> str:
    """Format byte size with appropriate unit."""
    return f"{s}B" if s < 1024 else f"{s/1024:.1f}KB" if s < 1024**2 else f"{s/(1024**2):.1f}MB"

def sanitize_filename(q: str) -> str:
    """Sanitize a query string to produce a safe filename (max 50 characters)."""
    s = "".join(c if c.isalnum() else "_" for c in q)
    return s[:50] if s.strip("_") else "query"

def load_api_key() -> str:
    """Load the Perplexity API key from environment or .env files; exits if not found."""
    # Try the environment variable first
    key = os.environ.get("PERPLEXITY_API_KEY")
    if key and key not in ["your_api_key_here", "pplx-", ""]:
        return key
    
    # Try keys from .env files - prioritizing home directory
    from pathlib import Path
    env_locations = [
        Path.cwd() / ".env",  # Current project directory first
        Path.home() / ".env",  # Home directory second
        Path.home() / ".perplexity" / ".env",  # Other common locations
        Path.home() / ".askp" / ".env"
    ]
    
    for p in env_locations:
        if p.exists():
            try:
                for line in p.read_text().splitlines():
                    if line.startswith("PERPLEXITY_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"\'' )
                        if key and key not in ["your_api_key_here", "pplx-", ""]:
                            return key
            except Exception as e:
                print(f"Warning: Error reading {p}: {e}")
    
    # If we got here, no valid key was found
    from rich import print as rprint
    from rich.panel import Panel
    
    rprint(Panel("""[bold red]ERROR: Perplexity API Key Not Found or Invalid[/bold red]

[yellow]To use ASKP, you need a valid Perplexity API key. Please follow these steps:[/yellow]

1. Visit [bold]https://www.perplexity.ai/account/api/keys[/bold] to create or retrieve your API key
2. Add your key to one of the following locations:
   - Environment variable: PERPLEXITY_API_KEY=pplx-xxxxxxxx
   - In a .env file in one of these locations:
     • ~/.env (recommended)
     • ~/.askp/.env
     • ~/.perplexity/.env

[bold]Example .env file contents:[/bold]
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

[bold]Note:[/bold] Make sure your API key is valid and not expired.
""", title="API Key Required", border_style="red"))
    exit(1)
