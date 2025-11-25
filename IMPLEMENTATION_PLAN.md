# SEMA-Based Perplexity Cache Implementation Plan

**Date**: 2025-10-24
**Goal**: Enable semantic caching of Perplexity results using existing SEMA system

---

## Architecture Overview

```
User Query
    ↓
askp CLI (--no-cache flag)
    ↓
Cache Check (cache.py)
    ↓
SEMA Search (semantic matching, threshold 0.75)
    ↓
[Cache Hit]              [Cache Miss]
    ↓                        ↓
Return paths          Perplexity API
Display results       Save + Index
    ↓                        ↓
User gets results     User gets results
```

---

## Phase 1: Perplexity Folder Discovery (1 hour)

### Files to Create/Modify
1. **`/Users/casey/CascadeProjects/SEMA/src/perplexity_discovery.py`** (NEW)
   - `discover_all_perplexity_folders()` - Use mdfind
   - `register_folders_with_sema()` - Add to SEMA registry

2. **`/Users/casey/CascadeProjects/SEMA/bin/sema`** (MODIFY)
   - Add `--register-perplexity` flag
   - Add `--index-perplexity` flag

### Implementation Details
```python
# perplexity_discovery.py
import subprocess
from pathlib import Path

def discover_all_perplexity_folders() -> list[Path]:
    """Find all perplexity_results folders using mdfind."""
    result = subprocess.run(
        ['mdfind', '-name', 'perplexity_results', '-onlyin', str(Path.home())],
        capture_output=True, text=True, check=True
    )
    folders = [Path(p) for p in result.stdout.strip().split('\n') if p]
    return [f for f in folders if f.exists() and f.is_dir()]

def register_folders_with_sema(folders: list[Path]) -> dict:
    """Register folders with SEMA's directory registry."""
    # Use SEMA's CascadeSearcher.add_directory_to_registry()
    pass
```

### Testing
- [ ] Discover folders on system
- [ ] Register with SEMA
- [ ] Verify in `~/.sema_directory_registry.json`
- [ ] Test SEMA search finds Perplexity results

---

## Phase 2: Cache Module (2 hours)

### Files to Create
1. **`/Users/casey/pro/askp/src/askp/cache.py`** (NEW)
   - `check_sema_cache(query: str) -> list[Path] | None`
   - `format_cache_results(paths: list[Path]) -> str`
   - `display_cache_hit(query: str, paths: list[Path])`

### Implementation Details
```python
# cache.py
import subprocess
import json
from pathlib import Path
from typing import Optional

SIMILARITY_THRESHOLD = 0.75

def check_sema_cache(query: str) -> Optional[list[Path]]:
    """Check SEMA for cached Perplexity results.

    Returns paths to cached results if similarity >= 0.75, else None.
    """
    try:
        result = subprocess.run(
            ['sema', '--raw', query],
            capture_output=True, text=True, timeout=5
        )

        if result.returncode != 0:
            return None

        matches = json.loads(result.stdout)

        # Filter by similarity threshold
        high_confidence = [
            Path(m['path'])
            for m in matches
            if m.get('score', 0) >= SIMILARITY_THRESHOLD
        ]

        return high_confidence[:5] if high_confidence else None

    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return None

def format_cache_results(paths: list[Path]) -> str:
    """Format cache results for display."""
    output = ["🎯 Found cached results:\n"]
    for i, path in enumerate(paths, 1):
        output.append(f"  {i}. {path}")
    return "\n".join(output)

def display_cache_hit(query: str, paths: list[Path]) -> bool:
    """Display cache hit and ask user if they want fresh search.

    Returns True if user wants to use cache, False for fresh search.
    """
    print(format_cache_results(paths))
    print(f"\n💡 These results match your query: '{query}'")

    import click
    return not click.confirm("Run fresh search anyway?", default=False)
```

### Testing
- [ ] Test cache hit (existing query)
- [ ] Test cache miss (new query)
- [ ] Test similarity threshold filtering
- [ ] Test timeout handling
- [ ] Test SEMA not running

---

## Phase 3: CLI Integration (1 hour)

