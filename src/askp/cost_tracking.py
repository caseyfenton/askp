#!/usr/bin/env python3
"""Cost tracking module for ASKP CLI."""
import os, json, random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from itertools import accumulate
import matplotlib.pyplot as plt
from collections import defaultdict
from .models import get_model_info, list_models
from .utils import detect_model

COST_LOG_DIR = os.path.expanduser("~/.askp/cost_logs")
COST_LOG_FILE = os.path.join(COST_LOG_DIR, "costs.jsonl")

def ensure_log_dir():
    Path(COST_LOG_DIR).mkdir(parents=True, exist_ok=True)

def log_query_cost(query_id: str, model_info: Dict, token_count: int, project: Optional[str] = None):
    ensure_log_dir(); cost = (token_count / 1_000_000) * model_info["cost_per_million"]
    entry = {"timestamp": datetime.now().isoformat(), "model": model_info["id"], "token_count": token_count, "cost": cost, "query_id": query_id}
    if project: entry["project"] = project
    with open(COST_LOG_FILE, "a") as f: f.write(json.dumps(entry) + "\n")
    if random.randint(1,50)==1: analyze_costs()

def format_cost(cost: float) -> str:
    return f"${cost:.2f}" if cost >= 0.1 else f"${cost:.4f}"

def format_number(n: float, precision: Optional[int] = None) -> str:
    if isinstance(n, int): return f"{n:,}"
    if precision is None: precision = 2 if n >= 1 else (3 if n >= 0.1 else 4)
    return f"{n:,.{precision}f}"

def format_date(date: datetime) -> str:
    return date.strftime("%b %d %Y")

def format_date_range(start: datetime, end: datetime) -> str:
    days = (end.date()-start.date()).days+1; dur = f" ({days}D)" if days>1 else ""
    if start.year != end.year: return f"{format_date(start)} - {format_date(end)}{dur}"
    if start.month != end.month: return f"{start.strftime('%b %d')} - {format_date(end)}{dur}"
    if start.day != end.day: return f"{start.strftime('%b %d')} - {end.day} {end.year}{dur}"
    return f"{format_date(start)}"

def get_ordinal(n: int) -> str:
    return 'th' if 10 <= n % 100 <= 20 else {1:'st',2:'nd',3:'rd'}.get(n % 10, 'th')

def build_project_tree(projects: Dict[str, Dict]) -> Dict:
    tree = {}
    for project, stats in projects.items():
        parts = project.split('/'); current = tree; path = ""
        for part in parts:
            path = f"{path}/{part}" if path else part
            if path not in current:
                current[path] = {"name": part, "full_path": path, "queries": 0, "cost": 0, "timestamps": [], "children": {}, "models": set()}
            current = current[path]["children"]
            for ancestor in [tree[p] for p in accumulate(parts, lambda x, y: x + '/' + y)]:
                ancestor["queries"] += stats["queries"]; ancestor["cost"] += stats["cost"]
                ancestor["timestamps"].extend(stats["timestamps"]); ancestor["models"].update(stats["models"])
    return tree

def print_project_tree(node: Dict, level: int = 0, show_empty: bool = False):
    if node["queries"] > 0 or show_empty:
        indent = "  " * level; dr = (format_date_range(datetime.fromtimestamp(min(node["timestamps"])), datetime.fromtimestamp(max(node["timestamps"]))) if node["timestamps"] else "No activity")
        print(f"{indent}{node['name']:<30} {format_number(node['queries']):>8}    ${format_number(node['cost']):>8}    {dr}")
    for child in sorted(node["children"].values(), key=lambda x: x["cost"], reverse=True):
        print_project_tree(child, level+1, show_empty)

def load_cost_data() -> List[Dict]:
    if not os.path.exists(COST_LOG_FILE): return []
    with open(COST_LOG_FILE, "r") as f: return [json.loads(line) for line in f]

def plot_monthly_costs(cost_data: List[Dict], output_path: str):
    monthly = defaultdict(float)
    for entry in cost_data:
        month = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m"); monthly[month] += entry["cost"]
    months = sorted(monthly.keys()); costs = [monthly[m] for m in months]
    plt.figure(figsize=(12,6)); plt.bar(months, costs); plt.title("Monthly Costs"); plt.xlabel("Month"); plt.ylabel("Cost ($)")
    plt.xticks(rotation=45); plt.tight_layout(); plt.savefig(output_path); plt.close()

