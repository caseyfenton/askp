#!/usr/bin/env python3
"""
Utility functions for ASKP.
Contains functions for formatting sizes, sanitizing filenames, API key loading, model info, and path handling.
"""
import os
import platform
import re
import json
import uuid
import sys
import tempfile
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
    debug_info = ["API Key Loading Debug Info:"]
    debug_info.append(f"OS: {os.name} / {platform.system()} {platform.release()}")
    
    key = os.environ.get("PERPLEXITY_API_KEY")
    debug_info.append(f"Environment variable PERPLEXITY_API_KEY exists: {key is not None}")
    
    if key and key not in ["your_api_key_here", "pplx-", ""]:
        debug_info.append("Using API key from environment variable")
        return key
    
    # Try keys from .env files - prioritizing home directory
    from pathlib import Path
    
    # Get home directory with more robust handling for Windows
    try:
        home_dir = Path.home()
        debug_info.append(f"Home directory: {home_dir}")
    except Exception as e:
        debug_info.append(f"Error getting home directory: {e}")
        home_dir = Path(os.path.expanduser("~"))
        debug_info.append(f"Fallback home directory: {home_dir}")
    
    # Define .env file locations with better Windows compatibility
    env_locations = [
        Path.cwd() / ".env",  # Current project directory first
        home_dir / ".env",  # Home directory second
        home_dir / ".perplexity" / ".env",  # Other common locations
        home_dir / ".askp" / ".env"
    ]
    
    # On Windows, also check AppData location
    if platform.system() == "Windows":
        appdata = os.environ.get("APPDATA")
        if appdata:
            appdata_path = Path(appdata)
            env_locations.extend([
                appdata_path / "perplexity" / ".env",
                appdata_path / "askp" / ".env"
            ])
    
    debug_info.append(f"Checking .env files at: {', '.join(str(p) for p in env_locations)}")
    
    for p in env_locations:
        debug_info.append(f"Checking {p} (exists: {p.exists()})")
        if p.exists():
            try:
                env_content = p.read_text(encoding="utf-8")
                debug_info.append(f"Successfully read {p}")
                
                for line in env_content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                        
                    if line.startswith("PERPLEXITY_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"\'' )
                        debug_info.append(f"Found API key entry in {p}")
                        
                        if key and key not in ["your_api_key_here", "pplx-", ""]:
                            debug_info.append(f"Using valid API key from {p}")
                            return key
                        else:
                            debug_info.append(f"Invalid API key format in {p}")
            except Exception as e:
                debug_info.append(f"Error reading {p}: {e}")
    
    # If we got here, no valid key was found
    from rich import print as rprint
    from rich.panel import Panel
    
    # Print debug info when in verbose mode or if DEBUG env var is set
    if os.environ.get("DEBUG") or os.environ.get("ASKP_DEBUG"):
        rprint("\n".join(debug_info))
    
    # Show different instructions based on OS
    if platform.system() == "Windows":
        env_instructions = """   - Environment variable: 
            • In PowerShell: $env:PERPLEXITY_API_KEY = "pplx-xxxxxxxx"
            • In Command Prompt: set PERPLEXITY_API_KEY=pplx-xxxxxxxx
            • Or set it permanently in System Properties > Environment Variables"""
        file_locations = r"""     • %USERPROFILE%\.env
     • %APPDATA%\askp\.env
     • %APPDATA%\perplexity\.env"""
    else:  # Unix-like
        env_instructions = "   - Environment variable: PERPLEXITY_API_KEY=pplx-xxxxxxxx"
        file_locations = """     • ~/.env (recommended)
     • ~/.askp/.env
     • ~/.perplexity/.env"""
    
    rprint(Panel(f"""[bold red]ERROR: Perplexity API Key Not Found or Invalid[/bold red]

[yellow]To use ASKP, you need a valid Perplexity API key. Please follow these steps:[/yellow]

1. Visit [bold]https://www.perplexity.ai/account/api/keys[/bold] to create or retrieve your API key
2. Add your key to one of the following locations:
{env_instructions}
   - In a .env file in one of these locations:
{file_locations}

[bold]Example .env file contents:[/bold]
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

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
        "display_name": model
    }
    
    if model == "sonar":
        model_info["display_name"] = "sonar (basic)"
        model_info["cost_per_million"] = 1.0
    elif model == "sonar-pro":
        model_info["display_name"] = "sonar-pro (EXPENSIVE)"
        model_info["cost_per_million"] = 15.0
    elif model == "sonar-reasoning":
        model_info["display_name"] = "sonar-reasoning (default)"
        model_info["cost_per_million"] = 5.0
    elif model == "sonar-reasoning-pro":
        model_info["display_name"] = "sonar-reasoning-pro (enhanced)"
        model_info["cost_per_million"] = 8.0
    elif model == "sonar-deep-research":
        model_info["display_name"] = "sonar-deep-research"
        model_info["cost_per_million"] = 8.0
    elif "llama" in model:
        model_info["display_name"] = "llama-3.1-sonar (code-optimized)"
        model_info["cost_per_million"] = 5.0
    
    return model_info

def normalize_model_name(model: Union[str, dict]) -> str:
    """Normalize model name to match Perplexity's expected format."""
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
        "prosonar": "sonar-pro", 
        "pro": "sonar-pro",
        # Handle legacy name (deprecated)
        "sonarproreasoning": "sonar-reasoning-pro",
        
        # Llama 3.1 models
        "llama31small": "llama-3.1-sonar-small-128k-online",
        "llama31large": "llama-3.1-sonar-large-128k-online",
        "llama31smallchat": "llama-3.1-sonar-small-128k-chat",
        "llama31largechat": "llama-3.1-sonar-large-128k-chat",
        "llama3170b": "llama-3.1-70b-instruct",
        "llama318b": "llama-3.1-8b-instruct",
        
        # Mixtral and PPLX models
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
            "sonar-reasoning": ["sonarreasoning", "sonar_reasoning"],
            "sonar-reasoning-pro": ["sonarreasoningpro", "sonar_reasoning_pro"],
            "sonar-deep-research": ["sonardeepresearch", "sonar_deep_research"],
            "llama-3.1-sonar-small-128k-online": ["llama31small", "llama_3_1_small"],
            "llama-3.1-sonar-large-128k-online": ["llama31large", "llama_3_1_large"],
            "mixtral-8x7b-instruct": ["mixtral", "mixtral8x7b"],
        }
        
        filename_lower = filename.lower()
        for model, indicators in model_indicators.items():
            for indicator in indicators:
                if indicator in filename_lower:
                    return model
    
    # If we have JSON response data, try to extract model info
    if isinstance(response_data, dict):
        # Check for model field in various locations
        if "model" in response_data:
            return response_data["model"]
        if "metadata" in response_data and isinstance(response_data["metadata"], dict):
            if "model" in response_data["metadata"]:
                return response_data["metadata"]["model"]
    
    # Default to sonar-reasoning if we can't detect
    return "sonar-reasoning"

def estimate_cost(response_data: Union[dict, str], model: str = None) -> float:
    """Estimate the cost of a query based on response data and model."""
    # Default cost if we can't determine
    default_cost = 0.005  # $0.005 per query
    
    # If model is not provided, try to detect it
    if not model and isinstance(response_data, dict):
        model = detect_model(response_data)
    
    # Get model info
    model_info = get_model_info(model) if model else {"cost_per_million": 5.0}
    
    # Calculate cost based on token count if available
    if isinstance(response_data, dict):
        # Check for token count in metadata
        token_count = 0
        if "metadata" in response_data and isinstance(response_data["metadata"], dict):
            metadata = response_data["metadata"]
            if "usage" in metadata and isinstance(metadata["usage"], dict):
                usage = metadata["usage"]
                if "total_tokens" in usage:
                    token_count = usage["total_tokens"]
                elif "completion_tokens" in usage and "prompt_tokens" in usage:
                    token_count = usage["completion_tokens"] + usage["prompt_tokens"]
        
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
    # If user specified a directory, use that
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
            
        # 2. Try script directory
        try:
            script_path = Path(sys.argv[0]).resolve()
            if script_path.exists() and script_path.is_file():
                script_dir = script_path.parent
                if os.access(script_dir, os.W_OK):
                    d = script_dir / "perplexity_results"
                    d.mkdir(exist_ok=True)
                    return d
        except (IndexError, PermissionError):
            pass
        
        # 3. Try current working directory
        try:
            cwd = Path.cwd()
            d = cwd / "perplexity_results"
            # Test if we can write to this directory
            d.mkdir(exist_ok=True)
            test_file = d / ".write_test"
            test_file.touch()
            test_file.unlink()
            return d
        except (PermissionError, OSError):
            pass
            
        # 4. Try user's home directory
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
        opts: Options dictionary containing format and other preferences
        
    Returns:
        Filename for combined results with appropriate extension
    """
    if opts is None:
        opts = {}
        
    # Determine file extension based on format
    format_type = opts.get("format", "markdown").lower()
    if format_type == "json":
        file_ext = ".json"
    elif format_type == "text":
        file_ext = ".txt"
    else:  # Default to markdown
        file_ext = ".md"
    
    # If output is specified, respect it but ensure correct extension
    if opts.get("output"):
        base = os.path.basename(opts["output"])
        # Replace extension if it doesn't match the requested format
        if not base.endswith(file_ext):
            base_name = os.path.splitext(base)[0]
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
    except:
        return path

# Always use a local 'perplexity_results' directory in the current folder
def get_default_output_dir() -> Path:
    """Get the default output directory: always ./perplexity_results in the current folder."""
    local_results = Path.cwd() / "perplexity_results"
    local_results.mkdir(exist_ok=True)
    return local_results

DEFAULT_OUTPUT_DIR = get_default_output_dir()

def get_output_dir(output_dir: str | Path | None = None) -> Path:
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
