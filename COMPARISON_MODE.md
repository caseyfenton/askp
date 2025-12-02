# ASKP Comparison Mode

## Overview

Comparison mode runs a query in **BOTH traditional and agent modes** simultaneously, allowing you to compare the two output formats side-by-side.

## Usage

```bash
askp --compare "your question here"
```

## What It Does

1. Runs the query in **traditional mode** - generates full markdown response with detailed content
2. Runs the query in **agent mode** - generates lightweight JSON index with lazy-loadable modules
3. Saves both outputs with distinct suffixes:
   - `query_*_traditional.md` - Full traditional response
   - `query_*_agent.md` - Lightweight agent index
4. Displays comparison summary with token counts and savings

## Example

```bash
askp --compare --basic "What is JavaScript?"
```

**Output:**
```
🔄 COMPARISON MODE - Running query in both traditional and agent modes...

📝 Running TRADITIONAL mode...
Saved: /path/to/query_1_20251201_223423_What_is_JavaScript__traditional.md

🤖 Running AGENT mode...
Saved: /path/to/query_1_20251201_223435_What_is_JavaScript__agent.md

============================================================
📊 COMPARISON SUMMARY
============================================================

✅ Both modes completed successfully!

📁 Output files:
   Traditional: /path/to/query_1_20251201_223423_What_is_JavaScript__traditional.md
   Agent:       /path/to/query_1_20251201_223435_What_is_JavaScript__agent.md

📈 Token comparison:
   Traditional: 750 tokens
   Agent:       370 tokens
   Savings:     50.7%

💡 Agent mode provides lightweight index with lazy-loadable modules.
   Use --agent-module <ID> --query-id <UUID> to load specific modules.
============================================================
```

## File Structure

### Traditional Mode Output (3600 bytes)
- Full detailed content
- Complete markdown formatting
- All citations and sources
- Ready for human reading

### Agent Mode Output (1670 bytes)
- Decision context (outcome, confidence, complexity)
- Entity graph (key-value facts)
- Module index (lazy-loadable content sections)
- Query UUID for module retrieval

## Use Cases

### For Development
Compare outputs during agent mode development to ensure both modes produce equivalent information.

### For Documentation
Generate examples showing the difference between traditional and agent mode responses.

### For Optimization
Measure token savings and response structure differences for different query types.

## Limitations

- Only works with **single queries** (not multiple queries or deep research)
- Runs two API calls (doubles the cost)
- Cannot be combined with other modes (comprehensive, expand, etc.)

## Related

- [AGENT_MODE.md](AGENT_MODE.md) - Full agent mode documentation
- [QUICK_START_AGENT_MODE.md](QUICK_START_AGENT_MODE.md) - Quick start guide
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing procedures

## Implementation

**Added in:** 2025-12-01
**Version:** 2.4.6 (pending)
**Files Modified:**
- `src/askp/cli.py` - Added `--compare` flag and comparison logic
- `src/askp/executor.py` - Added `compare_suffix` support for distinct filenames
