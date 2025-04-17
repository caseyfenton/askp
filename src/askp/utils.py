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
from typing import Optional

def format_size(s: int) -> str:
    """Format byte size with appropriate unit."""
    return f"{s}B" if s < 1024 else f"{s/1024:.1f}KB" if s < 1024**2 else f"{s/(1024**2):.1f}MB"

def sanitize_filename(q: str) -> str:
    """Sanitize a query string to produce a safe filename (max 50 characters)."""
    s = "".join(c if c.isalnum() else "_" for c in q)
    return s[:50] if s.strip("_") else "query"

def load_api_key() -> str:
    """Load the Perplexity API key from environment or .env files; exits if not found."""
    key = os.environ.get("PERPLEXITY_API_KEY")
    if key:
        return key
    from pathlib import Path
    for p in [Path.home() / ".env", Path.home() / ".perplexity" / ".env", Path.home() / ".askp" / ".env"]:
        if p.exists():
            try:
                for line in p.read_text().splitlines():
                    if line.startswith("PERPLEXITY_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"\'' )
            except Exception as e:
                print(f"Warning: Error reading {p}: {e}")
    print("Error: Could not find Perplexity API key.")
    exit(1)

def get_model_info(model: str) -> str:
    """Get information about a model for display purposes."""
    model = normalize_model_name(model)
    
    if model == "sonar":
        return "sonar (basic)"
    elif model == "sonar-pro":
        return "sonar-pro (EXPENSIVE)"
    elif model == "sonar-reasoning":
        return "sonar-reasoning (default)"
    elif model == "sonar-reasoning-pro":
        return "sonar-reasoning-pro (enhanced)"
    elif model == "sonar-deep-research":
        return "sonar-deep-research (research)"
    elif "llama-3.1-sonar-small" in model:
        return "llama-3.1-sonar-small (code)"
    elif "llama-3.1-sonar-large" in model:
        return "llama-3.1-sonar-large (advanced code)"
    else:
        return model

def normalize_model_name(model: str) -> str:
    """Normalize model name to match Perplexity's expected format."""
    if not model:
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

def detect_model(response_data: dict) -> str:
    """Detect which model was used based on response data."""
    if not response_data:
        return "unknown"
    model = response_data.get("model", "")
    if model:
        return normalize_model_name(model)
    # Attempt to detect from other fields
    if "usage" in response_data and hasattr(response_data["usage"], "model_name"):
        return normalize_model_name(response_data["usage"].model_name)
    return "unknown"

def estimate_cost(toks: int, mi: dict) -> float:
    """Estimate query cost based on token count."""
    return (toks/1_000_000) * mi["cost_per_million"]

def get_output_dir() -> str:
    """Return (and ensure) the output directory for query results."""
    from pathlib import Path
    d = Path(os.getcwd()) / "perplexity_results"
    d.mkdir(exist_ok=True)
    return str(d)

def generate_combined_filename(queries: list, opts: dict) -> str:
    """
    Generate a descriptive filename for combined results.
    
    Args:
        queries: List of query strings
        opts: Options dictionary containing format and other preferences
        
    Returns:
        Filename for combined results with appropriate extension
    """
    import re
    from datetime import datetime
    
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
    from datetime import datetime
    import uuid
    return str(uuid.uuid4()) if id_type=="session" else datetime.now().strftime("%Y%m%d_%H%M%S")

def format_path(path: str) -> str:
    """Format a path to be relative to the current directory if possible."""
    try:
        cwd = os.getcwd()
        return path[len(cwd)+1:] if path.startswith(cwd) else path
    except:
        return path