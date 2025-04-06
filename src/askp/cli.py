#!/usr/bin/env python3
"""
ASKP – Ask Perplexity CLI with Multi-Query Support.
Interface to the Perplexity API for search and knowledge discovery.
"""
import os
import sys
import json
import uuid
import threading
import time
import re
import shutil
import requests
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Any

import click
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from openai import OpenAI
from rich.panel import Panel
from .cost_tracking import log_query_cost
from .tips import get_formatted_tip
from .file_utils import get_file_stats, generate_cat_commands, format_path

console = Console()
VERSION = "2.4.1"


def sanitize_filename(q: str) -> str:
    """Sanitize a query string to produce a safe filename.

    Args:
        q: The query string.

    Returns:
        A sanitized filename string (max 50 characters).
    """
    s = "".join(c if c.isalnum() else "_" for c in q)
    return s[:50] if s.strip("_") else "query"


def load_api_key() -> str:
    """Load the Perplexity API key from environment or .env files.

    Returns:
        The API key string.

    Exits:
        Exits the program if the key is not found.
    """
    key = os.environ.get("PERPLEXITY_API_KEY")
    if key:
        return key
        
    for p in [Path.home() / ".env", Path.home() / ".perplexity" / ".env", Path.home() / ".askp" / ".env"]:
        if p.exists():
            try:
                content = p.read_text()
                for line in content.splitlines():
                    if line.startswith("PERPLEXITY_API_KEY="):
                        key = line.split("=", 1)[1].strip().strip('"\'' )
                        return key
            except Exception as e:
                rprint(f"[yellow]Warning: Error reading {p}: {e}[/yellow]")
    rprint("[red]Error: Could not find Perplexity API key.[/red]")
    sys.exit(1)


def get_model_info(m: str, reasoning: bool = False, pro_reasoning: bool = False) -> dict:
    """Return the model information dictionary based on flags.

    Args:
        m: Model name string.
        reasoning: Whether to use the reasoning model.
        pro_reasoning: Whether to use the pro reasoning model.

    Returns:
        Dictionary with model details.
    """
    if reasoning:
        return {"id": "reasoning", "model": "sonar-reasoning", "cost_per_million": 5.00, "reasoning": True}
    if pro_reasoning:
        return {"id": "pro-reasoning", "model": "sonar-reasoning-pro", "cost_per_million": 8.00, "reasoning": True}
    return {"id": m, "model": m, "cost_per_million": 1.00, "reasoning": False}


def normalize_model_name(model: str) -> str:
    """Normalize model name to handle case variations.
    
    Args:
        model: Input model name string
        
    Returns:
        Normalized model name that matches Perplexity's expected format
    """
    if not model:
        return "sonar-pro"
        
    model = model.lower().replace("-", "").replace(" ", "")
    mappings = {
        "sonarpro": "sonar-pro",
        "sonar": "sonar",
        "sonarproreasoning": "sonar-pro-reasoning",
        "prosonar": "sonar-pro",
        "pro": "sonar-pro",
        "sonarpro": "sonar-pro",
        "sonarreasoning": "sonar-reasoning"
    }
    return mappings.get(model, "sonar-pro")  # Default to sonar-pro if unknown


def estimate_cost(toks: int, model_info: dict) -> float:
    """Estimate the cost of a query based on token count.

    Args:
        toks: Number of tokens.
        model_info: Dictionary containing model cost per million tokens.

    Returns:
        Estimated cost as a float.
    """
    return (toks / 1_000_000) * model_info["cost_per_million"]


