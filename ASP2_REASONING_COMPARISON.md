# ASP2 - Reasoning Comparison Mode

## Overview

ASP2 (Advanced Search Protocol 2) compares **Q&A mode** (direct answers) with **Logic Chain mode** (step-by-step reasoning), allowing you to see how reasoning models think through problems.

## Usage

```bash
askp --compare-reasoning "your question here"
```

## What It Does

1. Runs query in **Q&A mode** (sonar) - fast, direct answers
2. Runs query in **Logic Chain mode** (sonar-reasoning-pro) - shows internal reasoning process
3. Generates two output files for side-by-side comparison
4. Displays performance metrics (tokens, cost, multiplier)

## Example

```bash
askp --compare-reasoning "Why is the sky blue?"
```

**Output:**
```
🧠 ASP2 COMPARISON MODE - Regular Q&A vs Logic Chain (Reasoning)
   Comparing: sonar (Q&A) vs sonar-reasoning-pro (logic chain)
   Please wait...

📝 Running REGULAR Q&A mode (sonar)...
Saved: /path/to/query_*_qa.md

🧠 Running REASONING logic chain mode (sonar-reasoning-pro)...
⚠️  Note: Reasoning models are 10-20x more expensive
Saved: /path/to/query_*_reasoning.md

======================================================================
🧠 ASP2 COMPARISON SUMMARY - Q&A vs Logic Chain
======================================================================

✅ Both modes completed successfully!

📁 Output files:
   Q&A (sonar):             /path/to/query_*_qa.md
   Reasoning (logic chain): /path/to/query_*_reasoning.md

📈 Performance comparison:
   Q&A:       420 tokens | $0.0004
   Reasoning: 850 tokens | $0.0085
   Cost Multiplier: 21.3x

💡 Reasoning model provides step-by-step logic chain thinking.
   Use for complex analysis, multi-step reasoning, or debugging logic.
   Regular Q&A model is faster and cheaper for simple fact retrieval.
======================================================================
```

## File Structure

### Q&A Mode Output (1664 bytes)
- Direct answer immediately
- Concise explanation
- Key supporting points
- Citations
- No internal reasoning visible

**Example:**
```markdown
The sky is blue because molecules in Earth's atmosphere scatter
sunlight, and blue light is scattered more than other colors due
to its shorter wavelength...

Key details supporting this explanation:
- Sunlight appears white but is composed of multiple colors...
- Rayleigh scattering occurs when air molecules...
```

### Reasoning Mode Output (3288 bytes, ~2x larger)
- Starts with `<think>` block showing internal reasoning
- Analyzes query type and requirements
- Plans response structure
- Considers what to include/exclude
- Then provides detailed answer
- More comprehensive and structured

**Example:**
```markdown
<think>
This is a straightforward science question about why the sky is blue.
Let me analyze what I need to do:

1. This falls under "Science and Math" in the query type rules
2. I need to provide a clear, comprehensive answer
3. I should cite the relevant search results naturally
4. I should use proper formatting with headers
5. I should avoid hedging language

The key points from the search results:
- White light from the sun contains all colors
- Blue light has shorter wavelengths and scatters more
- This phenomenon is called Rayleigh scattering
...
</think>

The sky appears blue because of how sunlight interacts with
Earth's atmosphere through a process called **Rayleigh scattering**...
```

## Key Differences: Q&A vs Logic Chain

| Feature | Q&A Mode (sonar) | Logic Chain (reasoning-pro) |
|---------|------------------|------------------------------|
| **Thinking Process** | Hidden | Visible in `<think>` blocks |
| **Response Style** | Direct answer | Analyzed + planned response |
| **Detail Level** | Concise | Comprehensive |
| **File Size** | ~1600 bytes | ~3200 bytes (2x) |
| **Tokens** | ~420 | ~850 (2x) |
| **Cost** | $0.0004 | $0.0085 (21x) |
| **Speed** | Fast | Slower |
| **Best For** | Simple facts | Complex reasoning |

## When to Use Each Mode

### Use Q&A Mode (sonar) when:
- You need quick facts
- Question is straightforward
- Cost matters
- Speed is important
- Simple lookup or definition

### Use Logic Chain (reasoning-pro) when:
- Complex multi-step problems
- Need to understand the reasoning
- Debugging logical issues
- Comparing approaches
- Educational/learning purposes
- Quality matters more than cost

## Use Cases

### 1. **Debugging Logic**
Compare how Q&A answers vs how reasoning thinks through a problem
```bash
askp --compare-reasoning "How do I fix this authentication bug?"
```

### 2. **Educational Purposes**
See the step-by-step thinking process
```bash
askp --compare-reasoning "Explain quantum entanglement"
```

### 3. **Complex Analysis**
For multi-step reasoning tasks
```bash
askp --compare-reasoning "What are the pros and cons of microservices vs monoliths?"
```

### 4. **Comparing Outputs**
During development to understand model behavior
```bash
askp --compare-reasoning "Best practices for API design"
```

## Cost Considerations

⚠️ **Important:** Reasoning models are 10-20x more expensive than regular models.

**Example costs (typical query):**
- Q&A mode: $0.0004 (0.04 cents)
- Reasoning mode: $0.0085 (0.85 cents)
- **Multiplier: 21x**

**Running comparison mode costs BOTH**, so:
- Single comparison: ~$0.0089
- 10 comparisons: ~$0.089
- 100 comparisons: ~$0.89

Use comparison mode for:
- Development and testing
- Understanding model differences
- Educational purposes
- Complex problems where reasoning helps

Avoid for:
- Production queries (unless reasoning is needed)
- Simple fact lookups
- High-volume operations
- Cost-sensitive applications

## Limitations

- Only works with **single queries** (not multiple queries or deep research)
- Runs two API calls (doubles the API cost)
- Cannot be combined with other comparison modes (--compare, --agent-mode)
- Reasoning models take longer to respond

## Implementation Details

**Added in:** 2025-12-02
**Version:** 2.4.6 (pending)

**Files Modified:**
- `src/askp/cli.py` - Added `--compare-reasoning` flag and ASP2 logic

**Models Used:**
- Q&A: `sonar` (basic Perplexity model)
- Reasoning: `sonar-reasoning-pro` (chain-of-thought model)

**File Naming:**
- Q&A output: `query_*_qa.md`
- Reasoning output: `query_*_reasoning.md`

## Related Documentation

- [AGENT_MODE.md](AGENT_MODE.md) - JSON structured responses
- [COMPARISON_MODE.md](COMPARISON_MODE.md) - Traditional vs Agent comparison
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing procedures

## Technical Notes

The reasoning model uses Perplexity's `sonar-reasoning-pro` which includes:
- Chain-of-thought processing
- Internal reasoning visible in `<think>` blocks
- More thorough analysis
- Step-by-step logic chains
- Better handling of complex queries

The `<think>` blocks are preserved in the output to show the reasoning process, making it valuable for:
- Understanding model behavior
- Educational purposes
- Debugging complex queries
- Comparing reasoning approaches

---

**ASP2 = Advanced Search Protocol 2**
- ASP1 = Regular Q&A mode (direct answers)
- ASP2 = Logic Chain mode (reasoning with visible thinking)
