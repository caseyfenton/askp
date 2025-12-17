#!/usr/bin/env python3
"""
Utility functions for ASKP.
Contains functions for formatting sizes, sanitizing filenames, API key loading, model info, and path handling.
"""
import os
import re
import json
import uuid
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Union, Any, List

from rich import print as rprint
from rich.panel import Panel

def format_size(s: int) -> str:
    """Format byte size with appropriate unit."""
    return f"{s}B" if s < 1024 else f"{s/1024:.1f}KB" if s < 1024**2 else f"{s/(1024**2):.1f}MB"

def sanitize_filename(q: str) -> str:
    """Sanitize a query string to produce a safe filename (max 50 characters)."""
    s = "".join(c if c.isalnum() else "_" for c in q)
    return s[:50] if s.strip("_") else "query"

def load_api_key(debug=False) -> str:
    """Load the Perplexity API key from environment or .env files; exits if not found."""
    # Try the environment variable first
    debug_info = ["API Key Loading Debug Info:"] if debug else []
    
    key = os.environ.get("PERPLEXITY_API_KEY")
    if debug:
        debug_info.append(f"Environment variable PERPLEXITY_API_KEY exists: {key is not None}")
    
    if key:
        # Strip any quotes from environment variable
        key = key.strip().strip('"').strip("'").strip()
        if debug:
            debug_info.append(f"Key from env: {key[:10]}...{key[-5:]}")
    
    if key and key not in ["your_api_key_here", "pplx-", ""]:
        if debug:
            debug_info.append("Using API key from environment variable")
            print("\n".join(debug_info))
        return key
    
    # Try keys from .env files - prioritizing home directory
    from pathlib import Path
    
    # Get home directory with more robust handling for Windows
    try:
        home_dir = Path.home()
        if debug:
            debug_info.append(f"Home directory: {home_dir}")
    except Exception as e:
        if debug:
            debug_info.append(f"Error getting home directory: {e}")
        home_dir = Path(os.path.expanduser("~"))
        if debug:
            debug_info.append(f"Fallback home directory: {home_dir}")
    
    # Define .env file locations with better Windows compatibility
    env_locations = [
        Path.cwd() / ".env",  # Current project directory first
        home_dir / ".env",  # Home directory second
        home_dir / ".perplexity" / ".env",  # Other common locations
        home_dir / ".askp" / ".env"
    ]
    
    if debug:
        debug_info.append(f"Checking .env files at: {', '.join(str(p) for p in env_locations)}")
    
    for p in env_locations:
        if debug:
            debug_info.append(f"Checking {p} (exists: {p.exists()})")
        if p.exists():
            try:
                env_content = p.read_text(encoding="utf-8")
                if debug:
                    debug_info.append(f"Successfully read {p}")
                
                for line in env_content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                        
                    if line.startswith("PERPLEXITY_API_KEY="):
                        key = line.split("=", 1)[1].strip()
                        # Strip any quotes
                        key = key.strip('"').strip("'").strip()
                        if debug:
                            debug_info.append(f"Found API key entry in {p}")
                        
                        if key and key not in ["your_api_key_here", "pplx-", ""]:
                            if debug:
                                debug_info.append(f"Using valid API key from {p}")
                                debug_info.append(f"Key from file: {key[:10]}...{key[-5:]}")
                                print("\n".join(debug_info))
                            return key
            except Exception as e:
                if debug:
                    debug_info.append(f"Error reading {p}: {e}")
    
    # If no API key was found, display an error message and exit
    if debug:
        print("\n".join(debug_info))
    
    # If no API key was found, display an error message
    if not key:
        file_locations = "     * ~/.env (recommended)\n     * ~/.askp/.env\n     * ~/.perplexity/.env"
        rprint(Panel(f"""[bold red]ERROR: Perplexity API Key Not Found or Invalid[/bold red]

[yellow]To use ASKP, you need a valid Perplexity API key. Please follow these steps:[/yellow]

1. Visit [bold]https://www.perplexity.ai/account/api/keys[/bold] to create or retrieve your API key
2. Add your key to one of the following locations:
{file_locations}
3. Format should be: PERPLEXITY_API_KEY=your_key_here

[bold]Note:[/bold] Make sure your API key is valid and not expired.
[dim]For debugging help, run with ASKP_DEBUG=1 environment variable.[/dim]
""", title="API Key Required", border_style="red"))
        exit(1)

