#!/usr/bin/env python3

# Read the file content
with open('src/askp/utils.py', 'r') as f:
    lines = f.readlines()

# Replace the problematic line (line 183)
lines[182] = '    """Normalize model name to match Perplexity API format."""\n'

# Write back the fixed content
with open('src/askp/utils.py', 'w') as f:
    f.writelines(lines)

print("Fixed docstring on line 183")
