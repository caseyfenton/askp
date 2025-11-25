# Agent Mode Testing Guide

## Pre-Testing Checklist

✅ **Completed:**
- [x] Syntax validation (all files compile)
- [x] Import tests (modules load correctly)
- [x] Cache functionality (store/retrieve works)
- [x] Schema validation (test responses validate)
- [x] CLI help text (agent flags visible)

## Live API Testing

### Prerequisites

1. **Perplexity API Key**: Set `PERPLEXITY_API_KEY` environment variable
2. **Model Access**: Ensure access to `sonar` or `sonar-pro` models
3. **Network**: Internet connection for API calls

### Test 1: Basic Agent Mode Query

```bash
# Test agent mode with simple query
askp --agent-mode "What is Python?"
```

**Expected Output:**
- Decision context (outcome, confidence, complexity)
- Entity graph with key facts
- Module index with IDs and tags
- Query UUID for retrieval

**Validation:**
- ✅ Index file created in output directory
- ✅ Full response cached in `~/.askp/agent_cache/<UUID>.json`
- ✅ Output includes query UUID
- ✅ Module count > 0

### Test 2: Retrieve Cached Index

```bash
# Get UUID from previous test output
QUERY_ID="<UUID-from-test-1>"

# Retrieve index only
askp --agent-index --query-id $QUERY_ID
```

**Expected Output:**
- Same index as Test 1 (cached)
- No new API call
- Fast response (<100ms)

**Validation:**
- ✅ No network traffic (check with --debug)
- ✅ Output matches original index
- ✅ No errors about missing cache

### Test 3: Retrieve Specific Module

```bash
# Get module ID from index (usually 1, 2, 3...)
askp --agent-module 1 --query-id $QUERY_ID
```

**Expected Output:**
- Module metadata (id, tags, token_estimate)
- Full raw_content

**Validation:**
- ✅ Content is substantial (>50 chars)
- ✅ Tags match index
- ✅ Token estimate is reasonable

### Test 4: JSON Format Output

```bash
# Query in JSON format
askp --agent-mode --format json "Explain async/await in Python" | jq '.'
```

**Expected Output:**
- Valid JSON (jq parses successfully)
- decision_context object
- entity_graph array
- module_index array

**Validation:**
- ✅ JSON is well-formed
- ✅ All required fields present
- ✅ Arrays have elements

### Test 5: Sonar Pro Model

```bash
# Test with sonar-pro (higher quality, more expensive)
askp --agent-mode --sonar-pro "Complex technical question about distributed systems"
```

**Expected Output:**
- Same structure as sonar
- More detailed entity graph
- More content modules
- Higher token count

**Validation:**
- ✅ Response structure matches schema
- ✅ Cost reflects sonar-pro pricing
- ✅ Content quality is higher

### Test 6: Validation Handling

```bash
# Test with debug mode to see validation
askp --agent-mode --debug "Test query"
```

**Expected Debug Output:**
- "Agent mode enabled: Using structured JSON response format"
- "Structured response parsed successfully"
- Decision/Entities/Modules count
- Validation status

**Validation:**
- ✅ Shows validation passed
- ✅ No parse errors
- ✅ No validation errors

### Test 7: Error Handling - Missing Query ID

```bash
# Try to retrieve without query ID
askp --agent-index
```

**Expected Output:**
```
Error: --query-id is required for agent index/module retrieval
Usage:
  askp --agent-index --query-id <UUID>
  askp --agent-module <ID> --query-id <UUID>
```

**Validation:**
- ✅ Clear error message
- ✅ Exit code != 0
- ✅ Usage examples shown

### Test 8: Error Handling - Invalid Query ID

```bash
# Try with non-existent UUID
askp --agent-index --query-id "00000000-0000-0000-0000-000000000000"
```

**Expected Output:**
```
No cached response found for query ID: 00000000-0000-0000-0000-000000000000
```

**Validation:**
- ✅ Graceful error (no crash)
- ✅ Clear message
- ✅ Exit code != 0

