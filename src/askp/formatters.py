#!/usr/bin/env python3
"""
Formatting functions for ASKP.
Contains format_json, format_markdown, and format_text.
"""
import json
import re
from typing import Dict, Any

def format_json(res: Dict[str, Any]) -> str:
    """Format result as pretty JSON."""
    return json.dumps(res, indent=2)

def format_markdown(res: Dict[str, Any]) -> str:
    """Format result as markdown text."""
    parts = []
    meta = res.get("metadata", {})
    if meta.get("verbose", False):
        parts += [f"**Query:** {res.get('query', 'No query')}",
                  f"**Model:** {meta.get('model', 'Unknown')}",
                  f"**Tokens Used:** {meta.get('tokens', 0)}",
                  f"**Estimated Cost:** ${meta.get('cost', 0):.6f}\n"]
    if res.get("error"):
        # Safely handle error with string conversion
        error_str = str(res.get("error", ""))
        parts.append(f"**Error:** {error_str}")
    elif "content" in res:
        # Ensure the content is a string
        content = str(res["content"]) if res["content"] is not None else ""
        parts.append(content)
    elif res.get("results") and isinstance(res.get("results"), list) and res["results"] and "content" in res["results"][0]:
        # Also ensure content is a string here
        content = str(res["results"][0]["content"]) if res["results"][0]["content"] is not None else ""
        parts.append(content)
    else:
        parts.append("No content available")
    
    # Safely handle citations which might be in different formats
    if res.get("citations"):
        if meta.get("verbose", False):
            parts.append("\n**Citations:**")
        # Handle citations as either strings or dicts
        if res.get("citations") and isinstance(res.get("citations"), list):
            for c in res.get("citations", []):
                if isinstance(c, str):
                    parts.append(f"- {c}")
                elif isinstance(c, dict) and "url" in c:
                    parts.append(f"- {c['url']}")
                else:
                    parts.append(f"- {str(c)}")
    if meta.get("verbose", False):
        parts.append("\n## Metadata")
        for k, v in meta.items():
            parts.append(f"- **{k}:** " + (f"${v:.6f}" if k=="cost" else str(v)))
    return "\n".join(parts)

def format_text(res: Dict[str, Any]) -> str:
    """Format result as plain text."""
    parts = []
    meta = res.get("metadata", {})
    if meta.get("verbose", False):
        parts += [f"Query: {res.get('query', 'No query')}",
                 f"Model: {meta.get('model', 'Unknown')}",
                 f"Tokens Used: {meta.get('tokens', 0)}",
                 f"Estimated Cost: ${meta.get('cost', 0):.6f}\n"]
    if res.get("error"):
        # Safely handle error with string conversion
        error_str = str(res.get("error", ""))
        parts.append(f"Error: {error_str}")
    elif "content" in res:
        # Ensure the content is a string
        content = str(res["content"]) if res["content"] is not None else ""
        parts.append(content)
    elif res.get("results") and isinstance(res.get("results"), list) and res["results"] and "content" in res["results"][0]:
        # Also ensure content is a string here
        content = str(res["results"][0]["content"]) if res["results"][0]["content"] is not None else ""
        parts.append(content)
    else:
        parts.append("No content available")
    return "\n".join(parts)