### Files to Modify
1. **`/Users/casey/pro/askp/src/askp/cli.py`**
   - Add `--no-cache` / `-NC` flag
   - Add cache check before API call
   - Add cache statistics to output

### Implementation Details
```python
# In cli.py

@click.option("--no-cache", "-NC", is_flag=True,
              help="Bypass cache and force fresh Perplexity search")
def cli(..., no_cache):
    # ... existing setup code ...

    # BEFORE processing queries, check cache
    if not no_cache and len(queries) == 1:
        from .cache import check_sema_cache, display_cache_hit

        cached_paths = check_sema_cache(queries[0])
        if cached_paths:
            if display_cache_hit(queries[0], cached_paths):
                # User wants to use cache
                for path in cached_paths:
                    with open(path) as f:
                        print(f.read())
                ctx.exit()

    # ... continue with normal flow if no cache or user wants fresh ...
```

### Testing
- [ ] Test `--no-cache` bypasses cache
- [ ] Test cache check happens by default
- [ ] Test user interaction (use cache vs fresh)
- [ ] Test multi-query (cache disabled for multi)

---

## Phase 4: Auto-Update Integration (1 hour)

### Files to Modify
1. **`/Users/casey/pro/askp/src/askp/executor.py`**
   - Add SEMA indexing after saving result

### Implementation Details
```python
# In executor.py, after save_result_file()

def index_with_sema(file_path: Path):
    """Index newly created result with SEMA."""
    try:
        subprocess.run(
            ['sema', '--index'],
            cwd=file_path.parent,
            capture_output=True,
            timeout=10
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # SEMA not available, skip indexing
```

### Testing
- [ ] Test new results get indexed automatically
- [ ] Test subsequent queries find newly created results
- [ ] Test SEMA not running doesn't break askp

---

## Edge Cases to Handle

1. **SEMA Not Running**
   - Fall through to normal API call
   - Don't break askp functionality

2. **Empty perplexity_results Folders**
   - SEMA should skip empty folders
   - Don't add to registry

3. **Stale Cache**
   - SEMA handles with incremental updates
   - Manual: `sema --update-all`

4. **Multi-Query Mode**
   - Disable cache for multi-query (too complex)
   - Only cache single queries

5. **Similarity Threshold False Positives**
   - Use 0.75 threshold (medium-high confidence)
   - User can always force fresh with `--no-cache`

6. **Large Result Sets**
   - Limit to 5 cached results max
   - Show most relevant first

---

## Testing Plan

### Unit Tests
- [ ] `cache.check_sema_cache()` with mocked SEMA
- [ ] `cache.format_cache_results()`
- [ ] `perplexity_discovery.discover_all_perplexity_folders()`

### Integration Tests
- [ ] End-to-end: Query → Cache hit → Display
- [ ] End-to-end: Query → Cache miss → API call
- [ ] SEMA indexing after new result

### Manual Tests
- [ ] `askp "test query"` (cache hit)
- [ ] `askp --no-cache "test query"` (bypass)
- [ ] `askp "completely new query"` (cache miss)
- [ ] `sema --register-perplexity` (discovery)

---

## Success Criteria

✅ Cache hit: Sub-second response (no API call)
✅ Cache miss: Normal API call, result indexed
✅ `--no-cache` always bypasses cache
✅ SEMA failure doesn't break askp
✅ Perplexity folders auto-discovered
✅ New results automatically indexed
✅ Similarity threshold filters irrelevant results

---

## Rollback Plan

If issues arise:
1. Remove `--no-cache` flag from CLI
2. Comment out cache check in `cli.py`
3. Keep `cache.py` for future use
4. SEMA integration remains (no harm)

---

## Timeline

- Phase 1: 1 hour (Discovery)
- Phase 2: 2 hours (Cache module)
- Phase 3: 1 hour (CLI integration)
- Phase 4: 1 hour (Auto-update)
- **Total: 5 hours**

---

## Next Steps

1. Create `perplexity_discovery.py`
2. Create `cache.py`
3. Modify `cli.py` to add `--no-cache` and cache check
4. Test with real queries
5. Launch verification agents in parallel
6. Commit changes

---

**Status**: Ready to implement
**Confidence**: High (building on existing SEMA)
