#!/usr/bin/env python3

# Read the file content
with open('src/askp/utils.py', 'r') as f:
    lines = f.readlines()

# Replace the problematic docstring with fixed triple quotes
lines[438] = '    """\n'
lines[439] = '    Get the default output directory.\n'
lines[440] = '    Tries to create perplexity_results in the current directory.\n'
lines[441] = '    If that fails due to permissions, it falls back to a directory in the users home folder.\n'
lines[442] = '    """\n'

# Write back the fixed content
with open('src/askp/utils.py', 'w') as f:
    f.writelines(lines)

print("Fixed docstring on lines 438-442")
