#!/usr/bin/env python3

# Read the entire file
with open('src/askp/utils.py', 'r') as file:
    lines = file.readlines()

# Fix the problematic line (line 100)
lines[99] = '                        key = key.strip(\'"\').strip()\n'

# Write the corrected content back to the file
with open('src/askp/utils.py', 'w') as file:
    file.writelines(lines)

print("File fixed using line-by-line approach")
