#!/usr/bin/env python3
"""
Prompt templates for ASKP.
These control how queries are sent to Perplexity.
"""

# Default prompt for information density
DEFAULT_PROMPT = """
Provide a highly factual, information-dense response to the following:
{query}

Format your response to maximize information density with these guidelines:
- Focus exclusively on concrete facts and information
- Eliminate all filler words, phrases and redundancies
- Use up to 50 words per line for maximum density
- Prioritize key details over explanatory text
- Remove pleasantries, introductions and conclusions
"""

# Human-readable prompt
HUMAN_READABLE_PROMPT = """
Answer the following question in a clear, well-structured format:
{query}

Provide thorough explanations with examples where helpful.
Use formatting to enhance readability.
"""

def get_prompt_template(opts):
    """Return the appropriate prompt template based on options."""
    if opts.get("human_readable", False):
        return HUMAN_READABLE_PROMPT
    return DEFAULT_PROMPT
