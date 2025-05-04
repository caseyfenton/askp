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

def get_model_info(model: str) -> Dict:
    """Get information about a specific model."""
    models = {
        "sonar-small-online": {
            "name": "Sonar Small Online",
            "description": "Fast, efficient model for simple queries",
            "context_window": 4000,
            "cost_per_query": 0.0001,
            "online": True
        },
        "sonar-medium-online": {
            "name": "Sonar Medium Online",
            "description": "Balanced model for general-purpose queries",
            "context_window": 8000,
            "cost_per_query": 0.0002,
            "online": True
        },
        "sonar-large-online": {
            "name": "Sonar Large Online",
            "description": "Powerful model for complex queries",
            "context_window": 12000,
            "cost_per_query": 0.0004,
            "online": True
        },
        "mixtral-8x7b-instruct": {
            "name": "Mixtral 8x7B Instruct",
            "description": "Powerful open-source model",
            "context_window": 32768,
            "cost_per_query": 0.0006,
            "online": False
        },
        "llama-3-70b-instruct": {
            "name": "Llama-3-70B-Instruct",
            "description": "Meta's latest large language model",
            "context_window": 8192,
            "cost_per_query": 0.0008,
            "online": False
        },
        "claude-3-opus-20240229": {
            "name": "Claude 3 Opus",
            "description": "Anthropic's most powerful model",
            "context_window": 200000,
            "cost_per_query": 0.0015,
            "online": False
        },
        "claude-3-sonnet-20240229": {
            "name": "Claude 3 Sonnet",
            "description": "Anthropic's balanced model",
            "context_window": 180000,
            "cost_per_query": 0.0008,
            "online": False
        },
        "claude-3-haiku-20240307": {
            "name": "Claude 3 Haiku",
            "description": "Anthropic's fastest model",
            "context_window": 160000,
            "cost_per_query": 0.0003,
            "online": False
        },
        "gpt-4o": {
            "name": "GPT-4o",
            "description": "OpenAI's most capable model",
            "context_window": 128000,
            "cost_per_query": 0.0015,
            "online": False
        },
        "gpt-4-turbo": {
            "name": "GPT-4 Turbo",
            "description": "OpenAI's powerful model",
            "context_window": 128000,
            "cost_per_query": 0.0010,
            "online": False
        },
        "gpt-3.5-turbo": {
            "name": "GPT-3.5 Turbo",
            "description": "OpenAI's efficient model",
            "context_window": 16385,
            "cost_per_query": 0.0002,
            "online": False
        },
        "command-r": {
            "name": "Command R",
            "description": "Cohere's powerful model",
            "context_window": 128000,
            "cost_per_query": 0.0010,
            "online": False
        }
    }
    
    return models.get(model, {
        "name": model,
        "description": "Unknown model",
        "context_window": 4000,
        "cost_per_query": 0.0005,
        "online": False
    })

def get_results_dir() -> Path:
    """Get the directory for storing results."""
    home = Path.home()
    results_dir = home / "perplexity_results"
    results_dir.mkdir(exist_ok=True)
    return results_dir