def plot_daily_costs(cost_data: List[Dict], days: int, output_path: str):
    now = datetime.now(); daily = defaultdict(float)
    for entry in cost_data:
        d = datetime.fromisoformat(entry["timestamp"])
        if (now-d).days <= days: daily[d.strftime("%Y-%m-%d")] += entry["cost"]
    d_keys = sorted(daily.keys())[-days:]; costs = [daily[d] for d in d_keys]
    plt.figure(figsize=(12,6)); plt.bar(d_keys, costs); plt.title(f"Daily Costs (Last {len(d_keys)} Days)"); plt.xlabel("Date"); plt.ylabel("Cost ($)")
    plt.xticks(rotation=45); plt.tight_layout(); plt.savefig(output_path); plt.close()

def analyze_costs(only_period: Optional[str] = None, by_project: bool = False, current_project: Optional[str] = None, tree_view: bool = False):
    ensure_log_dir(); cost_data = load_cost_data()
    if not cost_data:
        print("\nNo cost data found."); return
    cost_data.sort(key=lambda x: x["timestamp"])
    if only_period:
        now = datetime.now()
        cutoff = {"day": now-timedelta(days=1), "week": now-timedelta(weeks=1), "month": now-timedelta(days=30)}.get(only_period, datetime.min)
        cost_data = [e for e in cost_data if datetime.fromisoformat(e["timestamp"]) > cutoff]
    if not cost_data:
        print(f"\nNo cost data found for period: {only_period}"); return
    total_cost = sum(e["cost"] for e in cost_data); total_tokens = sum(e["token_count"] for e in cost_data)
    start_date = datetime.fromisoformat(cost_data[0]["timestamp"]); end_date = datetime.fromisoformat(cost_data[-1]["timestamp"])
    print("\n[bold blue]Cost Analysis[/bold blue]")
    print(f"\nPeriod: {format_date_range(start_date, end_date)}")
    print(f"Total Cost: {format_cost(total_cost)}")
    print(f"Total Tokens: {format_number(total_tokens)}")
    print(f"Average Cost per Query: {format_cost(total_cost/len(cost_data))}")
    model_stats = defaultdict(lambda: {"cost": 0, "tokens": 0, "count": 0})
    for entry in cost_data:
        m = entry["model"]; model_stats[m]["cost"] += entry["cost"]; model_stats[m]["tokens"] += entry["token_count"]; model_stats[m]["count"] += 1
    print("\n[bold]Model Usage:[/bold]")
    for m, s in sorted(model_stats.items(), key=lambda x: x[1]["cost"], reverse=True):
        print(f"\n{m}:"); print(f"  Cost: {format_cost(s['cost'])} ({(s['cost']/total_cost*100):.1f}%)")
        print(f"  Tokens: {format_number(s['tokens'])}"); print(f"  Queries: {s['count']}")
        print(f"  Average Cost per Query: {format_cost(s['cost']/s['count'])}")
    if by_project:
        proj_stats = defaultdict(lambda: {"cost": 0, "tokens": 0, "count": 0})
        for entry in cost_data:
            p = entry.get("project", "unknown"); proj_stats[p]["cost"] += entry["cost"]; proj_stats[p]["tokens"] += entry["token_count"]; proj_stats[p]["count"] += 1
        if tree_view:
            projects = {p: {"cost": s["cost"], "tokens": s["tokens"], "count": s["count"], "children": {}} for p, s in proj_stats.items()}
            tree = build_project_tree(projects)
            print("\n[bold]Project Costs (Tree View):[/bold]"); print_project_tree(tree)
        else:
            print("\n[bold]Project Costs:[/bold]")
            for p, s in sorted(proj_stats.items(), key=lambda x: x[1]["cost"], reverse=True):
                if current_project and p != current_project: continue
                print(f"\n{p}:"); print(f"  Cost: {format_cost(s['cost'])} ({(s['cost']/total_cost*100):.1f}%)")
                print(f"  Tokens: {format_number(s['tokens'])}"); print(f"  Queries: {s['count']}")
                print(f"  Average Cost per Query: {format_cost(s['cost']/s['count'])}")