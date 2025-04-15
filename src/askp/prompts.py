#!/usr/bin/env python3
"""
Prompt templates for ASKP.
Contains functions to generate prompts for different query types.
"""

def get_prompt_template(opts: dict) -> str:
    """
    Get the appropriate prompt template based on options.
    
    Args:
        opts: Options dictionary with format, model, etc.
        
    Returns:
        A template string with {query} placeholder
    """
    # Default template
    if opts.get("quick", False):
        return "Answer these questions concisely, one by one: {query}"
    return "Give a thorough and informative answer to the following: {query}"
