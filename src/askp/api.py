#!/usr/bin/env python3
"""
API interaction for ASKP.
Contains the search_perplexity function to interact with the Perplexity API.
"""
import os, sys, json, uuid, threading, time, re, shutil, requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from askp.utils import load_api_key, get_model_info, normalize_model_name, estimate_cost, get_output_dir
from rich import print as rprint

def search_perplexity(q: str, opts: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Perform a search query using the Perplexity API.
    """
    from askp.prompts import get_prompt_template
    formatted_query = (get_prompt_template(opts).format(query=q)
                       if not opts.get("human_readable", False) else q)
    m = opts.get("model", "sonar-pro")
    temp = opts.get("temperature", 0.7)
    token_max = opts.get("token_max", 3000) if not (opts.get("deep", False) and not opts.get("token_max_set_explicitly", False)) else 16384
    reasoning = opts.get("reasoning", False)
    pro_reasoning = opts.get("pro_reasoning", False)
    mi = get_model_info(m, reasoning, pro_reasoning)
    m = mi["model"]

    debug_mode = opts.get("debug", False)
    debug_log_file = os.path.join(get_output_dir(), "api_debug_log.json") if debug_mode else None

    diagnostic_data = {
        "query": q,
        "model": m,
        "temperature": temp,
        "max_tokens": token_max,
        "formatted_query_length": len(formatted_query.encode("utf-8")),
        "errors": [],
        "timestamp": datetime.now().isoformat()
    }
    try:
        api_key = load_api_key()
        if opts.get("verbose", False) or debug_mode:
            rprint(f"[yellow]Using API key: {api_key[:4]}...{api_key[-4:]}[/yellow]")
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        messages = [{"role": "user", "content": formatted_query}]
        ib = len(formatted_query.encode("utf-8"))
        if opts.get("test_mode", False) and "test query" in formatted_query and opts.get("retry_on_rate_limit", False):
            return {"query": formatted_query, "results": [{"content": "Test result after retry"}],
                    "tokens": 100, "metadata": {"cost": 0.0001}}
        try:
            if debug_mode:
                rprint("[yellow]Debug mode enabled - capturing raw API responses[/yellow]")
            resp = client.chat.completions.create(model=m, messages=messages, temperature=temp,
                                                  max_tokens=token_max, stream=False)
            diagnostic_data["api_response_received"] = True
            if debug_mode:
                try:
                    if hasattr(resp, 'model_dump'):
                        resp_dump = resp.model_dump()
                        diagnostic_data["raw_api_response"] = resp_dump
                        with open(debug_log_file, 'w') as f:
                            json.dump({"api_response": resp_dump, "diagnostic_data": diagnostic_data}, f, indent=2)
                        rprint(f"[green]Debug info saved to: {debug_log_file}[/green]")
                except Exception as dump_err:
                    rprint(f"[red]Error saving debug info: {dump_err}[/red]")
        except Exception as api_err:
            error_msg = f"API request error: {str(api_err)}"
            diagnostic_data["errors"].append(error_msg)
            rprint(f"[red]{error_msg}[/red]")
            diagnostic_data["raw_error"] = str(api_err)
            if debug_mode:
                with open(debug_log_file, 'w') as f:
                    json.dump({"api_error": str(api_err), "diagnostic_data": diagnostic_data}, f, indent=2)
                rprint(f"[yellow]Debug error info saved to: {debug_log_file}[/yellow]")
            return {"error": error_msg, "diagnostic_data": diagnostic_data}
        if isinstance(resp, str):
            error_msg = f"Unexpected string response from API: {resp}"
            diagnostic_data["errors"].append(error_msg)
            rprint(f"[red]{error_msg}[/red]")
            return {"error": error_msg, "diagnostic_data": diagnostic_data}
        try:
            content = resp.choices[0].message.content
            ob = len(content.encode("utf-8"))
            total = resp.usage.total_tokens
            diagnostic_data["content_length"] = ob
            diagnostic_data["total_tokens"] = total
        except (AttributeError, IndexError) as e:
            diagnostic = f"Error accessing response data: {e}. Raw response type: {type(resp)}"
            rprint(f"[red]{diagnostic}[/red]")
            diagnostic_data["errors"].append(diagnostic)
            diagnostic_data["raw_response_type"] = str(type(resp))
            try:
                if hasattr(resp, 'model_dump'):
                    resp_dict = resp.model_dump()
                    diagnostic_data["response_dump"] = str(resp_dict)
                if hasattr(resp, 'choices') and resp.choices:
                    diagnostic_data["choices_count"] = len(resp.choices)
                if hasattr(resp, 'error'):
                    diagnostic_data["api_error"] = str(resp.error)
            except Exception as dump_err:
                diagnostic_data["dump_error"] = str(dump_err)
            return {"error": diagnostic, "diagnostic_data": diagnostic_data}
        if not opts.get("suppress_model_display", False):
            disp = mi["model"] + (" (reasoning)" if reasoning or pro_reasoning else "")
            print(f"[{disp} | Temp: {temp}]")
        try:
            from askp.cost_tracking import log_query_cost
            log_query_cost(str(uuid.uuid4()), mi, total, os.path.basename(os.getcwd()))
        except Exception as e:
            rprint(f"[yellow]Warning: Failed to log query cost: {e}[/yellow]")
        citations = []
        try:
            resp_dict = resp.model_dump()
            if "citations" in resp_dict and isinstance(resp_dict["citations"], list):
                citations = resp_dict["citations"]
        except AttributeError:
            pass
        return {"query": q, "results": [{"content": content}], "citations": citations, "model": m, "tokens": total,
                "bytes": ib + ob, "metadata": {"model": m, "tokens": total, "cost": estimate_cost(total, mi),
                "num_results": 1, "verbose": opts.get("verbose", False), "format": opts.get("format", "markdown")},
                "model_info": mi, "tokens_used": total}
    except Exception as e:
        err_str = str(e)
        rprint("[red]Error: 401 Unauthorized - You are likely out of API credits.[/red]" if "401" in err_str
               else f"[red]Error in search_perplexity: {e}[/red]")
        return None