def search_perplexity(q: str, opts: dict) -> Optional[dict]:
    """Perform a search query using the Perplexity API.

    Args:
        q: Query string.
        opts: Options dictionary with model, temperature, tokens, etc.

    Returns:
        A dictionary with query results or None if an error occurred.
    """
    m = opts.get("model", "sonar-pro")
    temp = opts.get("temperature", 0.7)
    max_tokens = opts.get("max_tokens", 8192)
    if opts.get("deep", False) and not opts.get("token_max_set_explicitly", False):
        max_tokens = 16384
    reasoning = opts.get("reasoning", False)
    pro_reasoning = opts.get("pro_reasoning", False)
    model_info = get_model_info(m, reasoning, pro_reasoning)
    m = model_info["model"]
    try:
        api_key = load_api_key()
        if opts.get("verbose", False):
            rprint(f"[yellow]Using API key: {api_key[:4]}...{api_key[-4:]}[/yellow]")
        client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        messages = [{"role": "user", "content": q}]
        ib = len(q.encode("utf-8"))
        resp = client.chat.completions.create(
            model=m, messages=messages, temperature=temp, max_tokens=max_tokens, stream=False
        )
        if isinstance(resp, str):
            rprint(f"[red]Error: Unexpected string response from API: {resp}[/red]")
            return None
            
        try:
            content = resp.choices[0].message.content
            ob = len(content.encode("utf-8"))
            total = resp.usage.total_tokens
        except (AttributeError, IndexError) as e:
            rprint(f"[red]Error accessing response data: {e}[/red]")
            rprint(f"[yellow]Response type: {type(resp)}[/yellow]")
            return None
            
        if not opts.get("suppress_model_display", False):
            disp = model_info["model"] + (" (reasoning)" if reasoning or pro_reasoning else "")
            print(f"[{disp} | Temp: {temp}]")
        try:
            log_query_cost(str(uuid.uuid4()), model_info, total, os.path.basename(os.getcwd()))
        except Exception as e:
            rprint(f"[yellow]Warning: Failed to log query cost: {e}[/yellow]")
            
        citations = []
        try:
            resp_dict = resp.model_dump()
            if "citations" in resp_dict and isinstance(resp_dict["citations"], list):
                citations = resp_dict["citations"]
        except AttributeError:
            pass
            
        return {
            "query": q,
            "results": [{"content": content}],
            "citations": citations,  
            "model": m,
            "tokens": total,
            "bytes": ib + ob,
            "metadata": {
                "model": m,
                "tokens": total,
                "cost": estimate_cost(total, model_info),
                "num_results": 1,
                "verbose": opts.get("verbose", False),
                "format": opts.get("format", "markdown"),  
            },
            "model_info": model_info,
            "tokens_used": total,
        }
    except Exception as e:
        err_str = str(e)
        if "401" in err_str:
            rprint("[red]Error: 401 Unauthorized - You are likely out of API credits.[/red]")
            rprint("[yellow]Please visit https://perplexity.ai/account/api to check your balance and add more credits.[/yellow]")
        else:
            rprint(f"[red]Error in search_perplexity: {e}[/red]")
        return None


def get_output_dir() -> str:
    """Ensure and return the output directory for query results.

    Returns:
        The absolute path of the output directory.
    """
    d = Path(os.getcwd()) / "perplexity_results"
    d.mkdir(exist_ok=True)
    return str(d)


def save_result_file(q: str, res: dict, i: int, out_dir: str) -> str:
    """Save query result to a file (Markdown by default, JSON if specified).

    Args:
        q: The query string.
        res: The result dictionary.
        i: Query index.
        out_dir: Output directory.

    Returns:
        File path of the saved result.
    """
    os.makedirs(out_dir, exist_ok=True)
    
    use_json = res.get("metadata", {}).get("format", "markdown") == "json"
    
    if use_json:
        fname = f"{i:03d}_{sanitize_filename(q)[:50]}.json"
        fpath = os.path.join(out_dir, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2)
    else:
        fname = f"{i:03d}_{sanitize_filename(q)[:50]}.md"
        fpath = os.path.join(out_dir, fname)
        
        content = format_markdown(res)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
            
    return fpath


