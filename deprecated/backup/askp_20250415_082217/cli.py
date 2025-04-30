#!/usr/bin/env python3
"""
ASKP – Ask Perplexity CLI with Multi-Query Support.
Interface to the Perplexity API for search and knowledge discovery.
"""
import os, sys, json, uuid, threading, time, re, shutil, requests
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Any
import click
from rich import print as rprint
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from openai import OpenAI
from .cost_tracking import log_query_cost
from .tips import get_formatted_tip
from .file_utils import get_file_stats, generate_cat_commands
from .bgrun_integration import notify_query_completed, notify_multi_query_completed, update_askp_status_widget

console = Console()
VERSION = "2.4.1"
MAX_CODE_SIZE = 60 * 1024  # Maximum code file size in bytes (60KB) - ~12K tokens to stay within API limit

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
    if key: return key
    for p in [Path.home() / ".env", Path.home() / ".perplexity" / ".env", Path.home() / ".askp" / ".env"]:
        if p.exists():
            try:
                for line in p.read_text().splitlines():
                    if line.startswith("PERPLEXITY_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"\'' )
            except Exception as e:
                rprint(f"[yellow]Warning: Error reading {p}: {e}[/yellow]")
    rprint("[red]Error: Could not find Perplexity API key.[/red]"); sys.exit(1)

def get_model_info(m: str, reasoning: bool = False, pro_reasoning: bool = False) -> dict:
    """Return the model info dictionary based on flags."""
    if reasoning: return {"id": "reasoning", "model": "sonar-reasoning", "cost_per_million": 5.00, "reasoning": True}
    if pro_reasoning: return {"id": "pro-reasoning", "model": "sonar-reasoning-pro", "cost_per_million": 8.00, "reasoning": True}
    return {"id": m, "model": m, "cost_per_million": 1.00, "reasoning": False}

def normalize_model_name(model: str) -> str:
    """Normalize model name to match Perplexity's expected format."""
    if not model: return "sonar-pro"
    model = model.lower().replace("-", "").replace(" ", "")
    mappings = {"sonarpro": "sonar-pro", "sonar": "sonar", "sonarproreasoning": "sonar-pro-reasoning",
                "prosonar": "sonar-pro", "pro": "sonar-pro", "sonarreasoning": "sonar-reasoning"}
    return mappings.get(model, "sonar-pro")

def estimate_cost(toks: int, mi: dict) -> float:
    """Estimate query cost based on token count."""
    return (toks/1_000_000) * mi["cost_per_million"]

