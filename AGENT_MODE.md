# ASKP Agent Mode - Machine-Centric JSON Responses

## Overview

Agent Mode transforms ASKP into a headless JSON data engine for autonomous agents. Instead of human-readable markdown, it returns structured, machine-optimized JSON with lazy-loadable content modules.

## Key Features

- **Structured JSON Schema**: Responses conform to a strict schema designed for agent consumption
- **Lazy Loading**: Heavy content is separated into modules that can be loaded on-demand
- **Lightweight Index**: Initial response contains only decision context and entity facts
- **Query Caching**: Full responses cached for module retrieval without re-querying Perplexity

## Response Structure

### Decision Context (Always Loaded)
Small state header with immediate decision-making data:
- `outcome`: "definitive" | "ambiguous" | "insufficient_data"
- `confidence`: 0.0 - 1.0
- `complexity`: "low" | "medium" | "high"

### Entity Graph (Always Loaded)
Key-value facts as structured data:
```json
{
  "key": "python_version",
  "value": "3.11",
  "data_type": "string"
}
```

### Content Modules (Lazy Loaded)
Heavy text blocks with metadata for selective loading:
```json
{
  "id": 1,
  "tags": ["installation", "pip"],
  "token_estimate": 150,
  "raw_content": "..."
}
```

## Usage

### Basic Agent Mode Query

```bash
# Get lightweight index only (decision context + entity graph + module index)
askp --agent-mode "How do I install Python 3.11?"
```

**Output:**
```markdown
## Decision Context
- Outcome: definitive
- Confidence: 0.95
- Complexity: low

## Entity Graph
- python_version: 3.11 (string)
- installation_method: official_installer (string)
- supported_platforms: Windows,macOS,Linux (string)

## Content Modules
- Module 1: [installation, windows] (~200 tokens)
- Module 2: [installation, macos] (~180 tokens)
- Module 3: [installation, linux] (~220 tokens)
- Module 4: [verification, testing] (~100 tokens)

---
**Query ID:** `a1b2c3d4-e5f6-7890-abcd-ef1234567890`

Use this ID to retrieve modules:
```bash
askp --agent-module <ID> --query-id a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### Retrieve Specific Module

```bash
# Get full content of module 2 (macOS installation)
askp --agent-module 2 --query-id a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Output:**
```markdown
## Module 2
Tags: installation, macos
Tokens: ~180

### Content

To install Python 3.11 on macOS:

1. Download the official installer from python.org
2. Run the .pkg file
3. Follow the installation wizard
...
```

### Get Index in JSON Format

```bash
# Get machine-readable index
askp --agent-mode --format json "How do I install Python 3.11?"
```

**Output:**
```json
{
  "decision_context": {
    "outcome": "definitive",
    "confidence": 0.95,
    "complexity": "low"
  },
  "entity_graph": [
    {"key": "python_version", "value": "3.11", "data_type": "string"},
    {"key": "installation_method", "value": "official_installer", "data_type": "string"}
  ],
  "module_index": [
    {"id": 1, "tags": ["installation", "windows"], "token_estimate": 200},
    {"id": 2, "tags": ["installation", "macos"], "token_estimate": 180},
    {"id": 3, "tags": ["installation", "linux"], "token_estimate": 220},
    {"id": 4, "tags": ["verification", "testing"], "token_estimate": 100}
  ]
}
```

## Agent Workflow Example

```bash
#!/bin/bash
# Autonomous agent workflow

# 1. Get index to understand the response
QUERY_ID=$(askp --agent-mode --format json "Explain async/await in Python" | jq -r '.query_id')

# 2. Parse decision context to determine if answer is satisfactory
OUTCOME=$(askp --agent-index --query-id $QUERY_ID --format json | jq -r '.decision_context.outcome')

if [ "$OUTCOME" == "definitive" ]; then
  # 3. Scan module index for relevant tags
  MODULE_ID=$(askp --agent-index --query-id $QUERY_ID --format json | \
    jq -r '.module_index[] | select(.tags | contains(["examples"])) | .id')

  # 4. Load only the module we need
  askp --agent-module $MODULE_ID --query-id $QUERY_ID --format json
fi
```

## API Request Details

When `--agent-mode` is enabled, ASKP:

1. Sends system prompt optimized for agents:
   ```
   You are a headless JSON data engine for autonomous agents.
   You output only raw JSON that strictly conforms to the provided schema.
   You never talk to humans, never use markdown, and you encode all knowledge
   into the schema fields instead of asking clarifying questions.
   ```

2. Includes `response_format` parameter:
   ```json
   {
     "type": "json_schema",
     "json_schema": {
       "schema": { ... }
     }
   }
   ```

3. Uses Perplexity Sonar models (non-reasoning to avoid `<think>` blocks)

## Cache Location

Agent responses are cached in `~/.askp/agent_cache/` with the query UUID as filename:

```
~/.askp/agent_cache/
├── a1b2c3d4-e5f6-7890-abcd-ef1234567890.json
├── b2c3d4e5-f6g7-8901-bcde-fg2345678901.json
└── ...
```

## Best Practices

### For Agents

1. **Always start with the index**: Parse decision_context and entity_graph first
2. **Load modules selectively**: Only retrieve modules you need based on tags/estimates
3. **Check validation**: Verify `metadata.validated` is true before trusting structure
4. **Use JSON format**: `--format json` for easier parsing

### Model Selection

- ✅ Use `sonar` or `sonar-pro` for agent mode (clean JSON, no thinking blocks)
- ❌ Avoid reasoning models (may contaminate JSON with `<think>` tags)

### Token Optimization

```bash
# Index: ~500 tokens
askp --agent-mode "complex query"

# Specific module: ~200 tokens
askp --agent-module 1 --query-id <UUID>

# vs. Full response: ~2000+ tokens
askp "complex query"  # Regular mode loads everything
```

## Error Handling

### Validation Failures

```json
{
  "metadata": {
    "validated": false,
    "validation_error": "Missing required field: outcome"
  }
}
```

Handle gracefully - response may be partially usable or require fallback to regular mode.

### Parse Errors

```json
{
  "metadata": {
    "parse_error": "Failed to parse agent response as JSON: ..."
  }
}
```

Perplexity may have returned non-JSON despite schema. Check `content` field for raw response.

## Integration with Existing Tools

### With SEMA Cache

Agent mode responses are NOT indexed by SEMA (they're in separate cache). Use `--query-id` for retrieval, not SEMA search.

### With Deep Research

Agent mode is compatible with deep research:

```bash
askp --agent-mode --deep "comprehensive topic"
```

Each sub-query returns structured JSON modules.

## Future Enhancements

- [ ] Module filtering by tags in CLI
- [ ] Batch module retrieval
- [ ] Module dependency graph
- [ ] Cache expiration and cleanup
- [ ] Streaming module loading

## Support

For issues or questions:
- GitHub: https://github.com/caseyfenton/askp/issues
- Documentation: https://github.com/caseyfenton/askp#readme