def append_to_combined(q: str, res: dict, i: int, out_dir: str, lock: threading.Lock, opts: dict) -> str:
    """Append individual query result to a combined markdown file.

    Args:
        q: The query string.
        res: The result dictionary.
        i: Query index.
        out_dir: Output directory.
        lock: Threading lock to synchronize file writes.
        opts: Options dictionary containing settings.

    Returns:
        File path of the combined results file.
    """
    if opts.get("output"):
        combined = opts["output"]
    else:
        combined = os.path.join(out_dir, generate_combined_filename([q], opts))
    
    with lock:
        # Read existing content and parse sections
        sections = {}
        toc_entries = []
        if os.path.exists(combined):
            try:
                with open(combined, "r", encoding="utf-8") as f:
                    content = f.read()
                    # Extract existing sections
                    for section in re.split(r'\n---\n+', content):
                        if section.strip():
                            match = re.search(r'## Query (\d+): (.+?)\n', section)
                            if match:
                                query_num = int(match.group(1))
                                query_text = match.group(2)
                                sections[query_text] = section
            except Exception:
                pass
        
        # Add or update this section
        safe_name = re.sub(r'[^\w\s-]', '', q).strip().lower().replace(" ", "-")
        individual_file = f"query_{i+1}_{safe_name[:30]}.md"
        
        section = f"\n## Query {i+1}: {q}\n\n"
        section += res["results"][0]["content"]
        section += f"\n\n[View detailed results]({individual_file})\n"
        sections[q] = section
        
        # Write the combined file
        with open(combined, "w", encoding="utf-8") as f:
            f.write("# Combined Research Results\n\n")
            f.write("## Table of Contents\n\n")
            
            # Write table of contents
            for idx, (query, _) in enumerate(sections.items(), 1):
                safe_name = re.sub(r'[^\w\s-]', '', query).strip().lower().replace(" ", "-")
                f.write(f"{idx}. [{query}](#{safe_name})\n")
            
            # Write sections
            for section in sections.values():
                f.write("\n")
                f.write(section)
                f.write("\n---\n")
    
    return combined


def execute_query(q: str, i: int, opts: dict, lock: Optional[threading.Lock] = None) -> Optional[dict]:
    """Execute a single query and handle saving the result.

    Args:
        q: The query string.
        i: Query index.
        opts: Options dictionary.
        lock: Optional threading lock for combined file writing.

    Returns:
        The query result dictionary or None on failure.
    """
    res = search_perplexity(q, opts)
    if not res:
        return None
    od = get_output_dir()
    rf = save_result_file(q, res, i, od)
    if opts.get("combine") and lock:
        cf = append_to_combined(q, res, i, od, lock, opts)
        rprint(f"[green]Combined results saved to {cf}[/green]")
    if opts.get("suppress_model_display", False):
        t = q[:40] + "..." if len(q) > 40 else q
        if "results" in res and res["results"]:
            bytes_count = len(res["results"][0].get("content", ""))
        else:
            bytes_count = len(res.get("content", ""))
        rprint(f'{i+1}: "{t}"  {bytes_count:,} bytes | {res.get("tokens", 0):,} tokens | ${res["metadata"]["cost"]:.4f}')
    rprint(f"[green]Result saved: {rf}[/green]")
    return res