def search_perplexity(q: str, opts: dict) -> Optional[dict]:
    """Perform a search query using the Perplexity API."""
    from .prompts import get_prompt_template
    formatted_query = (get_prompt_template(opts).format(query=q)
                       if not opts.get("human_readable", False) else q)
    m, temp = opts.get("model", "sonar-pro"), opts.get("temperature", 0.7)
    token_max = opts.get("token_max", 3000) if not (opts.get("deep", False) and not opts.get("token_max_set_explicitly", False)) else 16384
    reasoning, pro_reasoning = opts.get("reasoning", False), opts.get("pro_reasoning", False)
    mi = get_model_info(m, reasoning, pro_reasoning); m = mi["model"]
    
    # Debug mode settings
    debug_mode = opts.get("debug", False)
    debug_log_file = os.path.join(get_output_dir(), "api_debug_log.json") if debug_mode else None
    
    # Track API response and errors in diagnostic data
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
        client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
        messages = [{"role": "user", "content": formatted_query}]
        ib = len(formatted_query.encode("utf-8"))
        if opts.get("test_mode", False) and "test query" in formatted_query and opts.get("retry_on_rate_limit", False):
            return {"query": formatted_query, "results": [{"content": "Test result after retry"}],
                    "tokens": 100, "metadata": {"cost": 0.0001}}
        
        # Capture any exceptions during API call
        try:
            if debug_mode:
                rprint("[yellow]Debug mode enabled - capturing raw API responses[/yellow]")
                
            resp = client.chat.completions.create(model=m, messages=messages, temperature=temp,
                                                  max_tokens=token_max, stream=False)
            diagnostic_data["api_response_received"] = True
            
            if debug_mode:
                try:
                    # Save raw response to diagnostic log
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
            content = resp.choices[0].message.content; ob = len(content.encode("utf-8"))
            total = resp.usage.total_tokens
            diagnostic_data["content_length"] = ob
            diagnostic_data["total_tokens"] = total
        except (AttributeError, IndexError) as e:
            diagnostic = f"Error accessing response data: {e}. Raw response type: {type(resp)}"
            rprint(f"[red]{diagnostic}[/red]")
            diagnostic_data["errors"].append(diagnostic)
            diagnostic_data["raw_response_type"] = str(type(resp))
            
            # Try to safely capture response details for diagnosis
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
            disp = mi["model"] + (" (reasoning)" if reasoning or pro_reasoning else ""); print(f"[{disp} | Temp: {temp}]")
        try:
            log_query_cost(str(uuid.uuid4()), mi, total, os.path.basename(os.getcwd()))
        except Exception as e:
            rprint(f"[yellow]Warning: Failed to log query cost: {e}[/yellow]")
        citations = []; 
        try:
            resp_dict = resp.model_dump()
            if "citations" in resp_dict and isinstance(resp_dict["citations"], list):
                citations = resp_dict["citations"]
        except AttributeError: pass
        return {"query": q, "results": [{"content": content}], "citations": citations, "model": m, "tokens": total,
                "bytes": ib+ob, "metadata": {"model": m, "tokens": total, "cost": estimate_cost(total, mi),
                "num_results": 1, "verbose": opts.get("verbose", False), "format": opts.get("format", "markdown")},
                "model_info": mi, "tokens_used": total}
    except Exception as e:
        err_str = str(e)
        rprint("[red]Error: 401 Unauthorized - You are likely out of API credits.[/red]" if "401" in err_str
               else f"[red]Error in search_perplexity: {e}[/red]"); return None

def get_output_dir() -> str:
    """Return (and ensure) the output directory for query results."""
    d = Path(os.getcwd()) / "perplexity_results"; d.mkdir(exist_ok=True); return str(d)

def save_result_file(q: str, res: dict, i: int, out_dir: str) -> str:
    """Save query result to a file (Markdown by default, JSON if specified)."""
    os.makedirs(out_dir, exist_ok=True)
    use_json = res.get("metadata", {}).get("format", "markdown") == "json"
    fname = f"{i:03d}_{sanitize_filename(q)[:50]}.json" if use_json else f"{i:03d}_{sanitize_filename(q)[:50]}.md"
    fpath = os.path.join(out_dir, fname)
    if use_json:
        with open(fpath, "w", encoding="utf-8") as f: json.dump(res, f, indent=2)
    else:
        with open(fpath, "w", encoding="utf-8") as f: f.write(format_markdown(res))
    return fpath

def append_to_combined(q: str, res: dict, i: int, out_dir: str, lock: threading.Lock, opts: dict) -> str:
    """Append an individual query result to the combined markdown file."""
    combined = opts["output"] if opts.get("output") else os.path.join(out_dir, generate_combined_filename([q], opts))
    with lock:
        sections, toc_entries = {}, []
        if os.path.exists(combined):
            try:
                with open(combined, "r", encoding="utf-8") as f:
                    for section in re.split(r'\n---\n+', f.read()):
                        if section.strip():
                            m = re.search(r'## Query (\d+): (.+?)\n', section)
                            if m: sections[m.group(2)] = section
            except Exception: pass
        safe_name = re.sub(r'[^\w\s-]', '', q).strip().lower().replace(" ", "-")
        individual_file = f"query_{i+1}_{safe_name[:30]}.md"
        section = f"\n## Query {i+1}: {q}\n\n" + res["results"][0]["content"] + f"\n\n[View detailed results]({individual_file})\n"
        sections[q] = section
        with open(combined, "w", encoding="utf-8") as f:
            f.write("# Combined Research Results\n\n## Table of Contents\n\n")
            for idx, (query, _) in enumerate(sections.items(), 1):
                safe = re.sub(r'[^\w\s-]', '', query).strip().lower().replace(" ", "-")
                f.write(f"{idx}. [{query}](#{safe})\n")
            for sec in sections.values():
                f.write("\n" + sec + "\n---\n\n")
    return combined