### Test 9: Multiple Queries

```bash
# Test with multiple queries (each gets own UUID)
askp --agent-mode "Python" "JavaScript" "Go"
```

**Expected Output:**
- 3 separate result files
- 3 different query UUIDs
- Each cached independently

**Validation:**
- ✅ All 3 queries processed
- ✅ All 3 cached
- ✅ Can retrieve each independently

### Test 10: Integration with Deep Research

```bash
# Test agent mode with deep research
askp --agent-mode --deep "History of programming languages"
```

**Expected Output:**
- Multiple content modules (one per research angle)
- Higher confidence score
- More comprehensive entity graph

**Validation:**
- ✅ Modules cover different aspects
- ✅ Module tags are diverse
- ✅ Token count is higher

## Performance Benchmarks

### Expected Timings (sonar model)
- Agent mode query: 2-4 seconds
- Index retrieval: <100ms (cached)
- Module retrieval: <100ms (cached)

### Token Usage
- Index only: ~200-500 tokens
- Per module: ~100-300 tokens
- Full response: ~1000-3000 tokens

### Cost Comparison
```
Regular mode (full response): ~3000 tokens = $0.003
Agent mode (index only):      ~400 tokens  = $0.0004

Savings: 87% when only index needed
```

## Troubleshooting

### Issue: "Failed to parse agent response as JSON"

**Possible Causes:**
1. Model returned markdown fences that weren't stripped
2. Model didn't follow schema despite request
3. Model returned thinking/reasoning text

**Solutions:**
- Try with `sonar` instead of reasoning models
- Check raw response with `--debug`
- Lower temperature (--temperature 0.1)

### Issue: "Validation failed: Missing required field"

**Possible Causes:**
1. Model didn't fully conform to schema
2. Partial response due to token limit

**Solutions:**
- Increase `--token_max` (default 4096)
- Simplify query
- Check `metadata.validation_error` for details

### Issue: Cache directory permissions

**Symptoms:**
```
Permission denied: /Users/username/.askp/agent_cache/
```

**Solution:**
```bash
mkdir -p ~/.askp/agent_cache
chmod 755 ~/.askp/agent_cache
```

## Integration Tests

### Test with Autonomous Agent

```python
#!/usr/bin/env python3
"""Test agent-driven workflow"""
import subprocess
import json

# 1. Query in agent mode
result = subprocess.run(
    ["askp", "--agent-mode", "--format", "json", "Python virtual environments"],
    capture_output=True,
    text=True
)

# 2. Parse response
data = json.loads(result.stdout)
assert "decision_context" in data
assert "module_index" in data

# 3. Check decision
outcome = data["decision_context"]["outcome"]
assert outcome in ["definitive", "ambiguous", "insufficient_data"]

# 4. Load relevant modules based on tags
for module in data["module_index"]:
    if "installation" in module["tags"]:
        # Get this specific module
        mod_result = subprocess.run(
            ["askp", "--agent-module", str(module["id"]),
             "--query-id", data["query_id"], "--format", "json"],
            capture_output=True,
            text=True
        )
        mod_data = json.loads(mod_result.stdout)
        print(f"Module {module['id']}: {len(mod_data['raw_content'])} chars")

print("✅ Agent workflow test passed!")
```

## Next Steps

After successful testing:

1. **Update README.md** with agent mode section
2. **Create examples/** directory with sample responses
3. **Add to CI/CD** pipeline
4. **Monitor Perplexity API** for schema changes
5. **Gather feedback** from agent users

## Known Issues / Limitations

1. **Schema Enforcement**: Perplexity may not always follow schema exactly
2. **Token Estimates**: Module token_estimate is approximate
3. **Cache Size**: No automatic cleanup (manual management needed)
4. **Model Compatibility**: Tested only with sonar/sonar-pro (not reasoning models)

## Support

For issues during testing:
- Check `--debug` output for detailed error messages
- Verify API key with `askp --account-status`
- Review cached responses in `~/.askp/agent_cache/`
- File bug report with full debug output