def handle_multi_query(queries: List[str], opts: dict) -> List[Optional[dict]]:
    """Process multiple queries in parallel.

    Args:
        queries: A list of query strings.
        opts: Options dictionary.

    Returns:
        A list of result dictionaries.
    """
    print(f"\nProcessing {len(queries)} queries in parallel...")
    mi = get_model_info(opts.get("model", "sonar-pro"), opts.get("reasoning", False), opts.get("pro_reasoning", False))
    print(f"Model: {mi['model']}{' (reasoning)' if mi.get('reasoning', False) else ''} | Temp: {opts.get('temperature', 0.7)}")
    opts["suppress_model_display"] = True
    
    results: List[Optional[dict]] = []
    total_tokens = 0
    total_cost = 0
    start = time.time()
    lock = threading.Lock()
    
    # Pre-generate combined filename if needed
    if opts.get("combine"):
        od = get_output_dir()
        if not opts.get("output"):
            opts["output"] = os.path.join(od, generate_combined_filename(queries, opts))
    
    max_workers = opts.get("max_parallel", 10)
    with ThreadPoolExecutor(max_workers=min(max_workers, len(queries))) as ex:
        futures = {ex.submit(execute_query, q, i, opts, lock): i for i, q in enumerate(queries)}
        for f in futures:
            try:
                r = f.result()
                if r:
                    results.append(r)
                    total_tokens += r.get("tokens", 0)
                    total_cost += r["metadata"].get("cost", 0)
            except Exception as e:
                rprint(f"[red]Error in future: {e}[/red]")
                
    elapsed = time.time() - start
    qps = len(results) / elapsed if elapsed > 0 else 0
    od = get_output_dir()
    
    if opts.get("deep", False) and len(results) > 1:
        try:
            if opts.get("verbose", False):
                rprint("[blue]Synthesizing research results...[/blue]")
            from .deep_research import synthesize_research
            sections = {}
            for i, r in enumerate(results):
                if i == 0:
                    continue
                sec = f"Section {i}: {r.get('query', '')}"
                content = r.get("results", [{}])[0].get("content", "")
                sections[sec] = content
            orig = opts.get("research_overview", results[0]["query"])
            if isinstance(orig, tuple):
                orig = " ".join(str(x) for x in orig)
            synthesis = synthesize_research(query=orig, results=sections, options=opts)
            intro_text = synthesis.get("introduction", "")
            concl_text = synthesis.get("conclusion", "")
            intro = {
                "query": "Introduction",
                "content": intro_text,
                "tokens": int(len(intro_text.split()) * 1.3),
                "metadata": {
                    "cost": int(len(intro_text.split()) * 1.3) * 0.000001,
                    "verbose": opts.get("verbose", False),
                    "model": opts.get("model", "sonar-pro"),
                    "tokens": int(len(intro_text.split()) * 1.3),
                    "num_results": 1,
                },
            }
            concl = {
                "query": "Conclusion",
                "content": concl_text,
                "tokens": int(len(concl_text.split()) * 1.3),
                "metadata": {
                    "cost": int(len(concl_text.split()) * 1.3) * 0.000001,
                    "verbose": opts.get("verbose", False),
                    "model": opts.get("model", "sonar-pro"),
                    "tokens": int(len(concl_text.split()) * 1.3),
                    "num_results": 1,
                },
            }
            results.insert(0, intro)
            results.append(concl)
            total_tokens += intro["tokens"] + concl["tokens"]
            total_cost += intro["metadata"]["cost"] + concl["metadata"]["cost"]
        except Exception as e:
            if opts.get("verbose", False):
                rprint(f"[yellow]Warning: Failed to synthesize research: {e}[/yellow]")
                
    if not opts.get("deep", False):
        print("\nProcessing complete!")
        if len(results) == 1:
            print(f"Result: {od}/{os.path.basename(save_result_file(results[0]['query'], results[0], 0, od))}")
        else:
            print(f"Results: {od}")
        print(f"Queries: {len(results)}/{len(queries)}")
        total_bytes = 0
        for r in results:
            if not r:
                continue
            if "results" in r and r["results"]:
                content_bytes = len(r["results"][0].get("content", ""))
            else:
                content_bytes = len(r.get("content", ""))
            total_bytes += content_bytes
        print(f"Totals | {total_bytes:,} bytes | {total_tokens:,} tokens | ${total_cost:.4f} | {elapsed:.1f}s ({qps:.2f} q/s)")
        
    if results:
        results[0]["metadata"].update({"queries_per_second": qps, "elapsed_time": elapsed, "output_dir": od})
    return results


def format_json(res: dict) -> str:
    """Format result dictionary as pretty JSON.

    Args:
        res: The result dictionary.

    Returns:
        JSON formatted string.
    """
    return json.dumps(res, indent=2)


