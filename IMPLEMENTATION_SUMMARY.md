# ASKP Agent Mode Implementation Summary

## Files Created

### 1. `src/askp/agent_response.py` (New)
Complete agent response handling module with:
- `AGENT_JSON_SCHEMA`: JSON schema definition for Perplexity
- `AGENT_SYSTEM_PROMPT`: System prompt for agent-only output
- `AgentResponseCache`: Class for storing/retrieving responses with lazy loading
- Helper functions: `parse_agent_response()`, `validate_agent_response()`, `format_agent_index()`
- `get_response_format_config()`: Returns Perplexity API response_format config

## Files Modified

### 2. `src/askp/api.py`
**Changes:**
- Import agent response utilities
- Add agent mode detection in `search_perplexity()`
- Use `AGENT_SYSTEM_PROMPT` when agent mode enabled
- Add `response_format` parameter to API call with JSON schema
- Parse and validate structured responses
- Store `structured_content` in result metadata
- Add validation status and errors to metadata

### 3. `src/askp/cli.py`
**New CLI Options:**
- `--agent-mode / -A`: Enable agent-centric JSON mode
- `--agent-index`: Retrieve lightweight index from cache
- `--agent-module ID`: Retrieve specific module from cache
- `--query-id UUID`: Query ID for cache retrieval

**Logic Added:**
- Agent mode retrieval handling (lines 154-197)
- Agent mode flag in opts dictionary
- Index/module display formatting

### 4. `src/askp/executor.py`
**Changes in `save_result_file()`:**
- Import `AgentResponseCache` and `format_agent_index`
- Detect agent mode and structured content
- Cache full response using query UUID
- Save lightweight index to file (instead of full content)
- Add query ID and retrieval instructions to output

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ASKP CLI                                │
│  --agent-mode / --agent-index / --agent-module / --query-id     │
└────────────────────┬───────────────────────┬────────────────────┘
                     │                       │
                     ▼                       ▼
         ┌──────────────────────┐  ┌──────────────────────┐
         │   api.search_        │  │  AgentResponseCache  │
         │   perplexity()       │  │  ~/.askp/agent_cache/│
         │                      │  │  <uuid>.json         │
         │  + AGENT_SYSTEM      │  │                      │
         │    _PROMPT           │  │  get_index()         │
         │  + response_format   │  │  get_module(id)      │
         │    JSON schema       │  │  store()             │
         └──────────┬───────────┘  └──────────────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Perplexity API       │
         │ POST /chat/          │
         │   completions        │
         │                      │
         │ response_format:     │
         │   type: json_schema  │
         │   schema: {...}      │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Structured JSON      │
         │ Response             │
         │                      │
         │ - decision_context   │
         │ - entity_graph       │
         │ - content_modules[]  │
         └──────────┬───────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ executor.save_       │
         │   result_file()      │
         │                      │
         │ → Cache full response│
         │ → Save index only    │
         └──────────────────────┘
```

## Usage Patterns

### Pattern 1: Agent Query with Index
```bash
askp --agent-mode "question"
# Returns: index.md with query UUID
```

### Pattern 2: Retrieve Specific Module
```bash
askp --agent-module 2 --query-id <UUID>
# Returns: full module content
```

### Pattern 3: Get Index in JSON
```bash
askp --agent-mode --format json "question"
# Returns: machine-readable index
```

### Pattern 4: Programmatic Access
```python
from askp.agent_response import AgentResponseCache

cache = AgentResponseCache()
index = cache.get_index(query_id)
module = cache.get_module(query_id, module_id=2)
```

## API Contract with Perplexity

### Request Format
```python
{
    "model": "sonar-pro",  # or "sonar"
    "messages": [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_query}
    ],
    "temperature": 0.1-0.3,  # Low for deterministic output
    "response_format": {
        "type": "json_schema",
        "json_schema": {
            "schema": AGENT_JSON_SCHEMA
        }
    }
}
```

### Response Processing
1. Extract `choices[0].message.content`
2. Strip potential markdown fences (```json)
3. Parse as JSON
4. Validate against schema
5. Store in cache with UUID
6. Return lightweight index

## Testing Checklist

- [ ] Agent mode query returns valid index
- [ ] Index includes decision_context, entity_graph, module_index
- [ ] Query UUID is returned in output
- [ ] Full response cached in ~/.askp/agent_cache/
- [ ] --agent-index retrieves cached index
- [ ] --agent-module retrieves specific module
- [ ] JSON format works for all operations
- [ ] Validation catches malformed responses
- [ ] Parse errors handled gracefully
- [ ] Works with sonar and sonar-pro models
- [ ] Compatible with existing flags (--debug, --verbose)

## Known Limitations

1. **Model Compatibility**: Requires Perplexity Sonar models (non-reasoning)
2. **Cache Management**: No automatic cleanup or expiration
3. **Validation**: Basic schema validation only, no deep semantic checks
4. **Error Recovery**: Malformed JSON requires manual inspection
5. **Module Dependencies**: No automatic tracking of module relationships

## Future Improvements

1. Cache expiration and cleanup utilities
2. Module dependency graph
3. Batch module retrieval
4. Enhanced validation with confidence scoring
5. Streaming support for large modules
6. Integration with SEMA semantic search
7. Module filtering by tags in CLI
8. Automatic module pre-loading based on tags

## Integration Notes

### Works With
- ✅ All existing ASKP flags (--debug, --verbose, --format)
- ✅ Multiple queries (each gets separate UUID)
- ✅ Deep research mode (--deep with --agent-mode)
- ✅ SEMA indexing (index files indexed, cache not)

### Not Compatible With
- ❌ Reasoning models (contaminate JSON)
- ❌ --view flag (shows index, not full content)
- ❌ Old cache format (separate cache directory)

## Documentation

- `AGENT_MODE.md`: Complete user documentation with examples
- `IMPLEMENTATION_SUMMARY.md`: This file - technical implementation details
- Code comments: Inline documentation in all modified functions