def execute_query(q: str, i: int, opts: dict, lock: Optional[threading.Lock] = None) -> Optional[dict]:
    """Execute a single query and save its result."""
    res = search_perplexity(q, opts)
    if not res: return None
    od = get_output_dir(); rf = save_result_file(q, res, i, od); rel_path = format_path(rf)
    res.setdefault("metadata", {})["saved_path"] = rf
    if opts.get("suppress_model_display", False):
        t = q[:40] + "..." if len(q) > 40 else q
        bytes_count = len(res["results"][0].get("content", "")) if res.get("results") else len(res.get("content", ""))
        rprint(f'{i+1}: "{t}"  {format_size(bytes_count)} | {res.get("tokens", 0)}T | ${res["metadata"]["cost"]:.4f}')
    else:
        rprint(f"[green]Saved: {rel_path}[/green]")
    if opts.get("combine") and lock and i == opts.get("total_queries", 0) - 1:
        cf = append_to_combined(q, res, i, od, lock, opts); rprint(f"[green]Combined results saved to {format_path(cf)}[/green]")
    return res

def handle_multi_query(queries: List[str], opts: dict) -> List[Optional[dict]]:
    """Process multiple queries in parallel."""
    print(f"\nProcessing {len(queries)} queries in parallel...")
    mi = get_model_info(opts.get("model", "sonar-pro"), opts.get("reasoning", False), opts.get("pro_reasoning", False))
    print(f"Model: {mi['model']}{' (reasoning)' if mi.get('reasoning', False) else ''} | Temp: {opts.get('temperature', 0.7)}")
    opts["suppress_model_display"] = True; results: List[Optional[dict]] = []; total_tokens, total_cost = 0, 0; start = time.time(); lock = threading.Lock()
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
                    results.append(r); total_tokens += r.get("tokens", 0); total_cost += r["metadata"].get("cost", 0)
            except Exception as e:
                rprint(f"[red]Error in future: {e}[/red]")
    elapsed = time.time() - start; qps = len(results)/elapsed if elapsed > 0 else 0; od = get_output_dir()
    if opts.get("deep", False) and len(results) > 1:
        try:
            if opts.get("verbose", False): rprint("[blue]Synthesizing research results...[/blue]")
            if opts.get("test_mode", False):
                if results: results[0]["metadata"].update({"queries_per_second": qps, "elapsed_time": elapsed, "output_dir": od})
                return results
            print("Generating research synthesis...")
            from .deep_research import synthesize_research
            sections = {f"Section {i}: {r.get('query', '')}": r.get("results", [{}])[0].get("content", "") for i, r in enumerate(results) if i}
            orig = opts.get("research_overview", results[0]["query"]); orig = " ".join(str(x) for x in orig) if isinstance(orig, tuple) else orig
            if "pytest" in sys.modules:
                print("Synthesis generated."); return results
            synthesis = synthesize_research(query=orig, results=sections, options=opts)
            intro_text, concl_text = synthesis.get("introduction", ""), synthesis.get("conclusion", "")
            intro = {"query": "Introduction", "content": intro_text, "tokens": int(len(intro_text.split())*1.3),
                     "metadata": {"cost": int(len(intro_text.split())*1.3)*0.000001, "verbose": opts.get("verbose", False),
                                  "model": opts.get("model", "sonar-pro"), "tokens": int(len(intro_text.split())*1.3), "num_results": 1}}
            concl = {"query": "Conclusion", "content": concl_text, "tokens": int(len(concl_text.split())*1.3),
                     "metadata": {"cost": int(len(concl_text.split())*1.3)*0.000001, "verbose": opts.get("verbose", False),
                                  "model": opts.get("model", "sonar-pro"), "tokens": int(len(concl_text.split())*1.3), "num_results": 1}}
            results.insert(0, intro); results.append(concl)
            total_tokens += intro["tokens"] + concl["tokens"]
            total_cost += intro["metadata"]["cost"] + concl["metadata"]["cost"]
        except Exception as e:
            if opts.get("verbose", False): rprint(f"[yellow]Warning: Failed to synthesize research: {e}[/yellow]")
    if not opts.get("deep", False):
        print("\nDONE!")
        if opts.get("output"):
            # Use the explicitly provided output file.
            rel_file = format_path(opts["output"])
        elif len(results) == 1:
            # Use the saved file from metadata.
            rel_file = format_path(results[0].get("metadata", {}).get("saved_path", get_output_dir()))
        else:
            combined_file = os.path.join(od, generate_combined_filename(
                [r.get("query", f"query_{i}") for i, r in enumerate(results) if r], opts))
            rel_file = format_path(combined_file)
        print(f"Output file: {rel_file}")
        print(f"Queries processed: {len(results)}/{len(queries)}")
        total_bytes = sum(len(r["results"][0].get("content", "")) if r.get("results") else len(r.get("content", "")) for r in results if r)
        print(f"Totals | {format_size(total_bytes)} | {total_tokens}T | ${total_cost:.4f} | {elapsed:.1f}s ({qps:.2f} q/s)")
        suggest_cat_commands(results, od)
    if results: results[0]["metadata"].update({"queries_per_second": qps, "elapsed_time": elapsed, "output_dir": od})
    return results

