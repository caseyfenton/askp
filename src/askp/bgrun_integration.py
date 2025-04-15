#!/usr/bin/env python3
"""
BGRun integration for ASKP.
Contains notification functions for BGRun integration.
"""

def notify_query_completed(query: str, saved_path: str, model: str, tokens: int, cost: float) -> None:
    """Notify BGRun about query completion."""
    # Implementation can be filled in later
    pass

def notify_multi_query_completed(num_queries: int, combined_file: str, tokens: int, cost: float) -> None:
    """Notify BGRun about multi-query completion."""
    # Implementation can be filled in later
    pass

def update_askp_status_widget(query_count: int, total_cost: float) -> None:
    """Update BGRun status widget with ASKP stats."""
    # Implementation can be filled in later
    pass
