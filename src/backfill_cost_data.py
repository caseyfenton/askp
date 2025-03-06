#!/usr/bin/env python3
"""Backfill cost tracking data for ASKP CLI from existing Perplexity results."""
import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from askp.cost_tracking import COST_LOG_FILE, ensure_log_dir
from askp.models import MODEL_REGISTRY
from askp.utils import detect_model

PROJECT_ROOTS = {"projects", "cascadeprojects", "workspace", "repos", "code"}
NON_PROJECT_DIRS = {"src", "results", "temp", "logs", "data", "tests", "perplexity", "ask", "askd", "askp", "old"}


def get_project_from_path(path: str) -> Optional[str]:
    p = Path(path).resolve()
    # Look for a .working_directory marker in parents.
    for parent in p.parents:
        wd_marker = parent / ".working_directory"
        if wd_marker.exists():
            try:
                return wd_marker.read_text().strip()
            except Exception:
                pass
    parts = p.parts
    # Check common project roots.
    for i, part in enumerate(parts):
        if part.lower() in PROJECT_ROOTS and i + 1 < len(parts):
            if parts[i + 1].lower() not in NON_PROJECT_DIRS:
                return parts[i + 1]
    # Check for src/project_name pattern.
    try:
        src_idx = parts.index("src")
        if src_idx > 0:
            return parts[src_idx - 1]
    except ValueError:
        pass
    # Check for results directory pattern.
    for i, part in enumerate(parts):
        if "results" in part.lower() and i > 0 and parts[i - 1].lower() not in NON_PROJECT_DIRS:
            return parts[i - 1]
    return None


def estimate_token_count(content: str) -> int:
    code_chars = len(re.findall(r"[{}()\[\]<>+=\-*/\\|;:~`@#$%^&]", content))
    total_chars = len(content)
    ratio = code_chars / total_chars if total_chars else 0
    tokens = int(total_chars / (3.5 if ratio > 0.05 else 4.0)) + code_chars
    return max(1, tokens)


def is_perplexity_result(filepath: str, content: str) -> bool:
    filename = Path(filepath).name
    if filename.endswith("_citations.md"):
        return False
    patterns = [
        r"perplexity_\d{8}_\d{6}_.+\.(txt|md)$",
        r"perplexity_[a-zA-Z0-9_]+\.(txt|md)$",
        r"[a-zA-Z_]+_\d{8}_\d{6}_[a-zA-Z_]+\.(txt|md)$",
        r"[a-zA-Z_]+_\d{8}_\d{6}\.(txt|md)$",
    ]
    if not any(re.match(p, filename) for p in patterns) or len(content) < 50:
        return False
    # If a citations file exists, consider it a valid result.
    if Path(filepath.replace(".md", "_citations.md")).exists():
        return True
    markers = [
        "Here are", "Based on", "According to", "Let me", "I'll", "To answer",
        "I found", "The answer", "References:", "Sources:", "http://", "https://"
    ]
    return any(marker in content for marker in markers)


def get_timestamp_from_file(filepath: str) -> str:
    filename = Path(filepath).name
    m = re.search(r"_(\d{8}_\d{6})(?:_|\.|$)", filename)
    if m:
        try:
            dt = datetime.strptime(m.group(1), "%Y%m%d_%H%M%S")
            return dt.isoformat()
        except ValueError:
            pass
    return datetime.fromtimestamp(Path(filepath).stat().st_ctime).isoformat()


def process_file_with_citations(filepath: str) -> str:
    try:
        content = Path(filepath).read_text(encoding="utf-8")
        citations = Path(filepath.replace(".md", "_citations.md"))
        if citations.exists():
            try:
                content += "\n\nCitations:\n" + citations.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Warning: Could not read citations file {citations}: {e}")
        return content
    except Exception as e:
        print(f"Error processing file {filepath}: {e}")
        return ""


