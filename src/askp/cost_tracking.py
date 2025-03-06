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
    """Ensure the cost log directory exists."""
    Path(COST_LOG_DIR).mkdir(parents=True, exist_ok=True)

def log_query_cost(query_id: str, model_info: Dict, token_count: int, project: Optional[str] = None):
    """Log the cost of a query to the cost log file."""
    ensure_log_dir()
    
    cost = (token_count / 1_000_000) * model_info["cost_per_million"]
    entry = {
        "timestamp": datetime.now().isoformat(),
        "model": model_info["id"],
        "token_count": token_count,
        "cost": cost,
        "query_id": query_id
    }
    
    if project:
        entry["project"] = project
    
    with open(COST_LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    # Randomly run cost analysis (1 in 50 chance)
    if random.randint(1, 50) == 1:
        analyze_costs()

def format_cost(cost: float) -> str:
    """Format cost with appropriate decimal places based on amount."""
    if cost >= 1:
        return f"${cost:.2f}"
    elif cost >= 0.1:
        return f"${cost:.2f}"
    return f"${cost:.4f}"

def format_number(n: float, precision: Optional[int] = None) -> str:
    """Format number with commas and appropriate precision."""
    if isinstance(n, int):
        return f"{n:,}"
    if precision is None:
        if n >= 1:
            precision = 2
        elif n >= 0.1:
            precision = 3
        else:
            precision = 4
    return f"{n:,.{precision}f}"

def format_date(date: datetime) -> str:
    """Format date in a concise format."""
    return date.strftime("%b %d %Y")

def format_date_range(start: datetime, end: datetime) -> str:
    """Format date range in a concise format with duration."""
    duration_days = (end.date() - start.date()).days + 1
    duration = f" ({duration_days}D)" if duration_days > 1 else ""
    
    if start.year != end.year:
        return f"{format_date(start)} - {format_date(end)}{duration}"
    elif start.month != end.month:
        return f"{start.strftime('%b %d')} - {format_date(end)}{duration}"
    elif start.day != end.day:
        return f"{start.strftime('%b %d')} - {end.day} {end.year}{duration}"
    else:
        return f"{format_date(start)}"

def get_ordinal(n: int) -> str:
    """Get ordinal suffix for a number."""
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
    return suffix

def build_project_tree(projects: Dict[str, Dict]) -> Dict:
    """Build a tree structure of projects and their costs."""
    tree = {}
    for project, stats in projects.items():
        parts = project.split('/')
        current = tree
        path = ""
        for part in parts:
            path = path + "/" + part if path else part
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
            # Accumulate stats at each level
            for ancestor in [tree[p] for p in accumulate(parts, lambda x, y: x + '/' + y)]:
                ancestor["queries"] += stats["queries"]
                ancestor["cost"] += stats["cost"]
                ancestor["timestamps"].extend(stats["timestamps"])
                ancestor["models"].update(stats["models"])
    return tree

def print_project_tree(node: Dict, level: int = 0, show_empty: bool = False):
    """Print project tree with proper indentation."""
    if node["queries"] > 0 or show_empty:
        indent = "  " * level
        date_range = format_date_range(
            datetime.fromtimestamp(min(node["timestamps"])),
            datetime.fromtimestamp(max(node["timestamps"]))
        ) if node["timestamps"] else "No activity"
        
        print(f"{indent}{node['name']:<30} {format_number(node['queries']):>8}    ${format_number(node['cost']):>8}    {date_range}")
        
    for child in sorted(node["children"].values(), key=lambda x: x["cost"], reverse=True):
        print_project_tree(child, level + 1, show_empty)

def load_cost_data() -> List[Dict]:
    """Load cost data from the cost log file."""
    if not os.path.exists(COST_LOG_FILE):
        return []
    
    with open(COST_LOG_FILE, "r") as f:
        return [json.loads(line) for line in f]

def plot_monthly_costs(cost_data: List[Dict], output_path: str):
    """Generate monthly cost bar chart."""
    monthly_costs = defaultdict(float)
    for entry in cost_data:
        date = datetime.fromisoformat(entry["timestamp"])
        month_key = date.strftime("%Y-%m")
        monthly_costs[month_key] += entry["cost"]
    
    months = sorted(monthly_costs.keys())
    costs = [monthly_costs[m] for m in months]
    
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
    """Generate daily cost bar chart for recent days."""
    now = datetime.now()
    daily_costs = defaultdict(float)
    
    for entry in cost_data:
        date = datetime.fromisoformat(entry["timestamp"])
        if (now - date).days <= days:
            day_key = date.strftime("%Y-%m-%d")
            daily_costs[day_key] += entry["cost"]
    
    days = sorted(daily_costs.keys())[-days:]
    costs = [daily_costs[d] for d in days]
    
    plt.figure(figsize=(12, 6))
    plt.bar(days, costs)
    plt.title(f"Daily Costs (Last {len(days)} Days)")
    plt.xlabel("Date")
    plt.ylabel("Cost ($)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def analyze_costs(only_period: Optional[str] = None, by_project: bool = False,
                 current_project: Optional[str] = None, tree_view: bool = False):
    """Analyze query costs globally or by project."""
    ensure_log_dir()
    
    # Load cost data
    cost_data = load_cost_data()
    if not cost_data:
        print("\nNo cost data found.")
        return
    
    # Sort entries by timestamp
    cost_data.sort(key=lambda x: x["timestamp"])
    
    # Filter by time period if specified
    if only_period:
        now = datetime.now()
        if only_period == "day":
            cutoff = now - timedelta(days=1)
        elif only_period == "week":
            cutoff = now - timedelta(weeks=1)
        elif only_period == "month":
            cutoff = now - timedelta(days=30)
        else:  # "all"
            cutoff = datetime.min
            
        cost_data = [
            entry for entry in cost_data 
            if datetime.fromisoformat(entry["timestamp"]) > cutoff
        ]
    
    if not cost_data:
        print(f"\nNo cost data found for period: {only_period}")
        return
    
    # Calculate total costs
    total_cost = sum(entry["cost"] for entry in cost_data)
    total_tokens = sum(entry["token_count"] for entry in cost_data)
    
    # Get date range
    start_date = datetime.fromisoformat(cost_data[0]["timestamp"])
    end_date = datetime.fromisoformat(cost_data[-1]["timestamp"])
    
    # Print global stats
    print("\n[bold blue]Cost Analysis[/bold blue]")
    print(f"\nPeriod: {format_date_range(start_date, end_date)}")
    print(f"Total Cost: {format_cost(total_cost)}")
    print(f"Total Tokens: {format_number(total_tokens)}")
    print(f"Average Cost per Query: {format_cost(total_cost / len(cost_data))}")
    
    # Group by model
    model_stats = defaultdict(lambda: {"cost": 0, "tokens": 0, "count": 0})
    for entry in cost_data:
        model = entry["model"]
        model_stats[model]["cost"] += entry["cost"]
        model_stats[model]["tokens"] += entry["token_count"]
        model_stats[model]["count"] += 1
    
    # Print model breakdown
    print("\n[bold]Model Usage:[/bold]")
    for model, stats in sorted(model_stats.items(), key=lambda x: x[1]["cost"], reverse=True):
        cost = stats["cost"]
        tokens = stats["tokens"]
        count = stats["count"]
        print(f"\n{model}:")
        print(f"  Cost: {format_cost(cost)} ({(cost/total_cost*100):.1f}%)")
        print(f"  Tokens: {format_number(tokens)}")
        print(f"  Queries: {count}")
        print(f"  Average Cost per Query: {format_cost(cost/count)}")
    
    # Group by project if requested
    if by_project:
        project_stats = defaultdict(lambda: {"cost": 0, "tokens": 0, "count": 0})
        for entry in cost_data:
            project = entry.get("project", "unknown")
            project_stats[project]["cost"] += entry["cost"]
            project_stats[project]["tokens"] += entry["token_count"]
            project_stats[project]["count"] += 1
        
        if tree_view:
            # Build and print project tree
            projects = {
                project: {
                    "cost": stats["cost"],
                    "tokens": stats["tokens"],
                    "count": stats["count"],
                    "children": {}
                }
                for project, stats in project_stats.items()
            }
            tree = build_project_tree(projects)
            print("\n[bold]Project Costs (Tree View):[/bold]")
            print_project_tree(tree)
        else:
            # Print flat project list
            print("\n[bold]Project Costs:[/bold]")
            for project, stats in sorted(project_stats.items(), key=lambda x: x[1]["cost"], reverse=True):
                if current_project and project != current_project:
                    continue
                cost = stats["cost"]
                tokens = stats["tokens"]
                count = stats["count"]
                print(f"\n{project}:")
                print(f"  Cost: {format_cost(cost)} ({(cost/total_cost*100):.1f}%)")
                print(f"  Tokens: {format_number(tokens)}")
                print(f"  Queries: {count}")
                print(f"  Average Cost per Query: {format_cost(cost/count)}")

def get_rate_limit_info() -> Dict:
    """Get rate limit information."""
    return {
        "requests_per_minute": 50,
        "current_minute_requests": 0,
        "minute_start": datetime.now()
    }

def estimate_token_count(text: str) -> int:
    """Estimate token count for a text string using a simple heuristic.
    
    This is a rough estimate based on word count. For more accurate counts,
    use the model's tokenizer directly.
    """
    return max(1, len(text.split()) + int(len(text) * 0.3))

def get_project_from_path(path: str) -> Optional[str]:
    """Extract project name from a file path.
    
    Args:
        path: File path to analyze
        
    Returns:
        Project name if found, None otherwise
    """
    if not path:
        return None
        
    path = Path(path).resolve()
    
    # Check for .working_directory file
    wd_file = path / ".working_directory"
    if wd_file.exists():
        return wd_file.read_text().strip()
    
    # Handle home directory paths
    home = Path.home()
    if str(path).startswith(str(home)):
        path = Path("~") / path.relative_to(home)
    
    # Look for common project indicators
    parts = path.parts
    for i, part in enumerate(parts):
        if part in [".git", "src", "tests", "docs"]:
            # Project name is typically the parent of these directories
            if i > 0:
                return str(parts[i-1])
    
    return None
