# SEMA Indexing Integration

## Summary

Added automatic SEMA indexing to askp after saving results. This enables future cache hits by indexing newly created result files.

## Implementation

### New Function: `index_with_sema()`

Location: `/Users/casey/pro/askp/src/askp/executor.py` (lines 26-39)

```python
def index_with_sema(result_path: Path) -> None:
    """Index newly created result with SEMA for future cache hits."""
    try:
        import subprocess
        subprocess.run(
            ['sema', '--index'],
            cwd=result_path.parent,
            capture_output=True,
            timeout=10,
            check=False  # Don't fail if sema not available
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # SEMA not available, skip indexing (don't break askp)
        pass
```

### Integration Points

1. **`save_result_file()`** (line 91)
   - Called after saving individual query results
   - Indexes single-query result files

2. **`append_to_combined()`** (line 199)
   - Called after appending to combined file
   - Indexes combined file incrementally as queries complete

3. **`output_multi_results()`** (line 607)
   - Called after writing final combined output
   - Indexes deep research and multi-query results

## Safety Features

- **Graceful Failure**: Does not break askp if SEMA is not installed
- **Timeout Protection**: 10-second timeout prevents blocking askp
- **Error Handling**: Catches `subprocess.TimeoutExpired` and `FileNotFoundError`
- **Non-blocking**: Uses `check=False` to prevent raising exceptions on SEMA errors

## Testing

All tests pass:
- ✓ Graceful failure when SEMA not available
- ✓ Integration with save_result_file()
- ✓ Timeout handling (10s limit)
- ✓ Python syntax validation

## Benefits

- Automatic indexing of all askp results
- No manual `sema --index` commands needed
- Future cache hits for similar queries
- Zero impact if SEMA not available
- Minimal performance overhead (10s max per file)