def find_and_process_results(base_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    base_dir = Path(base_dir or os.path.expanduser("~/CascadeProjects"))
    print(f"Searching for results in {base_dir}...")
    all_entries: List[Dict[str, Any]] = []
    processed_files: set = set()
    unknown_project_files: List[Any] = []
    skip_dirs = {"node_modules", ".git", "__pycache__", "venv", ".env"}

    def format_cost(cost: float) -> str:
        return f"${cost:.4f}" if cost < 0.01 else f"${cost:.2f}"

    total_files_processed = 0
    total_cost = 0.0
    current_folder = None

    for root, _, files in os.walk(base_dir):
        if any(skip in root for skip in skip_dirs):
            continue
        result_files = []
        for file in files:
            if file.endswith((".txt", ".md", ".json", ".jsonl")):
                filepath = os.path.join(root, file)
                if filepath in processed_files or file.endswith("_citations.md"):
                    continue
                try:
                    content = Path(filepath).read_text(encoding="utf-8")
                    if is_perplexity_result(filepath, content):
                        result_files.append((filepath, content))
                except (UnicodeDecodeError, Exception):
                    continue

        if result_files:
            if current_folder != root:
                if current_folder is not None:
                    print()
                current_folder = root
                rel = os.path.relpath(root, base_dir)
                print(f"Found {len(result_files)} result files in {rel}")
            entries, dir_cost, files_processed = [], 0.0, 0
            for filepath, content in result_files:
                try:
                    model = detect_model(content, filepath)
                    if not model:
                        continue
                    tokens = estimate_token_count(content)
                    cost = (tokens / 1_000_000) * MODEL_REGISTRY[model]["cost_per_million"]
                    project = get_project_from_path(filepath) or "unknown"
                    if project == "unknown":
                        unknown_project_files.append((filepath, cost))
                    entry = {
                        "timestamp": get_timestamp_from_file(filepath),
                        "file": filepath,
                        "model": MODEL_REGISTRY[model]["id"],
                        "token_count": tokens,
                        "cost": cost,
                        "project": project,
                        "working_directory": os.path.dirname(filepath),
                        "source": "perplexity"
                    }
                    entries.append(entry)
                    all_entries.append(entry)
                    processed_files.add(filepath)
                    dir_cost += cost
                    files_processed += 1
                    if len(result_files) > 20 and files_processed % 20 == 0:
                        print(f"Progress: {files_processed}/{len(result_files)} files ({format_cost(dir_cost)} cost so far)")
                except Exception as e:
                    print(f"Error processing {Path(filepath).name}: {e}")
            if entries:
                rel_dir = os.path.relpath(root, base_dir)
                print(f"\nFinished processing {rel_dir}:")
                print(f"- Files processed: {files_processed}")
                print(f"- Total cost: {format_cost(dir_cost)}")
                total_files_processed += files_processed
                total_cost += dir_cost

    if total_files_processed == 0:
        print("\nNo Perplexity result files found.")
        return []

    print(f"\nOverall Summary:")
    print(f"- Total files processed: {total_files_processed}")
    print(f"- Total cost entries: {len(all_entries)}")
    print(f"- Total cost: ${total_cost:.2f}")

    if unknown_project_files:
        print("\nWarning: Could not determine project for some files:")
        for filepath, cost in unknown_project_files[:5]:
            print(f"  - {os.path.relpath(filepath, base_dir)} (cost: {format_cost(cost)})")
        if len(unknown_project_files) > 5:
            print(f"  ... and {len(unknown_project_files) - 5} more files")
        print("\nTo fix this, you can:")
        print("1. Create a .working_directory file in the project root with the project name")
        print("2. Move results to a more standard project directory structure")
    return all_entries


def write_cost_data(entries: List[Dict], mode: str = "a") -> None:
    if not entries:
        print("No entries to write")
        return
    try:
        ensure_log_dir()
        print("\nSorting entries by timestamp...")
        entries.sort(key=lambda x: x["timestamp"])
        existing_keys = set()
        cost_log = Path(COST_LOG_FILE)
        if cost_log.exists():
            with cost_log.open("r") as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        key = f"{entry['timestamp']}:{entry.get('file', '')}"
                        existing_keys.add(key)
                    except json.JSONDecodeError:
                        continue
        print("Writing new entries...")
        new_count, total_new_cost = 0, 0.0
        with cost_log.open(mode) as f:
            for entry in entries:
                key = f"{entry['timestamp']}:{entry.get('file', '')}"
                if key not in existing_keys:
                    f.write(json.dumps(entry) + "\n")
                    new_count += 1
                    total_new_cost += entry["cost"]
        print(f"\nResults:")
        print(f"- Added {new_count} new entries")
        print(f"- Skipped {len(entries) - new_count} duplicate entries")
        print(f"- Total cost of new entries: ${total_new_cost:.2f}")
    except Exception as e:
        print(f"Error writing to cost log: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Backfill cost tracking data from Perplexity results")
    parser.add_argument("--directory", "-d", type=str, help="Directory to search (default: ~/CascadeProjects)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing cost log")
    parser.add_argument("--quick", dest="quick_extract", action="store_true", help="Use quick extraction")
    args = parser.parse_args()
    directory = os.path.expanduser(args.directory) if args.directory else os.path.expanduser("~/CascadeProjects")
    try:
        entries = find_and_process_results(directory)
        if entries:
            write_cost_data(entries, mode="w" if args.overwrite else "a")
    except Exception as e:
        print(f"Error during backfill: {e}")
        import traceback
        print(traceback.format_exc())
        exit(1)