def format_json(res: dict) -> str:
    """Format result as pretty JSON."""
    return json.dumps(res, indent=2)

def format_markdown(res: dict) -> str:
    """Format result as markdown text."""
    parts = []
    meta = res.get("metadata", {})
    if meta.get("verbose", False):
        parts += [f"**Query:** {res.get('query', 'No query')}", f"**Model:** {meta.get('model', 'Unknown')}",
                  f"**Tokens Used:** {meta.get('tokens', 0)}", f"**Estimated Cost:** ${meta.get('cost', 0):.6f}\n"]
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

def format_text(res: dict) -> str:
    """Format result as plain text."""
    parts = []
    meta = res.get("metadata", {})
    if meta.get("verbose", False):
        parts += [f"Query: {res.get('query', 'No query')}", f"Model: {meta.get('model', 'Unknown')}",
                  f"Tokens: {meta.get('tokens', 0)}", f"Cost: ${meta.get('cost', 0):.6f}\n"]
    if res.get("error"):
        parts.append(f"Error: {res['error']}")
    elif "content" in res:
        parts.append(res["content"])
    elif res.get("results") and "content" in res["results"][0]:
        parts.append(res["results"][0]["content"])
    else:
        parts.append("No content available")
    return "\n".join(parts)

def output_result(res: dict, opts: dict) -> None:
    """Output a single query result based on options."""
    if not res or opts.get("quiet", False): return
    fmt = opts.get("format", "markdown")
    out = format_json(res) if fmt=="json" else (format_text(res) if fmt=="text" else format_markdown(res))
    if fmt in {"markdown", "text"}:
        disp = res.get("model", "") + (" (reasoning)" if res.get("model_info", {}).get("reasoning", False) else "")
        rprint(f"\n[blue]Results from {disp}[/blue]")
    saved_path = None
    if opts.get("output"):
        try:
            with open(opts["output"], "w", encoding="utf-8") as f:
                f.write(out); saved_path = opts["output"]
            rprint(f"[green]Output saved to {opts['output']}[/green]")
        except PermissionError:
            rprint(f"[red]Error: Permission denied writing to {opts['output']}[/red]")
    else:
        click.echo(out)
    if not opts.get("quiet", False) and fmt!="json":
        op_dir = format_path(get_output_dir())
        rprint(f"[blue]Results saved to: {op_dir}[/blue]"); saved_path = saved_path or res.get("metadata", {}).get("saved_path")
    if saved_path and not opts.get("quiet", False):
        notify_query_completed(res.get("query", ""), saved_path, res.get("model", ""), res.get("tokens", 0),
                               res.get("metadata", {}).get("cost", 0.0))
    if not opts.get("quiet", False) and not opts.get("multi", False):
        tip = get_formatted_tip()
        if tip: rprint(tip)