def get_model_info(model: str) -> Dict:
    """Get information about a model including cost and display name."""
    model = normalize_model_name(model)
    
    model_info = {
        "model": model,
        "cost_per_million": 1.0,  # Default cost
        "display_name": model,
    }
    
    # Map models to their display names and costs
    if model == "sonar-reasoning":
        model_info["display_name"] = "sonar-reasoning"
        model_info["cost_per_million"] = 1.0
    elif model == "sonar-reasoning-pro":
        model_info["display_name"] = "sonar-reasoning-pro"
        model_info["cost_per_million"] = 2.0
    elif model == "sonar":
        model_info["display_name"] = "sonar"
        model_info["cost_per_million"] = 0.5
    elif model == "sonar-pro":
        model_info["display_name"] = "sonar-pro"
        model_info["cost_per_million"] = 1.5
    elif model == "sonar-deep-research":
        model_info["display_name"] = "sonar-deep-research"
        model_info["cost_per_million"] = 8.0
    elif "llama" in model:
        model_info["display_name"] = "llama-3.1-sonar (code-optimized)"
        model_info["cost_per_million"] = 5.0
    
    return model_info

def normalize_model_name(model: Union[str, dict]) -> str:
    """Normalize model name to match Perplexity API format."""
    if not model:
        return "sonar-pro"
        
    # Handle case where model is a dictionary (happens with newer OpenAI client)
    if isinstance(model, dict) and "model" in model:
        model = model["model"]
    elif isinstance(model, dict):
        # If it's a dict but doesn't have a 'model' key, use default
        return "sonar-pro"
        
    model = model.lower().replace("-", "").replace(" ", "")
    
    # Map aliases to full model names
    mappings = {
        # Legacy Sonar models
        "sonarpro": "sonar-pro", 
        "sonar": "sonar", 
        "sonarreasoning": "sonar-reasoning",
        "sonarreasoningpro": "sonar-reasoning-pro",
        "sonardeepresearch": "sonar-deep-research",
        
        # Llama 3.1 Sonar Models 
        "llama31sonarsm": "llama-3.1-sonar-small-128k-online",
        "llama31sonarlg": "llama-3.1-sonar-large-128k-online",
        "llama31sonarsmonline": "llama-3.1-sonar-small-128k-online",
        "llama31sonarlgonline": "llama-3.1-sonar-large-128k-online",
        "llama31sonarsmchat": "llama-3.1-sonar-small-128k-chat",
        "llama31sonarlgchat": "llama-3.1-sonar-large-128k-chat",
        
        # Llama 3.1 Instruct Models
        "llama318b": "llama-3.1-8b-instruct",
        "llama3170b": "llama-3.1-70b-instruct", 
        "llama318binstruct": "llama-3.1-8b-instruct",
        "llama3170binstruct": "llama-3.1-70b-instruct",
        
        # PPLX models
        "mixtral": "mixtral-8x7b-instruct",
        "pplx7b": "pplx-7b-online",
        "pplx70b": "pplx-70b-online",
        "pplx7bchat": "pplx-7b-chat",
        "pplx70bchat": "pplx-70b-chat",
        
        # Offline model
        "r1": "r1-1776"
    }
    
    return mappings.get(model, model)

