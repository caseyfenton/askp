#!/usr/bin/env python3

# Read the entire file
with open('src/askp/utils.py', 'r') as file:
    content = file.read()

# Replace Unicode bullet characters with standard ASCII
fixed_content = content.replace('•', '*')

# Write the corrected content back to the file
with open('src/askp/utils.py', 'w') as file:
    file.write(fixed_content)

print("Unicode bullet characters replaced with ASCII '*'")