def format_markdown(res: dict) -> str:
    """Format result as markdown text.

    Args:
        res: The result dictionary.

    Returns:
        Markdown formatted string.
    """
    parts = ["# Search Results\n"]
    meta = res.get("metadata", {})
    if meta.get("verbose", False):
        parts += [
            f"**Query:** {res.get('query', 'No query')}",
            f"**Model:** {meta.get('model', 'Unknown')}",
            f"**Tokens Used:** {meta.get('tokens', 0)}",
            f"**Estimated Cost:** ${meta.get('cost', 0):.6f}\n",
        ]
    if "content" in res:
        parts.append(res["content"])
    elif "results" in res and res["results"] and "content" in res["results"][0]:
        parts.append(res["results"][0]["content"])
    else:
        parts.append("No content available")
    if res.get("citations") and meta.get("verbose", False):
        parts.append("\n**Citations:**")
        parts += [f"- {c}" for c in res["citations"]]
    if meta.get("verbose", False):
        parts.append("\n## Metadata")
        for k, v in meta.items():
            formatted_v = f"${v:.6f}" if k == "cost" else v
            parts.append(f"- **{k}:** {formatted_v}")
    return "\n".join(parts)


def format_text(res: dict) -> str:
    """Format result as plain text.

    Args:
        res: The result dictionary.

    Returns:
        Plain text formatted string.
    """
    parts = ["=== Search Results ==="]
    meta = res.get("metadata", {})
    if meta.get("verbose", False):
        parts += [
            f"Query: {res.get('query', 'No query')}",
            f"Model: {meta.get('model', 'Unknown')}",
            f"Tokens: {meta.get('tokens', 0)}",
            f"Cost: ${meta.get('cost', 0):.6f}\n",
        ]
    if "content" in res:
        parts.append(res["content"])
    elif "results" in res and res["results"] and "content" in res["results"][0]:
        parts.append(res["results"][0]["content"])
    else:
        parts.append("No content available")
    return "\n".join(parts)


def output_result(res: dict, opts: dict) -> None:
    """Output a single query result based on options.

    Args:
        res: The result dictionary.
        opts: Options dictionary.
    """
    if not res or opts.get("quiet", False):
        return
    fmt = opts.get("format", "markdown")
    if fmt == "json":
        out = format_json(res)
    elif fmt == "text":
        out = format_text(res)
    else:
        out = format_markdown(res)
    if fmt in {"markdown", "text"}:
        disp = res.get("model", "") + (" (reasoning)" if res.get("model_info", {}).get("reasoning", False) else "")
        out += f"\n{disp} | {res.get('tokens_used', 0):,} tokens | ${res.get('metadata', {}).get('cost', 0):.4f}"
    if opts.get("output"):
        p = Path(opts["output"])
        if not p.parent.exists():
            rprint(f"[red]Error: Directory {p.parent} does not exist[/red]")
        else:
            try:
                p.write_text(out, encoding="utf-8")
                rprint(f"[green]Output saved to {opts['output']}[/green]")
            except PermissionError:
                rprint(f"[red]Error: Permission denied writing to {opts['output']}[/red]")
    else:
        if fmt == "markdown":
            console.print(Markdown(out))
        else:
            click.echo(out)
    if not opts.get("quiet", False) and fmt != "json":
        rprint(f"[blue]Results directory: {get_output_dir()}[/blue]")
    if not opts.get("quiet", False) and not opts.get("multi", False):
        tip = get_formatted_tip()
        if tip:
            rprint(tip)


