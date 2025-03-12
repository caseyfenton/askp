#!/usr/bin/env python3
"""Tips module for ASKP CLI."""
import random
from typing import Optional

TIPS = [
    "TIP: Run multiple searches in a single command to parallelize your research:\naskp -m \"Python packaging\" \"Python security\" \"Python compatibility\"",
    "TIP: Combine results into a single output file for faster reading:\naskp -m -c -o research.md \"Query 1\" \"Query 2\" \"Query 3\"",
    "TIP: For complex research topics, break down your question into 5-10 specific queries for more comprehensive results.",
    "TIP: Use ASKP with Windsurf or other vector-enabled IDEs to make all search results instantly searchable within your codebase.",
    "TIP: Track your API usage costs with 'askp costs' to monitor your spending.",
    "TIP: Use the --expand option to automatically generate related queries:\naskp --expand 5 \"Python best practices\"",
    "TIP: Save common query patterns to a file and use with -i option:\naskp -m -i my_queries.txt",
    "TIP: Combine --expand with --multi for comprehensive research on complex topics.",
    "TIP: The average cost per search is a fraction of a penny, making ASKP extremely cost-effective for research.",
    "TIP: For legal research, use ASKP to quickly gather primary sources and bring them into your codebase.",
    "TIP: The -e/--expand option generates solution-focused queries that consider recent developments and time-sensitive information.",
    "TIP: For coding problems, use -e to generate queries that focus on up-to-date solutions and recent language features:\naskp -e 3 \"How to optimize Python code for performance\"",
    "TIP: Query expansion is designed to help you find practical, actionable solutions to problems, not just information."
]

def get_random_tip() -> str:
    """Return a random tip from the collection."""
    return random.choice(TIPS)

def should_show_tip(frequency: float = 0.3) -> bool:
    """Determine if a tip should be shown based on frequency (0.0-1.0)."""
    return random.random() < frequency

def format_tip(tip: str) -> str:
    """Format a tip for display."""
    return f"\n[bright_blue]{tip}[/bright_blue]\n"

def get_formatted_tip(frequency: float = 0.3) -> Optional[str]:
    """Get a formatted random tip if it should be shown based on frequency."""
    if should_show_tip(frequency):
        return format_tip(get_random_tip())
    return None