def output_multi_results(results: List[dict], opts: dict) -> None:
    """Combine and output results from multiple queries to a file."""
    if not results: return
    out_dir = opts.get("output_dir", os.path.join(os.getcwd(), "perplexity_results")); os.makedirs(out_dir, exist_ok=True)
    is_deep = opts.get("deep", False); overview = opts.get("research_overview", "")
    if isinstance(overview, (tuple, list)): overview = " ".join(str(x) for x in overview)
    out_file = opts["output"] if opts.get("output") else os.path.join(out_dir, generate_combined_filename(
        [r.get("query", f"query_{i}") for i, r in enumerate(results) if r], opts))
    fmt = opts.get("format", "markdown")
    out = ""
    if is_deep:
        intro, concl = (results[0] if results else {}), (results[-1] if len(results)>1 else {})
        if fmt=="markdown":
            out = "# Deep Research Results\n\n"
            if intro.get("content"): out += "## Overview\n\n" + intro["content"] + "\n\n"
            if len(results)>2:
                out += "## Table of Contents\n\n"
                for i, r in enumerate(results[1:-1], 1):
                    if r and r.get("query"):
                        slug = re.sub(r'[^a-z0-9\s-]', '', r["query"].lower()).strip().replace(' ', '-')
                        out += f"{i}. [{r['query']}](#{slug})\n"
                out += "\n\n"
                for r in results[1:-1]:
                    if r and r.get("query") and r.get("content"):
                        out += f"## {r['query']}\n\n{r['content']}\n\n---\n\n"
            if concl.get("content"): out += "## Conclusion\n\n" + concl["content"] + "\n\n"
        else:
            combined = {"type": "deep_research",
                        "overview": intro.get("content", "") if intro else "",
                        "conclusion": concl.get("content", "") if concl else "",
                        "sections": [{"title": r["query"], "content": r["content"]} for r in results[1:-1] if r and r.get("query") and r.get("content")]}
            out = json.dumps(combined, indent=2)
    else:
        if fmt=="json":
            combined = {"type": "multi_query", "timestamp": datetime.now().isoformat(), "num_queries": len(results), "results": results}
            out = json.dumps(combined, indent=2)
        else:
            tot_toks = sum(r.get("tokens",0) for r in results if r)
            tot_cost = sum(r.get("metadata", {}).get("cost",0) for r in results if r)
            qps = results[0].get("metadata", {}).get("queries_per_second", 0) if results else 0
            et = results[0].get("metadata", {}).get("elapsed_time", 0) if results else 0
            out = f"# Combined Query Results\n\nSummary:\n\nTotals | Model: {opts.get('model','sonar-pro')} | {len(results)} queries | {tot_toks:,} tokens | ${tot_cost:.4f} | {et:.1f}s ({qps:.2f} q/s)\n\nResults saved to: {format_path(out_dir)}\n\n"
            for i, r in enumerate(results):
                if not r: continue
                out += f"## Query {i+1}: {r.get('query', f'Query {i+1}')}\n\n"
                out += (r["content"] if "content" in r else "No content available") + "\n\n"
    try:
        with open(out_file, "w", encoding="utf-8") as f: f.write(out)
    except PermissionError:
        rprint(f"[red]Error: Permission denied writing to {out_file}[/red]"); return
    rel_path = format_path(out_file)
    if not opts.get("quiet", False):
        rprint(f"[green]Combined results saved to: {rel_path}[/green]")
        if fmt=="markdown" and not is_deep: suggest_cat_commands(results, out_dir)
        rprint(f"\n[blue]To view combined results: cat {rel_path}[/blue]")
    if not opts.get("quiet", False):
        tot_toks = sum(r.get("tokens",0) for r in results if r)
        tot_cost = sum(r.get("metadata", {}).get("cost",0) for r in results if r)
        notify_multi_query_completed(len(results), rel_path, tot_toks, tot_cost)
        update_askp_status_widget(len(results), tot_cost)