def detect_model(response_data: Union[dict, str], filename: str = None) -> str:
    """Detect which model was used based on response data or filename."""
    # If we have a filename with model info, use that
    if filename:
        model_indicators = {
            "sonar-pro": ["sonarpro", "sonar_pro"],
            "sonar": ["sonar"],  
            "sonar-reasoning": ["sonarreasoning", "sonar_reasoning"],
            "sonar-reasoning-pro": ["sonarreasoningpro", "sonar_reasoning_pro"],
            "llama-3.1-8b-instruct": ["llama318b", "llama31_8b"],
            "llama-3.1-70b-instruct": ["llama3170b", "llama31_70b"],
            "mixtral-8x7b-instruct": ["mixtral"],
            "pplx-7b-online": ["pplx7b"],
            "pplx-70b-online": ["pplx70b"],
            "r1-1776": ["r1"]
        }
        
        # Check if any model indicators are in the filename
        for model, indicators in model_indicators.items():
            for indicator in indicators:
                if indicator.lower() in filename.lower():
                    return model
    
    # Try to get the model from the response data metadata
    if isinstance(response_data, dict):
        if "model" in response_data:
            return response_data["model"]
        if "metadata" in response_data:
            if isinstance(response_data["metadata"], dict):
                if "model" in response_data["metadata"]:
                    return response_data["metadata"]["model"]
    
    # Default to sonar-reasoning if we can't detect
    return "sonar-reasoning"

def estimate_cost(response_data: Union[dict, str], model: str = None) -> float:
    """Estimate the cost of a query based on response data and model."""
    # Default cost if we can't determine
    default_cost = 0.005  # $0.005 per query
    
    # Determine the model if not provided
    if model is None:
        model = detect_model(response_data)
        
    # Get model info including cost
    model_info = get_model_info(model)
    
    # Try to extract token count from the response
    token_count = 0
    
    if isinstance(response_data, dict):
        # First try to get the token count directly
        if "tokens" in response_data and isinstance(response_data["tokens"], int):
            token_count = response_data["tokens"]
        # Otherwise try to get it from the metadata
        elif "metadata" in response_data and isinstance(response_data["metadata"], dict):
            metadata = response_data["metadata"]
            if "usage" in metadata and isinstance(metadata["usage"], dict):
                usage = metadata["usage"]
                if "total_tokens" in usage and isinstance(usage["total_tokens"], int):
                    token_count = usage["total_tokens"]
        
        if token_count > 0:
            # Calculate cost based on tokens and model rate
            return (token_count / 1000000) * model_info["cost_per_million"]
    
    # Return default cost if we couldn't calculate
    return default_cost

def get_results_dir(output_dir: str = None) -> Path:
    """
    Determine the best directory for storing results.
    
    Args:
        output_dir: Optional user-specified output directory
        
    Returns:
        Path object for the results directory
    """
    # If user specified an output directory, try to use that
    if output_dir:
        d = Path(output_dir)
        d.mkdir(exist_ok=True, parents=True)
        return d
        
    # Otherwise, try several locations in order of preference
    d = None
    
    # Try to find a suitable directory
    if not d:
        # 1. Try ~/.perplexity directory
        try:
            home_dir = Path.home()
            d = home_dir / ".perplexity"
            d.mkdir(exist_ok=True)
            if os.access(d, os.W_OK):
                return d
        except (PermissionError, OSError):
            pass
            
    if not d:
        # 2. Try ~/.askp directory
        try:
            home_dir = Path.home()
            d = home_dir / ".askp" 
            d.mkdir(exist_ok=True)
            if os.access(d, os.W_OK):
                return d
        except (PermissionError, OSError):
            pass
    
    if not d:
        # 3. Try ./perplexity_results directory (in current dir)
        try:
            d = Path.cwd() / "perplexity_results"
            d.mkdir(exist_ok=True)
            if os.access(d, os.W_OK):
                return d
        except (PermissionError, OSError):
            pass
            
    if not d:        
        # 4. Try ~/perplexity_results directory
        try:
            home_dir = Path.home()
            d = home_dir / "perplexity_results" 
            d.mkdir(exist_ok=True)
            return d
        except (PermissionError, OSError):
            pass
            
        # 5. Last resort: use system temp directory
        temp_dir = Path(tempfile.gettempdir())
        d = temp_dir / "perplexity_results"
        
    # Ensure the directory exists
    d.mkdir(exist_ok=True)
    return d

