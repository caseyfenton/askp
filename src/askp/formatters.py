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
        parts.append(f"**Error:** {res['error']}")
    elif "content" in res:
        parts.append(res["content"])
    elif res.get("results") and "content" in res["results"][0]:
        parts.append(res["results"][0]["content"])
    else:
        parts.append("No content available")
    if res.get("citations") and meta.get("verbose", False):
        parts.append("\n**Citations:**")
        parts += [f"- {c}" for c in res["citations"]]
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
                  f"Tokens: {meta.get('tokens', 0)}",
                  f"Cost: ${meta.get('cost', 0):.6f}\n"]
    if res.get("error"):
        parts.append(f"Error: {res['error']}")
    elif "content" in res:
        parts.append(res["content"])
    elif res.get("results") and "content" in res["results"][0]:
        parts.append(res["results"][0]["content"])
    else:
        parts.append("No content available")
    return "\n".join(parts)