def output_multi_results(results: List[dict], opts: dict) -> None:
    """Combine and output results from multiple queries to a file.

    Args:
        results: List of result dictionaries.
        opts: Options dictionary.
    """
    if not results:
        return
    out_dir = opts.get("output_dir", os.path.join(os.getcwd(), "perplexity_results"))
    os.makedirs(out_dir, exist_ok=True)
    is_deep = opts.get("deep", False)
    overview = opts.get("research_overview", "")
    if isinstance(overview, (tuple, list)):
        overview = " ".join(str(x) for x in overview)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fmt = opts.get("format", "markdown")
    ext = "md" if fmt == "markdown" else ("json" if fmt == "json" else "txt")
    if is_deep:
        s_query = re.sub(r"[^\w\s-]", "", overview).strip().replace(" ", "_")[:30]
        fname = f"deep_research_{s_query}_{ts}.{ext}"
    elif len(results) == 1:
        s_query = re.sub(r"[^\w\s-]", "", results[0].get("query", "")).strip().replace(" ", "_")[:30]
        fname = f"query_result_{s_query}_{ts}.{ext}"
    else:
        fname = f"multi_query_results_{ts}.{ext}"
    out_fp = os.path.join(out_dir, fname)
    if fmt == "json":
        combined = [json.loads(format_json(r)) for r in results if r]
        if is_deep:
            combined.insert(0, {"research_overview": overview})
        with open(out_fp, 'w') as f:
            json.dump({"combined_result": combined}, f, ensure_ascii=False)
        out = json.dumps({"combined_result": combined}, ensure_ascii=False)
    elif fmt == "markdown":
        if is_deep:
            qdisp = overview if isinstance(overview, str) else " ".join(overview)
            out = f"# Deep Research: {qdisp}\n\n## Research Findings\n\n"
            for i, r in enumerate(results):
                if r:
                    out += f"### {i+1}. {r.get('query', 'Section '+str(i+1))}\n\n" + format_markdown(r) + "\n\n" + "-" * 50 + "\n\n"
            tot_toks = sum(r.get("tokens", 0) for r in results if r)
            tot_cost = sum(r.get("metadata", {}).get("cost", 0) for r in results if r)
            qps = results[0].get("metadata", {}).get("queries_per_second", 0) if results else 0
            et = results[0].get("metadata", {}).get("elapsed_time", 0) if results else 0
            out += f"\n## Summary\n\nTotals | Model: {opts.get('model', 'sonar-pro')} | {len(results)} queries | {tot_toks:,} tokens | ${tot_cost:.4f} | {et:.1f}s ({qps:.2f} q/s)\n\nResults: {out_fp}\n"
        else:
            out = "# Multiple Query Results\n\n" if len(results) > 1 else "# Single Query Result\n\n"
            for i, r in enumerate(results):
                if r:
                    qdisp = r.get("query", "Query " + str(i + 1))
                    qdisp = qdisp if len(qdisp) <= 50 else qdisp[:50] + "..."
                    out += f"## Query {i+1}: {qdisp}\n\n" + format_markdown(r) + "\n\n" + "-" * 50 + "\n\n"
            tot_toks = sum(r.get("tokens", 0) for r in results if r)
            tot_cost = sum(r.get("metadata", {}).get("cost", 0) for r in results if r)
            out += f"\n## Summary\n\nTotals | {len(results)} queries | {tot_toks:,} tokens | ${tot_cost:.4f}\n\nResults: {out_fp}\n"
    else:
        if is_deep:
            qdisp = overview if isinstance(overview, str) else " ".join(overview)
            out = f"=== Deep Research: {qdisp} ===\n\n=== Research Findings ===\n\n"
            for i, r in enumerate(results):
                if r:
                    out += f"=== {i+1}. {r.get('query', 'Section ' + str(i+1))} ===\n\n" + format_text(r) + "\n\n" + "=" * 50 + "\n\n"
            tot_toks = sum(r.get("tokens", 0) for r in results if r)
            tot_cost = sum(r.get("metadata", {}).get("cost", 0) for r in results if r)
            qps = results[0].get("metadata", {}).get("queries_per_second", 0) if results else 0
            et = results[0].get("metadata", {}).get("elapsed_time", 0) if results else 0
            out += "=== Summary ===\n\n" + f"Totals | Model: {opts.get('model', 'sonar-pro')} | {len(results)} queries | {tot_toks:,} tokens | ${tot_cost:.4f} | {et:.1f}s ({qps:.2f} q/s)\n\nResults: {out_fp}\n"
        else:
            out = "=== Multi-Query Results ===\n\n" if len(results) > 1 else "=== Single Query Result ===\n\n"
            for i, r in enumerate(results):
                if r:
                    qdisp = r.get("query", "Query " + str(i + 1))
                    qdisp = qdisp if len(qdisp) <= 50 else qdisp[:50] + "..."
                    out += f"=== Query {i+1}: {qdisp} ===\n\n" + format_text(r) + "\n\n" + "=" * 50 + "\n\n"
            tot_toks = sum(r.get("tokens", 0) for r in results if r)
            tot_cost = sum(r.get("metadata", {}).get("cost", 0) for r in results if r)
            out += "=== Summary ===\n\n" + f"Totals | {len(results)} queries | {tot_toks:,} tokens | ${tot_cost:.4f}\n\nResults: {out_fp}\n"
    if opts.get("output") == '-':
        sys.stdout = sys.stderr
    with open(out_fp, "w", encoding="utf-8") as f:
        f.write(out)
        
    file_size, line_count = get_file_stats(out_fp)
    cat_commands = generate_cat_commands([out_fp])
    
    file_stats = f"\n=== File Information ===\n"
    file_stats += f"Location: {out_fp}\n"
    file_stats += f"Size: {file_size:,} bytes | Lines: {line_count:,}\n"
    file_stats += f"\n=== Viewing Commands ===\n"
    for i, cmd in enumerate(cat_commands):
        if len(cat_commands) > 1:
            file_stats += f"Part {i+1}/{len(cat_commands)}: {cmd}\n"
        else:
            file_stats += f"View all: {cmd}\n"
    
    with open(out_fp, "a", encoding="utf-8") as f:
        f.write(file_stats)
    
    out += file_stats
        
    if not opts.get("quiet", False) and (len(results) == 1 or opts.get("verbose", False)):
        if fmt == "markdown":
            console.print(Markdown(out))
        else:
            click.echo(out)
    return out_fp