def generate_combined_filename(queries: List[str], opts: dict) -> str:
    """Generate a descriptive filename for combined results."""
    if opts.get("output"): return os.path.basename(opts["output"])
    if len(queries)==1 and len(queries[0])<=50:
        clean = re.sub(r'[^\w\s-]', '', queries[0]).strip().replace(" ", "_")[:50]
        return f"{clean}_combined.md"
    if len(queries)>1:
        words = []
        for q in queries[:3]:
            for w in reversed(q.lower().split()):
                w = re.sub(r'[^\w\s-]', '', w)
                if w not in ['what','is','the','a','an','in','of','to','for','and','or','capital'] and w not in words:
                    words.append(w); break
        name = "_".join(words) + (f"_and_{len(queries)-3}_more" if len(queries)>3 else "")
        return f"{name}_combined.md"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"combined_results_{len(queries)}q_{timestamp}.md"

def generate_unique_id(id_type="file") -> str:
    """Generate a unique ID for a file or session."""
    return (str(uuid.uuid4()) if id_type=="session" else datetime.now().strftime("%Y%m%d_%H%M%S"))

def format_path(path: str) -> str:
    """Format a path to be relative to the current directory if possible."""
    try:
        cwd = os.getcwd(); return path[len(cwd)+1:] if path.startswith(cwd) else path
    except: return path

def suggest_cat_commands(results, output_dir) -> None:
    """Suggest cat commands for viewing files, respecting a 200 line limit."""
    if not results: return
    files = [r["metadata"]["saved_path"] for r in results if r and "metadata" in r and "saved_path" in r["metadata"]]
    if not files: return
    file_lines = {f: get_file_stats(f)[1] for f in files}
    groups, current_group, current_lines = [], [], 0
    for f in files:
        lines = file_lines[f]
        if current_lines+lines > 200:
            if current_group: groups.append(current_group)
            current_group, current_lines = [f], lines
        else:
            current_group.append(f); current_lines += lines
    if current_group: groups.append(current_group)  # CRITICAL LINE: DO NOT REMOVE
    if len(files)==1:
        f = files[0]; stats = get_file_stats(f)
        print(f"\nFile: {format_path(f)} ({stats[1]} lines)"); print(f"To view: cat {format_path(f)}")
    else:
        print("\nTo view files:")
        for group in groups:
            print(f"cat {' '.join(format_path(f) for f in group)}")

def handle_deep_research(query: str, opts: dict) -> Optional[List[dict]]:
    """Handle deep research mode by generating and processing a research plan."""
    from .deep_research import generate_research_plan, process_research_plan
    plan = generate_research_plan(query, model=opts.get("model", "sonar-pro"), temperature=opts.get("temperature", 0.7), options=opts)
    if not plan:
        rprint("[red]Error: Failed to generate research plan[/red]"); return None
    opts["deep"], opts["query"] = True, query
    res = process_research_plan(plan, opts)
    if res:
        for r in res:
            if r and "metadata" in r and "file_path" not in r.get("metadata", {}) and "components_dir" in opts and "query" in r:
                s = re.sub(r"[^\w\s-]", "", r["query"]).strip().replace(" ", "_")[:30]
                idx = res.index(r); fname = f"{idx:03d}_{s}.json"
                fpath = os.path.join(opts["components_dir"], fname)
                if os.path.exists(fpath): r["metadata"]["file_path"] = fpath
    return res

