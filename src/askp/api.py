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
from openai import AuthenticationError, APIError, RateLimitError, BadRequestError, APIConnectionError
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
import requests

ModelType = Literal[
    # Legacy Sonar Models
    "sonar", "sonar-pro", "sonar-reasoning", "sonar-reasoning-pro", "sonar-deep-research",
    # Llama 3.1 Sonar Models
    "llama-3.1-sonar-small-128k-online", "llama-3.1-sonar-large-128k-online", 
    "llama-3.1-sonar-small-128k-chat", "llama-3.1-sonar-large-128k-chat",
    # Llama 3.1 Instruct Models
    "llama-3.1-70b-instruct", "llama-3.1-8b-instruct",
    # Mixtral and PPLX Models
    "mixtral-8x7b-instruct", "pplx-7b-online", "pplx-70b-online", "pplx-7b-chat", "pplx-70b-chat",
    # Offline Model
    "r1-1776"
]

class PerplexityResponse(TypedDict, total=False):
    """TypedDict for Perplexity API response structure."""
    content: str
    model: str
    tokens: int
    query: str
    metadata: Dict[str, Any]
    error: Optional[str]
    raw_response: Optional[Any]
    citations: Optional[List[str]]
    
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
    from askp.cli import load_api_key, OpenAI
    
    api_key = api_key or load_api_key()
    if not api_key:
        raise ValueError("No API key found. Set PERPLEXITY_API_KEY environment variable or create a .env file.")
    
    return OpenAI(
        api_key=api_key,
        base_url="https://api.perplexity.ai"
    )

def safe_str(obj):
    """Convert any object to a string safely."""
    if obj is None:
        return ""
    try:
        return str(obj)
    except Exception:
        return repr(obj)

def search_perplexity(q: str, opts: Dict[str, Any]) -> Optional[PerplexityResponse]:
    """
    Search the Perplexity API with the given query and options.
    
    Args:
        q: The query string to send to Perplexity
        opts: Dictionary of options including:
            - model: Model name to use (sonar, sonar-pro, etc.)
            - temperature: Temperature for generation (0.0-1.0)
            - token_max: Maximum tokens to generate
            - search_depth: Search depth (low, medium, high)
    
    Returns:
        PerplexityResponse or None if the request failed
    """
    import os
    from askp.utils import normalize_model_name, get_model_info, estimate_cost

    model = normalize_model_name(opts.get("model", ""))
    
    # No more runtime model switching - explicit model selection only
    # Models are now directly selected by CLI flags
    
    temperature = float(opts.get("temperature", 0.7))
    max_tokens = int(opts.get("token_max", 4096))
    search_depth = opts.get("search_depth", "medium")
    
    # Prepare API client with appropriate configuration
    client = load_openai_client()
    if not client:
        return None
    
    verbose = opts.get("verbose", False)
    debug = opts.get("debug", False)
    model_info = get_model_info(model)
    
    # Only display model info if not suppressed
    if not opts.get("suppress_model_display", False):
        rprint(f"Model: {model_info['display_name']} | Temp: {temperature}")
    
    start_time = time.time()
    
    try:
        if verbose and not opts.get("quiet", False):
            rprint("Sending query to Perplexity API...")
        
        # Configure additional parameters based on search depth
        system_message = None
        if search_depth == "low":
            system_message = "Provide a brief answer with minimal search."
        elif search_depth == "high":
            system_message = "Provide a comprehensive answer with deep search across many sources."
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": q})
        
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
        except openai.AuthenticationError as e:
            error_msg = f"Authentication error: {e}. Please check your API key."
            rprint(f"{error_msg}")
            return {"error": error_msg}
        except openai.RateLimitError as e:
            error_msg = f"Rate limit exceeded: {e}. Please try again later."
            rprint(f"{error_msg}")
            return {"error": error_msg}
        except openai.APIError as e:
            error_msg = safe_str(e)
            if "insufficient_quota" in error_msg.lower():
                error_msg = f"Insufficient quota: {e}."
            rprint(f"{error_msg}")
            return {"error": error_msg}
        except openai.APIConnectionError as e:
            error_msg = f"API connection error: {e}. Please check your internet connection."
            rprint(f"{error_msg}")
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Error querying Perplexity API: {e}."
            rprint(f"{error_msg}")
            return {"error": error_msg}
        
        end_time = time.time()
        response_time = end_time - start_time
        
        try:
            content = completion.choices[0].message.content
            ob = len(content.encode("utf-8"))
            total = completion.usage.total_tokens
            
            mi = get_model_info(model)
            cost = estimate_cost(total, mi)
            
            result: PerplexityResponse = {
                "content": content,
                "model": model,
                "tokens": total,
                "query": q,
                "metadata": {
                    "bytes": ob,
                    "cost": cost,
                    "elapsed_time": response_time,
                    "timestamp": time.time(),
                    "uuid": str(uuid.uuid4())
                }
            }
            
            # Extract citation URLs if present in the response
            citations = []
            # Safely get citations, different versions of the API might store them differently
            if hasattr(completion, 'citations') and completion.citations:
                citations = completion.citations
            elif isinstance(completion, dict) and 'citations' in completion:
                citations = completion['citations']
                
            if citations:
                result["citations"] = citations
            
            # Add raw response for debug mode
            if opts.get("debug", False):
                result["raw_response"] = safe_str(completion)
            
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
            
            return result
            
        except (AttributeError, IndexError) as e:
            # Create a more user-friendly error message without excessive debug info
            diagnostic = f"Error accessing response data: {e}. Raw response: {safe_str(completion)}"
            rprint(f"{diagnostic}")
            return {"error": diagnostic, "raw_response": completion}
            
    except Exception as e:
        error_msg = f"Error querying Perplexity API: {e}"
        rprint(f"{error_msg}")
        return None

