#!/usr/bin/env python3
"""
Module for retrieving and analyzing OpenAI API usage costs
"""
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from rich.console import Console
from rich.table import Table

console = Console()

def load_openai_key() -> Optional[str]:
    """Load the OpenAI API key from environment or .env files."""
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        return key
    
    for p in [os.path.join(os.path.expanduser("~"), ".env"),
              os.path.join(os.path.expanduser("~"), ".openai", ".env"),
              os.path.join(os.path.expanduser("~"), ".askp", ".env")]:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    for line in f:
                        if line.startswith("OPENAI_API_KEY="):
                            return line.split("=", 1)[1].strip().strip('"\'' )
            except Exception as e:
                print(f"Warning: Error reading {p}: {e}")
    print("Error: Could not find OpenAI API key.")
    return None

def get_costs(days: int = 7) -> Dict:
    """Get OpenAI API usage costs for the specified number of days.
    
    Args:
        days: Number of days of cost history to retrieve (default: 7)
        
    Returns:
        Dictionary containing the cost data response
    """
    api_key = load_openai_key()
    if not api_key:
        raise ValueError("OpenAI API key not found")
    
    # Create headers for direct API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Calculate start time as Unix timestamp
    end_time = int(time.time())
    start_time = end_time - (days * 24 * 60 * 60)
    
    import requests
    
    try:
        response = requests.get(
            "https://api.openai.com/v1/organization/costs",
            headers=headers,
            params={
                "start_time": start_time,
                "end_time": end_time,
                "limit": days
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error retrieving costs: {e}")
        return {}

def display_costs(days: int = 7):
    """Display OpenAI API usage costs in a formatted table.
    
    Args:
        days: Number of days of cost history to display (default: 7)
    """
    costs = get_costs(days)
    
    if not costs or not costs.get("data"):
        console.print("No cost data available")
        return
    
    table = Table(title=f"OpenAI API Costs (Last {days} Days)")
    table.add_column("Date", style="cyan")
    table.add_column("Amount", style="green")
    table.add_column("Currency", style="blue")
    
    for bucket in costs["data"]:
        date = datetime.fromtimestamp(bucket["start_time"]).strftime("%Y-%m-%d")
        for result in bucket["results"]:
            amount = result["amount"]["value"]
            currency = result["amount"]["currency"].upper()
            table.add_row(date, f"{amount:.2f}", currency)
    
    console.print(table)

if __name__ == "__main__":
    display_costs()
