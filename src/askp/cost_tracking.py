#!/usr/bin/env python3
"""Cost tracking module for ASKP CLI."""
import os
import json
import random
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from itertools import accumulate
from collections import defaultdict

# Don't import matplotlib directly - use lazy loading
# Global flag to check if visualization is available
HAS_MATPLOTLIB = False

# Import models and utils modules that don't depend on matplotlib
from .models import get_model_info, list_models
from .utils import detect_model

COST_LOG_DIR = os.path.expanduser("~/.askp/cost_logs")
COST_LOG_FILE = os.path.join(COST_LOG_DIR, "costs.jsonl")
PROJECT_ROOTS = {"projects", "cascadeprojects", "workspace", "repos", "code"}
NON_PROJECT_DIRS = {"src", "results", "temp", "logs", "data", "tests", "perplexity", "ask", "askd", "askp", "old"}

def _try_import_matplotlib():
    """Try to import matplotlib, return True if successful."""
    global HAS_MATPLOTLIB, plt
    if HAS_MATPLOTLIB:
        return True
        
    try:
        import matplotlib.pyplot as plt
        HAS_MATPLOTLIB = True
        return True
    except ImportError:
        return False
    except Exception as e:
        print(f"Warning: Matplotlib available but error occurred: {e}")
        return False

def ensure_log_dir():
    """Ensure the cost log directory exists."""
    Path(COST_LOG_DIR).mkdir(parents=True, exist_ok=True)

