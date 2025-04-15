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

def get_model_info(m: str, reasoning: bool = False, pro_reasoning: bool = False) -> dict:
    """Return the model info dictionary based on flags."""
    if reasoning:
        return {"id": "reasoning", "model": "sonar-reasoning", "cost_per_million": 5.00, "reasoning": True}
    if pro_reasoning:
        return {"id": "pro-reasoning", "model": "sonar-reasoning-pro", "cost_per_million": 8.00, "reasoning": True}
    return {"id": m, "model": m, "cost_per_million": 1.00, "reasoning": False}

def normalize_model_name(model: str) -> str:
    """Normalize model name to match Perplexity's expected format."""
    if not model:
        return "sonar-pro"
    model = model.lower().replace("-", "").replace(" ", "")
    mappings = {"sonarpro": "sonar-pro", "sonar": "sonar", "sonarproreasoning": "sonar-pro-reasoning",
                "prosonar": "sonar-pro", "pro": "sonar-pro", "sonarreasoning": "sonar-reasoning"}
    return mappings.get(model, "sonar-pro")

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
    """Generate a descriptive filename for combined results."""
    import re
    from datetime import datetime
    if opts.get("output"):
        return os.path.basename(opts["output"])
    if len(queries) == 1 and len(queries[0]) <= 50:
        clean = re.sub(r'[^\w\s-]', '', queries[0]).strip().replace(" ", "_")[:50]
        return f"{clean}_combined.md"
    if len(queries) > 1:
        words = []
        for q in queries[:3]:
            for w in reversed(q.lower().split()):
                w = re.sub(r'[^\w\s-]', '', w)
                if w not in ['what','is','the','a','an','in','of','to','for','and','or','capital'] and w not in words:
                    words.append(w)
                    break
        name = "_".join(words) + (f"_and_{len(queries)-3}_more" if len(queries)>3 else "")
        return f"{name}_combined.md"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"combined_results_{len(queries)}q_{timestamp}.md"

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