#!/usr/bin/env python3
"""
API interaction module for ASKP CLI.
Contains functions to interact with the Perplexity API and process responses.
"""
import os
import sys
import json
import time
import uuid
from typing import Dict, Any, Optional, List, Union, Tuple, TypedDict, Literal

import openai
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn

ModelType = Literal["sonar", "sonar-pro", "sonar-pro-reasoning", "sonar-reasoning"]

class PerplexityResponse(TypedDict, total=False):
    """TypedDict for Perplexity API response structure."""
    content: str
    model: str
    tokens: int
    query: str
    metadata: Dict[str, Any]
    error: Optional[str]
    raw_response: Optional[Any]
    
def load_openai_client(api_key: Optional[str] = None) -> openai.OpenAI:
    """
    Load OpenAI client with appropriate configuration for Perplexity API.
    
    Args:
        api_key: Optional API key to use instead of environment variable
        
    Returns:
        Configured OpenAI client for Perplexity API
        
    Raises:
        ValueError: If no API key is found
    """
    from askp.utils import load_api_key
    
    api_key = api_key or load_api_key()
    if not api_key:
        raise ValueError("No API key found. Set PERPLEXITY_API_KEY environment variable or create a .env file.")
    
    return openai.OpenAI(
        api_key=api_key,
        base_url="https://api.perplexity.ai"
    )

def search_perplexity(q: str, opts: Dict[str, Any]) -> Optional[PerplexityResponse]:
    """
    Search the Perplexity API with the given query and options.
    
    Args:
        q: The query string to send to Perplexity
        opts: Dictionary of options including:
            - model: Model name to use (sonar, sonar-pro, etc.)
            - temperature: Temperature for generation (0.0-1.0)
            - token_max: Maximum tokens to generate
            - reasoning: Whether to use reasoning mode
            - pro_reasoning: Whether to use pro reasoning mode
            - debug: Whether to capture raw API responses
            
    Returns:
        Dictionary containing the response content and metadata, or
        an error dictionary with 'error' key if the request failed
        
    Note:
        If the request fails, returns a dictionary with an 'error' key
        instead of None for better error handling in downstream functions.
    """
    from askp.utils import normalize_model_name, get_model_info, estimate_cost
    
    model = normalize_model_name(opts.get("model", ""))
    if opts.get("reasoning", False) and "reasoning" not in model:
        model = "sonar-reasoning" if model == "sonar" else "sonar-pro-reasoning"
    if opts.get("pro_reasoning", False):
        model = "sonar-pro-reasoning"
    
    temperature = float(opts.get("temperature", 0.7))
    max_tokens = int(opts.get("token_max", 4096))
    
    if opts.get("verbose", False):
        rprint(f"[blue]Query: {q}[/blue]")
        rprint(f"[blue]Model: {model}, Temperature: {temperature}, Max tokens: {max_tokens}[/blue]")
    
    try:
        client = load_openai_client()
        
        # Only show progress if not explicitly disabled (for parallel queries)
        if opts.get("disable_progress", False):
            # Skip progress display for concurrent requests
            start_time = time.time()
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": q}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            elapsed = time.time() - start_time
        else:
            # Use progress indicator for single requests
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Querying Perplexity API...", total=None)
                
                start_time = time.time()
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": q}],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                elapsed = time.time() - start_time
        
        try:
            content = resp.choices[0].message.content
            ob = len(content.encode("utf-8"))
            total = resp.usage.total_tokens
            
            mi = get_model_info(model, "reasoning" in model, "pro-reasoning" in model)
            cost = estimate_cost(total, mi)
            
            result: PerplexityResponse = {
                "content": content,
                "model": model,
                "tokens": total,
                "query": q,
                "metadata": {
                    "bytes": ob,
                    "cost": cost,
                    "elapsed_time": elapsed,
                    "timestamp": time.time(),
                    "uuid": str(uuid.uuid4())
                }
            }
            
            # Log query cost if not suppressed
            if not opts.get("suppress_cost_logging", False):
                try:
                    log_query_success = False
                    try:
                        from .cost_tracking import log_query_cost
                        log_query_cost(q[:50], total, cost, model)
                        log_query_success = True
                    except ImportError:
                        # This is expected if matplotlib is not available
                        if opts.get("verbose", False):
                            print("Cost tracking disabled: required dependencies not available")
                    except Exception as e:
                        # Other errors during cost logging
                        if opts.get("verbose", False):
                            print(f"Warning: Failed to log query cost: {e}")
                    
                    # If cost tracking failed but debug mode is on, show more info
                    if not log_query_success and opts.get("debug", False):
                        print("Note: Cost tracking is disabled due to missing matplotlib/numpy dependencies.")
                        print("This does not affect core functionality.")
                except Exception as e:
                    if opts.get("verbose", False):
                        print(f"Warning: Cost logging error: {e}")
            
            # If debug mode is enabled, capture the raw response
            if opts.get("debug", False):
                result["raw_response"] = resp
                
            return result
            
        except (AttributeError, IndexError) as e:
            diagnostic = f"Error accessing response data: {e}. Raw response: {resp}"
            rprint(f"[red]{diagnostic}[/red]")
            return {"error": diagnostic, "raw_response": resp}
            
    except Exception as e:
        error_msg = f"Error querying Perplexity API: {e}"
        rprint(f"[red]{error_msg}[/red]")
        return {"error": error_msg}