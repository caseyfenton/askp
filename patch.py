#!/usr/bin/env python3
with open('src/askp/utils.py', 'r') as f:
    content = f.read()

# Fix the specific line with the syntax error
fixed_content = content.replace('key = key.strip(\'"\\\'").strip()', 'key = key.strip("\'\"").strip()')

with open('src/askp/utils.py', 'w') as f:
    f.write(fixed_content)
    
print("Syntax error fixed!")