def generate_combined_filename(queries: List[str], opts: dict) -> str:
    """Generate a descriptive combined file name.
    
    Args:
        queries: List of query strings to summarize
        opts: Options dictionary with settings
        
    Returns:
        A descriptive filename for the combined results
    """
    if opts.get("output"):
        return os.path.basename(opts["output"])
        
    # If we have a single query and it's short enough, use it directly
    if len(queries) == 1 and len(queries[0]) <= 50:
        clean_name = re.sub(r'[^\w\s-]', '', queries[0]).strip().replace(" ", "_")[:50]
        return f"{clean_name}_combined.md"
        
    # For multiple queries, create a simple descriptive name
    if len(queries) > 1:
        # Get key nouns from each query for the name
        words = []
        for q in queries[:3]:  # Only use first 3 queries
            # Skip common words and get the last meaningful word (often the subject)
            q_words = q.lower().split()
            for w in reversed(q_words):
                w = re.sub(r'[^\w\s-]', '', w)
                if w not in ['what', 'is', 'the', 'a', 'an', 'in', 'of', 'to', 'for', 'and', 'or', 'capital']:
                    if w not in words:
                        words.append(w)
                    break
        
        name = "_".join(words)
        if len(queries) > 3:
            name += f"_and_{len(queries)-3}_more"
        return f"{name}_combined.md"
    
    # Fallback: Use timestamp and number of queries
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"combined_results_{len(queries)}q_{timestamp}.md"


