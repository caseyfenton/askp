# Agent Mode Quick Start

## 30-Second Overview

Agent Mode returns lightweight, structured JSON instead of full markdown responses. Perfect for autonomous agents that need to minimize context usage.

## Installation

```bash
# Already installed if you have askp >= 2.4.5
# No additional dependencies needed
```

## 3-Step Workflow

### 1. Query (Get Index)

```bash
askp --agent-mode "your question here"
```

**Returns:**
- Decision context (outcome, confidence, complexity)
- Entity facts (key-value pairs)
- Module index (IDs, tags, token estimates)
- **Query UUID** (for retrieval)

### 2. Review Index

```markdown
## Decision Context
- Outcome: definitive
- Confidence: 0.95
- Complexity: low

## Content Modules
- Module 1: [installation, windows] (~200 tokens)
- Module 2: [installation, macos] (~180 tokens)
- Module 3: [configuration] (~150 tokens)

Query ID: `abc123...`
```

### 3. Load Module (If Needed)

```bash
askp --agent-module 2 --query-id abc123...
```

**Returns:**
Full content of module 2 (macOS installation)

## Common Use Cases

### For Agents: Minimize Context

```bash
# Traditional: Load 3000 tokens
askp "complex question"

# Agent Mode: Load 400 tokens (87% savings)
askp --agent-mode "complex question"

# Later: Load specific 200-token module
askp --agent-module 3 --query-id <UUID>
```

### For Humans: Fast Overview

```bash
# Get quick summary
askp --agent-mode "Docker vs Kubernetes"

# Scan module tags to find what you need
# Load only relevant modules
```

## Flags Cheat Sheet

| Flag | Short | Purpose |
|------|-------|---------|
| `--agent-mode` | `-A` | Enable agent JSON mode |
| `--agent-index` | - | Get cached index only |
| `--agent-module <ID>` | - | Get specific module |
| `--query-id <UUID>` | - | Cache key (required for retrieval) |
| `--format json` | `-f json` | JSON output instead of markdown |

## Example Workflows

### Bash Script

```bash
#!/bin/bash
# Get index, parse decision, load modules

# Query
RESULT=$(askp --agent-mode --format json "Python virtual environments")
QUERY_ID=$(echo "$RESULT" | jq -r '.query_id')
OUTCOME=$(echo "$RESULT" | jq -r '.decision_context.outcome')

if [ "$OUTCOME" == "definitive" ]; then
  # High confidence - load installation module
  askp --agent-module 1 --query-id "$QUERY_ID" --format json
fi
```

### Python Script

```python
import subprocess
import json

# Query
result = subprocess.run(
    ["askp", "--agent-mode", "--format", "json", "FastAPI tutorial"],
    capture_output=True, text=True
)
data = json.loads(result.stdout)

# Check confidence
if data["decision_context"]["confidence"] > 0.8:
    # Load examples module
    for mod in data["module_index"]:
        if "examples" in mod["tags"]:
            subprocess.run([
                "askp", "--agent-module", str(mod["id"]),
                "--query-id", data["query_id"]
            ])
```

## Pro Tips

1. **Use JSON format** for easy parsing:
   ```bash
   askp --agent-mode --format json "query" | jq '.entity_graph'
   ```

2. **Filter modules by tags**:
   ```bash
   jq '.module_index[] | select(.tags | contains(["examples"]))' index.json
   ```

3. **Batch queries, selective loading**:
   ```bash
   for q in "Python" "JavaScript" "Go"; do
     askp --agent-mode "$q"  # All cached
   done
   # Later: load only modules you need
   ```

4. **Check cache size**:
   ```bash
   du -sh ~/.askp/agent_cache/
   ```

## Troubleshooting

### No query UUID in output?

Make sure you're using `--agent-mode`:
```bash
askp --agent-mode "query"  # ✅ Has UUID
askp "query"                # ❌ No UUID (regular mode)
```

### "No cached response found"?

Check if query ID is correct:
```bash
ls ~/.askp/agent_cache/
# Find your UUID, then:
askp --agent-index --query-id <correct-UUID>
```

### Want to see full response?

Use regular mode:
```bash
askp "query"  # Full response, no agent mode
```

## Learn More

- Full docs: `AGENT_MODE.md`
- Testing guide: `TESTING_GUIDE.md`
- Implementation: `IMPLEMENTATION_SUMMARY.md`

## Quick Reference Card

```
┌─────────────────────────────────────────────────────┐
│ ASKP AGENT MODE QUICK REFERENCE                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│ 1. GET INDEX                                        │
│    askp --agent-mode "question"                     │
│    → Returns lightweight index + UUID               │
│                                                     │
│ 2. LOAD MODULE                                      │
│    askp --agent-module <ID> --query-id <UUID>       │
│    → Returns full module content                    │
│                                                     │
│ 3. GET INDEX ONLY (from cache)                      │
│    askp --agent-index --query-id <UUID>             │
│    → No API call, instant                           │
│                                                     │
│ FORMATS:                                            │
│    --format markdown  (default, readable)           │
│    --format json      (parseable)                   │
│                                                     │
│ CACHE:                                              │
│    ~/.askp/agent_cache/<UUID>.json                  │
│                                                     │
└─────────────────────────────────────────────────────┘
```