def get_account_status(api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Get Perplexity account status including remaining credits.
    
    Args:
        api_key: Optional API key to use instead of environment variable
        
    Returns:
        Dictionary containing account status information
    """
    from askp.utils import load_api_key
    
    try:
        api_key = api_key or load_api_key()
        client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai"
        )
        
        # Make a minimal models list request to check if the API key is valid
        try:
            # Try to make a small test request
            response = client.chat.completions.create(
                model="sonar",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5
            )
            
            # If we get here, the API key is valid
            return {
                "status": "active",
                "valid_key": True,
                "model_used": "sonar",
                "message": "API key is valid and working correctly",
                # Add estimated information since we can't get actual credits
                "credits": {
                    "remaining": "Unknown (API doesn't provide balance information)",
                    "used": "Unknown (API doesn't provide usage information)"
                }
            }
        except openai.AuthenticationError:
            return {
                "error": "Authentication failed. The API key is invalid or expired.",
                "status_code": 401,
                "valid_key": False
            }
        except openai.RateLimitError:
            return {
                "status": "rate_limited",
                "valid_key": True,
                "error": "Rate limit exceeded. This indicates your API key is valid but you've reached usage limits.",
                "status_code": 429
            }
        except openai.APIError as e:
            error_msg = safe_str(e)
            if "insufficient_quota" in safe_str(error_msg).lower():
                return {
                    "status": "no_credits",
                    "valid_key": True,
                    "error": "Insufficient quota. Your API key is valid but you have no remaining credits.",
                    "status_code": 429
                }
            return {
                "error": f"API error: {error_msg}",
                "status_code": 500,
                "valid_key": None  # Unknown if valid
            }
        except Exception as e:
            return {
                "error": f"Error checking account status: {str(e)}"
            }
    except Exception as e:
        return {
            "error": f"Error checking account status: {str(e)}"
        }

def display_account_status(api_key: Optional[str] = None, verbose: bool = False) -> None:
    """
    Display Perplexity account status including remaining credits in a nice format.
    
    Args:
        api_key: Optional API key to use instead of environment variable
        verbose: Whether to show more detailed information
    """
    status = get_account_status(api_key)
    
    if "error" in status:
        rprint(Panel(
            f"[bold red]{status['error']}[/bold red]",
            title="Error Checking Account Status",
            border_style="red"
        ))
        return
    
    # Create a table for the information
    table = Table(title="Perplexity API Key Status")
    
    # Add columns
    table.add_column("Item", style="cyan")
    table.add_column("Value", style="green")
    
    # Add API key status
    table.add_row("API Key", "✅ Valid" if status.get("valid_key", False) else "❌ Invalid")
    table.add_row("Status", status.get("status", "Unknown"))
    
    # Add a note about the API limitation
    table.add_row(
        "Credits Info", 
        "⚠️ Not available via API (must check Perplexity dashboard)"
    )
    
    if verbose:
        table.add_row(
            "Note", 
            "Perplexity API does not provide endpoints for checking credit balance.\n"
            "Visit https://www.perplexity.ai/account/api/keys for account details."
        )
    
    # Print the table
    rprint(table)