@click.command()
@click.version_option(version=VERSION, prog_name="askp")
@click.argument("query_text", nargs=-1, required=False)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress console output for multiple queries")
@click.option("--format", "-f", type=click.Choice(["text", "json", "markdown"]), default="markdown", help="Output format")
@click.option("--output", "-o", "-O", type=click.Path(), help="Save output to file")
@click.option("--num-results", "-n", type=int, default=5, help="Number of results to return from Perplexity")
@click.option("--model", default="sonar", help="Model to use (default: sonar)")
@click.option("--temperature", type=float, default=0.7, help="Temperature (0.0-1.0)")
@click.option("--token-max", "-t", type=int, default=8192, help="Maximum tokens to use")
@click.option("--reasoning", "-r", is_flag=True, help="Use reasoning model ($5.00 per million tokens)")
@click.option("--pro-reasoning", is_flag=True, help="Use pro reasoning model ($8.00 per million tokens)")
@click.option("--single", "-s", is_flag=True, help="Process all arguments as a single query (default is multi-query mode)")
@click.option("--max-parallel", type=int, default=5, help="Maximum number of parallel queries")
@click.option("--file", "-i", type=click.Path(exists=True), help="Read queries from file, one per line")
@click.option("--combine", "-c", "-C", is_flag=True, help="Combine multi-query results into a single output")
@click.option("--expand", "-e", type=int, help="Expand queries to specified total number by generating related queries")
@click.option("--deep", "-d", is_flag=True, help="Perform deep research by generating a comprehensive research plan")
@click.option("--cleanup-component-files", is_flag=True, help="Move component files to trash after deep research is complete")
def cli(query_text, verbose, quiet, format, output, num_results, model, temperature, token_max, reasoning, pro_reasoning, single, max_parallel, file, combine, expand, deep, cleanup_component_files):
    """ASKP CLI - Search Perplexity AI from the command line"""
    model = normalize_model_name(model)
    if reasoning and pro_reasoning:
        rprint("[red]Error: Cannot use both --reasoning and --pro-reasoning together[/red]")
        sys.exit(1)
    ctx = click.get_current_context()
    token_max_set = "token_max" in ctx.params
    reasoning_set = "reasoning" in ctx.params or "pro_reasoning" in ctx.params
    queries = []
    if file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                queries.extend([l.strip() for l in f if l.strip()])
        except Exception as e:
            rprint(f"[red]Error reading query file: {e}[/red]")
            sys.exit(1)
    if query_text:
        if single:
            queries.append(" ".join(query_text))
        else:
            queries.extend(list(query_text))
    elif not queries and not sys.stdin.isatty():
        queries.extend([l.strip() for l in sys.stdin.read().splitlines() if l.strip()])
    if not queries:
        click.echo(ctx.get_help())
        ctx.exit()
    opts: Dict[str, Any] = {
        "verbose": verbose,
        "quiet": quiet,
        "format": format,
        "output": output,
        "num_results": num_results,
        "model": model,
        "temperature": temperature,
        "max_tokens": token_max,
        "reasoning": reasoning,
        "pro_reasoning": pro_reasoning,
        "combine": combine,
        "max_parallel": max_parallel,
        "token_max_set_explicitly": token_max_set,
        "reasoning_set_explicitly": reasoning_set,
        "output_dir": get_output_dir(),
        "multi": not single,
        "cleanup_component_files": cleanup_component_files,
    }
    if expand:
        opts["expand"] = expand
    if deep:
        if not quiet:
            rprint("[blue]Deep research mode enabled. Generating research plan...[/blue]")
        if not reasoning_set:
            opts["model"] = "sonar-pro"
        if not quiet:
            rprint(f"[blue]Using model: {opts['model']} | Temperature: {opts['temperature']}[/blue]")
        comp_dir = os.path.join(opts["output_dir"], "components")
        os.makedirs(comp_dir, exist_ok=True)
        final_out_dir = opts["output_dir"]
        opts["components_dir"] = comp_dir
        opts["deep"] = True
        opts["cleanup_component_files"] = cleanup_component_files
        opts["query"] = queries[0]
        res = handle_deep_research(queries[0], opts)
        opts["output_dir"] = final_out_dir
        if not res:
            rprint("[red]Error: Failed to process queries[/red]")
            sys.exit(1)
        output_multi_results(res, opts)
    elif expand and expand > len(queries):
        rprint(f"[blue]Expanding {len(queries)} queries to {expand} total queries...[/blue]")
        from .expand import generate_expanded_queries
        queries = generate_expanded_queries(queries, expand, model=model, temperature=temperature)
    elif not single or file or len(queries) > 1:
        res = handle_multi_query(queries, opts)
        if not res:
            rprint("[red]Error: Failed to process queries[/red]")
            sys.exit(1)
        output_multi_results(res, opts)
    else:
        r = execute_query(queries[0], 0, opts)
        if not r:
            rprint("[red]Error: Failed to get response from Perplexity API[/red]")
            sys.exit(1)
        output_result(r, opts)


def main() -> None:
    """Main entry point for the ASKP CLI."""
    cli()


if __name__ == "__main__":
    main()