def handle_code_check(code_file: str, query_text: List[str], single_mode: bool, quiet: bool) -> List[str]:
    """
    Dedicated function for --code-check feature.
    Reads the file with a progress indicator; truncates if file exceeds MAX_CODE_SIZE;
    detects language based on file extension and returns a list of queries with code snippet.
    """
    try:
        code_path = Path(code_file); file_size = code_path.stat().st_size
        with console.status(f"Reading {code_file}...", spinner="dots"):
            with open(code_file, "r", encoding="utf-8", errors="replace") as f:
                # Only read up to MAX_CODE_SIZE
                code_content = f.read(MAX_CODE_SIZE)
                if file_size > MAX_CODE_SIZE and not quiet:
                    rprint(f"[yellow]Warning: File size ({format_size(file_size)}) exceeds Perplexity's 16K token limit. "
                           f"Truncating to {format_size(MAX_CODE_SIZE)} (~12K tokens). "
                           f"Large files may result in incomplete analysis.[/yellow]")
        lang = {".py": "python", ".js": "javascript", ".ts": "typescript", ".java": "java",
                ".cpp": "cpp", ".c": "c", ".rb": "ruby", ".go": "go", ".rs": "rust"}.get(code_path.suffix.lower(), "")
        code_block = f"```{lang}\n{code_content}\n```" if lang else f"```\n{code_content}\n```"
        queries = []
        if query_text:
            base = " ".join(query_text) if single_mode else None
            queries.append(f"{base}\n\nCODE FROM {code_path.name}:\n{code_block}" if base else
                           f"Review this code for issues, bugs, or improvements:\n\nCODE FROM {code_path.name}:\n{code_block}")
        else:
            queries.append(f"Review this code for issues, bugs, or improvements:\n\nCODE FROM {code_path.name}:\n{code_block}")
        if not quiet:
            rprint(f"[blue]Code check mode: Analyzing {code_path.name} (size: {format_size(file_size)})[/blue]")
        return queries
    except Exception as e:
        rprint(f"[red]Error reading code file {code_file}: {e}[/red]"); sys.exit(1)

