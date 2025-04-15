#!/usr/bin/env python3
"""
Visualization module for ASKP cost analytics.
This module is completely optional and will gracefully fail if matplotlib is not available.
"""
import os
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Global flag to indicate if visualization is available
VISUALIZATION_AVAILABLE = False

try:
    import matplotlib
    import matplotlib.pyplot as plt
    VISUALIZATION_AVAILABLE = True
except ImportError:
    pass
except Exception as e:
    print(f"Warning: Matplotlib available but error occurred: {e}")

def is_visualization_available() -> bool:
    """Check if visualization capabilities are available."""
    return VISUALIZATION_AVAILABLE

def plot_monthly_costs(cost_data: List[Dict], output_path: str) -> bool:
    """
    Plot monthly costs and save to output_path.
    
    Args:
        cost_data: List of cost entry dictionaries
        output_path: Where to save the plot
        
    Returns:
        True if successful, False if visualization not available
    """
    if not VISUALIZATION_AVAILABLE:
        print("Warning: Matplotlib not available, skipping monthly cost plot.")
        return False
        
    try:
        monthly = defaultdict(float)
        for entry in cost_data:
            month = datetime.fromisoformat(entry["timestamp"]).strftime("%Y-%m")
            monthly[month] += entry["cost"]
        
        months = sorted(monthly.keys())
        costs = [monthly[m] for m in months]
        readable_months = [datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in months]
        
        plt.figure(figsize=(10, 5))
        plt.bar(readable_months, costs)
        plt.xlabel("Month")
        plt.ylabel("Cost ($)")
        plt.title("Monthly Perplexity API Costs")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return True
    except Exception as e:
        print(f"Error plotting monthly costs: {e}")
        return False

def plot_daily_costs(cost_data: List[Dict], days: int, output_path: str) -> bool:
    """
    Plot daily costs for the past N days and save to output_path.
    
    Args:
        cost_data: List of cost entry dictionaries
        days: Number of days to show
        output_path: Where to save the plot
        
    Returns:
        True if successful, False if visualization not available
    """
    if not VISUALIZATION_AVAILABLE:
        print("Warning: Matplotlib not available, skipping daily cost plot.")
        return False
        
    try:
        now = datetime.now()
        daily = defaultdict(float)
        for entry in cost_data:
            try:
                date = datetime.fromisoformat(entry["timestamp"]).date()
                if (now.date() - date).days <= days:
                    daily[date.isoformat()] += entry["cost"]
            except (ValueError, KeyError):
                continue
                
        dates = sorted(daily.keys())
        costs = [daily[d] for d in dates]
        readable_dates = [datetime.fromisoformat(d).strftime("%m/%d") for d in dates]
        
        plt.figure(figsize=(12, 5))
        plt.bar(readable_dates, costs)
        plt.xlabel("Date")
        plt.ylabel("Cost ($)")
        plt.title(f"Daily Perplexity API Costs (Last {days} Days)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return True
    except Exception as e:
        print(f"Error plotting daily costs: {e}")
        return False

def plot_model_distribution(cost_data: List[Dict], output_path: str) -> bool:
    """
    Plot cost distribution by model type.
    
    Args:
        cost_data: List of cost entry dictionaries
        output_path: Where to save the plot
        
    Returns:
        True if successful, False if visualization not available
    """
    if not VISUALIZATION_AVAILABLE:
        print("Warning: Matplotlib not available, skipping model distribution plot.")
        return False
        
    try:
        model_costs = defaultdict(float)
        for entry in cost_data:
            model = entry.get("model", "unknown")
            model_costs[model] += entry.get("cost", 0)
            
        models = list(model_costs.keys())
        costs = [model_costs[m] for m in models]
        
        # Sort by cost in descending order
        models, costs = zip(*sorted(zip(models, costs), key=lambda x: x[1], reverse=True))
        
        plt.figure(figsize=(10, 6))
        plt.bar(models, costs)
        plt.xlabel("Model")
        plt.ylabel("Cost ($)")
        plt.title("Perplexity API Costs by Model")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        return True
    except Exception as e:
        print(f"Error plotting model distribution: {e}")
        return False
