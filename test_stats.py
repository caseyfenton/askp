#!/usr/bin/env python3
"""
Test script for ASKD cost statistics and backfill operations.
"""
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
sys.path.insert(0, src_path)

from askp.cost_tracking import analyze_costs, COST_LOG_FILE
from src.backfill_cost_data import find_and_process_results, write_cost_data

def test_current_stats():
    """Test the current statistics functionality"""
    print("\n=== Current Cost Statistics ===")
    print(f"Looking for cost log file at: {COST_LOG_FILE}")
    if os.path.exists(COST_LOG_FILE):
        print(f"Cost log file exists, size: {os.path.getsize(COST_LOG_FILE)} bytes")
    else:
        print("Cost log file does not exist yet.")
    
    print("\nRunning cost analysis:")
    analyze_costs()
    
def run_backfill():
    """Run the backfill operation to populate cost data from existing files"""
    print("\n=== Running Backfill Operation ===")
    results_dir = os.path.expanduser("~/CascadeProjects")
    print(f"Looking for Perplexity results in: {results_dir}")
    
    try:
        extracted_entries = find_and_process_results(results_dir)
        if extracted_entries:
            print(f"Found {len(extracted_entries)} entries to backfill.")
            write_cost_data(extracted_entries)
            print("Backfill complete!")
        else:
            print("No entries were found to backfill.")
    except Exception as e:
        print(f"Error during backfill: {str(e)}")
        return False
    
    return True

def check_stats_after_backfill():
    """Check statistics after backfill operation"""
    print("\n=== Statistics After Backfill ===")
    analyze_costs()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test ASKD cost statistics and backfill")
    parser.add_argument("--stats-only", action="store_true", help="Only show current statistics")
    parser.add_argument("--backfill-only", action="store_true", help="Only run backfill operation")
    
    args = parser.parse_args()
    
    if args.stats_only:
        test_current_stats()
    elif args.backfill_only:
        run_backfill()
    else:
        # Run full test
        test_current_stats()
        if run_backfill():
            check_stats_after_backfill()