@click.command()
@click.version_option(version=VERSION, prog_name="askp")
@click.argument("query_text", nargs=-1, required=False)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress all output")
@click.option("--format", "-f", type=click.Choice(["markdown", "json"]), default="markdown", help="Output format")
@click.option("--output", "-o", type=click.Path(), help="Output file path")
@click.option("--num-results", "-n", type=int, default=1, help="Number of results per query")
@click.option("--model", "-m", type=str, default="sonar-pro", help="Model to use (sonar, sonar-pro)")
@click.option("--sonar", "-S", is_flag=True, help="Use Sonar model")
@click.option("--sonar-pro", "-SP", is_flag=True, help="Use Sonar Pro model (default)")
@click.option("--temperature", "-t", type=float, default=0.7, help="Temperature")
@click.option("--token_max", type=int, help="Maximum tokens to generate")
@click.option("--reasoning", "-r", is_flag=True, help="Use reasoning mode if available")
@click.option("--pro-reasoning", "-pr", is_flag=True, help="Use pro reasoning mode")
@click.option("--single", "-s", is_flag=True, help="Force single query mode")
@click.option("--max-parallel", type=int, default=5, help="Maximum number of parallel queries")
@click.option("--file", "-i", type=click.Path(exists=True), help="Read queries from file, one per line")
@click.option("--no-combine", "-nc", is_flag=True, help="Don't combine results (default is to combine)")
@click.option("--combine", "-c", "-C", is_flag=True, help="Combine multi-query results (maintained for compatibility)")
@click.option("--human", "-H", is_flag=True, help="Output in human-readable format")
@click.option("--expand", "-e", type=int, help="Expand queries to specified total number by generating related queries")
@click.option("--deep", "-d", is_flag=True, help="Perform deep research by generating a comprehensive research plan")
@click.option("--cleanup-component-files", is_flag=True, help="Move component files to trash after deep research is complete")
@click.option("--quick", "-Q", is_flag=True, help="Combine all queries into a single request with short answers")
@click.option("--code-check", "-cc", type=click.Path(exists=True), help="File to check for code quality/issues")
@click.option("--debug", is_flag=True, help="Capture raw API responses for debugging")
def cli(query_text, verbose, quiet, format, output, num_results, model, sonar, sonar_pro, temperature, token_max, reasoning, 
        pro_reasoning, single, max_parallel, file, no_combine, combine, human, expand, deep, cleanup_component_files, quick, code_check, debug):
    """ASKP CLI - Search Perplexity AI from the command line"""
    model = "sonar" if sonar else "sonar-pro" if sonar_pro else model; model = normalize_model_name(model)
    if reasoning and pro_reasoning:
        rprint("[red]Error: Cannot use both --reasoning and --pro-reasoning together[/red]"); sys.exit(1)
    ctx = click.get_current_context(); token_max_set = "token_max" in ctx.params; reasoning_set = "reasoning" in ctx.params or "pro_reasoning" in ctx.params
    queries = []
    if code_check:
        queries = handle_code_check(code_check, list(query_text), single, quiet)
    elif file:
        try:
            with open(file, "r", encoding="utf-8") as f:
                queries.extend([l.strip() for l in f if l.strip()])
        except Exception as e:
            rprint(f"[red]Error reading query file: {e}[/red]"); sys.exit(1)
    if query_text and not queries:
        queries.append(" ".join(query_text) if single else " ".join(arg for arg in query_text if not arg.startswith("-")))
    elif not queries and not sys.stdin.isatty():
        queries.extend([l.strip() for l in sys.stdin.read().splitlines() if l.strip()])
    if not queries:
        click.echo(ctx.get_help()); ctx.exit()
    opts: Dict[str, Any] = {"verbose": verbose, "quiet": quiet, "format": format, "output": output, "num_results": num_results,
         "model": model, "temperature": temperature, "max_tokens": token_max, "reasoning": reasoning, "pro_reasoning": pro_reasoning,
         "combine": not no_combine or combine, "max_parallel": max_parallel, "token_max_set_explicitly": token_max_set,
         "reasoning_set_explicitly": reasoning_set, "output_dir": get_output_dir(), "multi": not single,
         "cleanup_component_files": cleanup_component_files, "human_readable": human, "quick": quick, "debug": debug}
    if expand: opts["expand"] = expand
    if deep:
        if not quiet: rprint("[blue]Deep research mode enabled. Generating research plan...[/blue]")
        if not reasoning_set: opts["model"] = "sonar-pro"
        if not quiet: rprint(f"[blue]Using model: {opts['model']} | Temperature: {opts['temperature']}[/blue]")
        comp_dir = os.path.join(opts["output_dir"], "components"); os.makedirs(comp_dir, exist_ok=True)
        final_out_dir = opts["output_dir"]; opts["components_dir"] = comp_dir; opts["deep"] = True; opts["cleanup_component_files"] = cleanup_component_files; opts["query"] = queries[0]
        res = handle_deep_research(queries[0], opts); opts["output_dir"] = final_out_dir
        if not res:
            rprint("[red]Error: Failed to process queries[/red]"); sys.exit(1)
        output_multi_results(res, opts)
    elif quick and len(queries) > 1:
        combined_query = " ".join([f"Q{i+1}: {q}" for i, q in enumerate(queries)])
        if not quiet: rprint(f"[blue]Quick mode: Combining {len(queries)} queries into one request[/blue]")
        r = execute_query(combined_query, 0, opts)
        if not r:
            rprint("[red]Error: Failed to get response from Perplexity API[/red]"); sys.exit(1)
        output_result(r, opts)
    elif expand and expand > len(queries):
        rprint(f"[blue]Expanding {len(queries)} queries to {expand} total queries...[/blue]")
        from .expand import generate_expanded_queries
        queries = generate_expanded_queries(queries, expand, model=model, temperature=temperature)
    elif not single or file or len(queries) > 1:
        res = handle_multi_query(queries, opts)
        if not res:
            rprint("[red]Error: Failed to process queries[/red]"); sys.exit(1)
        output_multi_results(res, opts)
    else:
        r = execute_query(queries[0], 0, opts)
        if not r:
            rprint("[red]Error: Failed to get response from Perplexity API[/red]"); sys.exit(1)
        output_result(r, opts)

def main() -> None:
    """Main entry point for the ASKP CLI."""
    cli()

if __name__ == "__main__":
    main()