def log_query_cost(query_id: str, token_count: int, cost: float, model: str, project: Optional[str] = None):
    """
    Log the cost of a query to the cost log file.
    
    Args:
        query_id: Identifier for the query (usually a snippet of the query text)
        token_count: Number of tokens used in the query
        cost: Estimated cost of the query
        model: The model used for the query
        project: Optional project name for cost categorization
    """
    ensure_log_dir()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {
        "timestamp": timestamp,
        "model": model,
        "token_count": token_count,
        "cost": cost,
        "query_id": query_id
    }
    if project:
        entry["project"] = project
    
    with open(COST_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    # Only trigger cost analysis when explicitly requested, not randomly
    # This prevents unwanted output during deep research
    # if random.randint(1, 50) == 1:
    #     try:
    #         analyze_costs()
    #     except Exception as e:
    #         print(f"Warning: Cost analysis failed: {e}")

def format_cost(cost: float) -> str:
    """Format a cost value as a dollar amount with appropriate precision."""
    return f"${cost:.2f}" if cost >= 0.1 else f"${cost:.4f}"

def format_number(n: float, precision: Optional[int] = None) -> str:
    """Format a number with commas and appropriate precision."""
    if isinstance(n, int):
        return f"{n:,}"
    if precision is None:
        precision = 2 if n >= 1 else (3 if n >= 0.1 else 4)
    return f"{n:,.{precision}f}"

def estimate_token_count(content: str) -> int:
    """Estimate the number of tokens in a string based on character count and code symbols."""
    code_chars = len(re.findall(r"[{}()\[\]<>+=\-*/\\|;:~`@#$%^&]", content))
    total_chars = len(content)
    ratio = code_chars / total_chars if total_chars else 0
    tokens = int(total_chars / (3.5 if ratio > 0.05 else 4.0)) + code_chars
    return max(1, tokens)

def get_project_from_path(path: str) -> Optional[str]:
    """Attempt to determine project name from a file path."""
    p = Path(path).resolve()
    wd_marker = p / ".working_directory" if p.is_dir() else None
    if wd_marker and wd_marker.exists():
        try:
            return wd_marker.read_text().strip()
        except Exception:
            pass
    for parent in p.parents:
        wd_marker = parent / ".working_directory"
        if wd_marker.exists():
            try:
                return wd_marker.read_text().strip()
            except Exception:
                pass
    parts = p.parts
    for i, part in enumerate(parts):
        if part.lower() in PROJECT_ROOTS and i + 1 < len(parts):
            if parts[i + 1].lower() not in NON_PROJECT_DIRS:
                return parts[i + 1]
    try:
        src_idx = parts.index("src")
        if src_idx > 0:
            return parts[src_idx - 1]
    except ValueError:
        pass
    for i, part in enumerate(parts):
        if "results" in part.lower() and i > 0 and parts[i - 1].lower() not in NON_PROJECT_DIRS:
            return parts[i - 1]
    return None

def format_date(date: datetime) -> str:
    """Format a date as 'Month Day Year'."""
    return date.strftime("%b %d %Y")

def format_date_range(start: datetime, end: datetime) -> str:
    """Format a date range with appropriate detail level based on the range."""
    days = (end.date() - start.date()).days + 1
    dur = f" ({days}D)" if days > 1 else ""
    if start.year != end.year:
        return f"{format_date(start)} - {format_date(end)}{dur}"
    if start.month != end.month:
        return f"{start.strftime('%b %d')} - {format_date(end)}{dur}"
    if start.day != end.day:
        return f"{start.strftime('%b %d')} - {end.day} {end.year}{dur}"
    return f"{format_date(start)}"

def get_ordinal(n: int) -> str:
    """Get the ordinal suffix for a number (1st, 2nd, 3rd, etc.)."""
    return "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

def build_project_tree(projects: Dict[str, Dict]) -> Dict:
    """Build a hierarchical tree of projects."""
    tree = {}
    for project, stats in projects.items():
        parts = project.split("/")
        current = tree
        path = ""
        for part in parts:
            path = f"{path}/{part}" if path else part
            if path not in current:
                current[path] = {
                    "name": part,
                    "full_path": path,
                    "queries": 0,
                    "cost": 0,
                    "timestamps": [],
                    "children": {},
                    "models": set()
                }
            current = current[path]["children"]
            for ancestor in [tree[p] for p in accumulate(parts, lambda x, y: x + "/" + y)]:
                ancestor["queries"] += stats["queries"]
                ancestor["cost"] += stats["cost"]
                ancestor["timestamps"].extend(stats["timestamps"])
                ancestor["models"].update(stats["models"])
    return tree

def print_project_tree(node: Dict, level: int = 0, show_empty: bool = False):
    if node["queries"] > 0 or show_empty:
        indent = "  " * level
        dr = (format_date_range(datetime.fromtimestamp(min(node["timestamps"])), datetime.fromtimestamp(max(node["timestamps"])))
              if node["timestamps"] else "No activity")
        print(f"{indent}{node['name']:<30} {format_number(node['queries']):>8}    ${format_number(node['cost']):>8}    {dr}")
    for child in sorted(node["children"].values(), key=lambda x: x["cost"], reverse=True):
        print_project_tree(child, level + 1, show_empty)

def load_cost_data() -> List[Dict]:
    if not os.path.exists(COST_LOG_FILE):
        return []
    with open(COST_LOG_FILE, "r") as f:
        return [json.loads(line) for line in f]

def plot_monthly_costs(cost_data: List[Dict], output_path: str):
    """Plot monthly costs to a file."""
    if not _try_import_matplotlib():
        print("Warning: Matplotlib not available, skipping plot.")
        return
        
    monthly = defaultdict(float)
    for entry in cost_data:
        month = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m")
        monthly[month] += entry["cost"]
    months = sorted(monthly.keys())
    costs = [monthly[m] for m in months]
    plt.figure(figsize=(12, 6))
    plt.bar(months, costs)
    plt.title("Monthly Costs")
    plt.xlabel("Month")
    plt.ylabel("Cost ($)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_daily_costs(cost_data: List[Dict], days: int, output_path: str):
    """Plot daily costs for the last N days to a file."""
    if not _try_import_matplotlib():
        print("Warning: Matplotlib not available, skipping plot.")
        return
        
    now = datetime.now()
    daily = defaultdict(float)
    for entry in cost_data:
        d = datetime.fromisoformat(entry["timestamp"])
        if (now - d).days <= days:
            daily[d.strftime("%Y-%m-%d")] += entry["cost"]
    d_keys = sorted(daily.keys())[-days:]
    costs = [daily[d] for d in d_keys]
    plt.figure(figsize=(12, 6))
    plt.bar(d_keys, costs)
    plt.title(f"Daily Costs (Last {len(d_keys)} Days)")
    plt.xlabel("Date")
    plt.ylabel("Cost ($)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def analyze_costs(only_period: Optional[str] = None, by_project: bool = False, current_project: Optional[str] = None, tree_view: bool = False):
    ensure_log_dir()
    cost_data = load_cost_data()
    if not cost_data:
        print("\nNo cost data found.")
        return
    cost_data.sort(key=lambda x: x["timestamp"])
    if only_period:
        now = datetime.now()
        cutoff = {"day": now - timedelta(days=1), "week": now - timedelta(weeks=1), "month": now - timedelta(days=30)}.get(only_period, datetime.min)
        cost_data = [e for e in cost_data if datetime.fromisoformat(e["timestamp"]) > cutoff]
    if not cost_data:
        print(f"\nNo cost data found for period: {only_period}")
        return
    total_cost = sum(e["cost"] for e in cost_data)
    total_tokens = sum(e["token_count"] for e in cost_data)
    start_date = datetime.fromisoformat(cost_data[0]["timestamp"])
    end_date = datetime.fromisoformat(cost_data[-1]["timestamp"])
    print("\nCost Analysis")
    print(f"\nPeriod: {format_date_range(start_date, end_date)}")
    print(f"Total Cost: {format_cost(total_cost)}")
    print(f"Total Tokens: {format_number(total_tokens)}")
    print(f"Average Cost per Query: {format_cost(total_cost/len(cost_data))}")
    model_stats = defaultdict(lambda: {"cost": 0, "tokens": 0, "count": 0})
    for entry in cost_data:
        m = entry["model"]
        model_stats[m]["cost"] += entry["cost"]
        model_stats[m]["tokens"] += entry["token_count"]
        model_stats[m]["count"] += 1
    print("\nModel Usage:")
    for m, s in sorted(model_stats.items(), key=lambda x: x[1]["cost"], reverse=True):
        print(f"\n{m}:")
        print(f"  Cost: {format_cost(s['cost'])} ({(s['cost']/total_cost*100):.1f}%)")
        print(f"  Tokens: {format_number(s['tokens'])}")
        print(f"  Queries: {s['count']}")
        print(f"  Average Cost per Query: {format_cost(s['cost']/s['count'])}")
    if by_project:
        proj_stats = defaultdict(lambda: {"cost": 0, "tokens": 0, "count": 0})
        for entry in cost_data:
            p = entry.get("project", "unknown")
            proj_stats[p]["cost"] += entry["cost"]
            proj_stats[p]["tokens"] += entry["token_count"]
            proj_stats[p]["count"] += 1
        if tree_view:
            projects = {p: {"cost": s["cost"], "tokens": s["tokens"], "count": s["count"], "children": {}} for p, s in proj_stats.items()}
            tree = build_project_tree(projects)
            print("\nProject Costs (Tree View):")
            print_project_tree(tree)
        else:
            print("\nProject Costs:")
            for p, s in sorted(proj_stats.items(), key=lambda x: x[1]["cost"], reverse=True):
                if current_project and p != current_project:
                    continue
                print(f"\n{p}:")
                print(f"  Cost: {format_cost(s['cost'])} ({(s['cost']/total_cost*100):.1f}%)")
                print(f"  Tokens: {format_number(s['tokens'])}")
                print(f"  Queries: {s['count']}")
                print(f"  Average Cost per Query: {format_cost(s['cost']/s['count'])}")