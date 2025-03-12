#!/usr/bin/env python3
"""Utility functions for ASKP."""
from typing import Optional

def detect_model(text: str, filename: Optional[str] = None) -> str:
    """Detect the most appropriate model based on text content and filename.
    
    Args:
        text: Content to analyze
        filename: Optional filename for context
        
    Returns:
        Model ID string
    """
    text = text.lower()
    if "sonar-pro" in text:
        return "sonar-pro"
    elif "pplx-api" in text:
        return "pplx"
    elif "gpt4-omni" in text:
        return "gpt4"
    elif "claude-3.5" in text:
        return "claude"
    if filename:
        filename = filename.lower()
        if "sonar-pro" in filename:
            return "sonar-pro"
        elif "pplx-api" in filename or "pplx" in filename:
            return "pplx"
        elif "gpt4-omni" in filename or "gpt4" in filename:
            return "gpt4"
        elif "claude-3.5" in filename or "claude" in filename:
            return "claude"
    return "sonar"