def generate_combined_filename(queries: list, opts: dict = None) -> str:
    """
    Generate a descriptive filename for combined results.
    
    Args:
        queries: List of query strings
        opts: Optional dictionary with extra options
    
    Returns:
        A descriptive filename with extension
    """
    if not opts:
        opts = {}
        
    # Check if a custom filename is provided
    custom_name = opts.get("output") 
    file_ext = ".md"  # Default extension
    
    # Apply code formatting if needed
    if opts.get("code"):
        file_ext = ".py" if not custom_name or "." not in custom_name else ""
        
    if custom_name:
        # Use the provided filename
        base = custom_name
        # Add extension if needed
        if "." not in base:
            base_name = base.rstrip(".")
            return f"{base_name}{file_ext}"
        return base
    
    # Use timestamp for the filename for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    
    # Generate descriptive names based on queries
    if len(queries) == 1:
        # For a single query, use a portion of the query text
        clean = re.sub(r'[^\w\s-]', '', queries[0]).strip().replace(" ", "_")[:40]
        return f"{clean}_{timestamp}{file_ext}"
    
    if len(queries) > 1:
        # For multiple queries, include the count and first query keywords
        count = len(queries)
        sample_query = queries[0]
        words = []
        parts = sample_query.split()[:3]  # Take first 3 words of first query
        for w in parts:
            w = re.sub(r'[^\w\s-]', '', w)
            if w not in ['what','is','the','a','an','in','of','to','for','and','or','capital'] and w not in words:
                words.append(w)
        if words:
            query_hint = "_".join(words)[:20]
            return f"queries_{count}_{query_hint}_{timestamp}{file_ext}"
    # Fallback with clear count indication
    return f"queries_{len(queries)}_{timestamp}{file_ext}"

def generate_unique_id(id_type="file") -> str:
    """Generate a unique ID for a file or session."""
    return str(uuid.uuid4()) if id_type=="session" else datetime.now().strftime("%Y%m%d_%H%M%S")

def format_path(path: str) -> str:
    """Format a path to be relative to the current directory if possible."""
    try:
        cwd = os.getcwd()
        return path[len(cwd)+1:] if path.startswith(cwd) else path
    except (OSError, ValueError):
        return path

# Always use a local 'perplexity_results' directory in the current folder
def get_default_output_dir() -> Path:
    """
    Get the default output directory.
    Tries to create perplexity_results in the current directory.
    If that fails due to permissions, it falls back to a directory in the users home folder.
    """
    try:
        # Try to create in the current working directory first
        local_results = Path.cwd() / "perplexity_results"
        local_results.mkdir(parents=True, exist_ok=True)
        # Test writability by creating and deleting a temporary file
        test_file = local_results / ".writable_test"
        test_file.touch()
        test_file.unlink()
        return local_results
    except (OSError, PermissionError):
        # If CWD is not writable (e.g., root '/'), fall back to a user-specific cache directory
        home_results = Path.home() / ".cache" / "askp" / "results"
        home_results.mkdir(parents=True, exist_ok=True)
        return home_results

DEFAULT_OUTPUT_DIR = get_default_output_dir()

def get_output_dir(output_dir: Union[str, Path, None] = None) -> Path:
    """Determines the output directory for saving results.

    Args:
        output_dir: Optional path to a specific output directory.
                      If None, uses DEFAULT_OUTPUT_DIR.

    Returns:
        The resolved Path object for the output directory.

    Raises:
        TypeError: If the provided output_dir is not a str or Path.
        FileNotFoundError: If the resolved directory does not exist and cannot be created.
    """
    if output_dir:
        if isinstance(output_dir, str):
            resolved_dir = Path(output_dir).resolve()
        elif isinstance(output_dir, Path):
            resolved_dir = output_dir.resolve()
        else:
            # Should ideally raise a more specific error or log a warning
            # For now, falling back to default, but this indicates incorrect usage.
            print(f"Warning: Invalid type for output_dir '{type(output_dir)}'. Using default.") # Consider logging
            resolved_dir = DEFAULT_OUTPUT_DIR
    else:
        resolved_dir = DEFAULT_OUTPUT_DIR

    try:
        resolved_dir.mkdir(parents=True, exist_ok=True)
        return resolved_dir
    except OSError as e:
        # Handle potential permission errors or other OS issues during directory creation
        raise FileNotFoundError(f"Could not create or access output directory: {resolved_dir}. Error: {e}")
