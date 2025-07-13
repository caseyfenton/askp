#!/usr/bin/env python3

# Read the file content
with open('src/askp/utils.py', 'r') as f:
    lines = f.readlines()

# Replace the problematic rprint with fixed structure
lines[126:134] = [
    '    \n',
    '    # If no API key was found, display an error message\n',
    '    if not key:\n',
    '        file_locations = "     * ~/.env (recommended)\\n     * ~/.askp/.env\\n     * ~/.perplexity/.env"\n',
    '        rprint(Panel(f"""[bold red]ERROR: Perplexity API Key Not Found or Invalid[/bold red]\n',
    '\n',
    '[yellow]To use ASKP, you need a valid Perplexity API key. Please follow these steps:[/yellow]\n',
    '\n'
]

# Write back the fixed content
with open('src/askp/utils.py', 'w') as f:
    f.writelines(lines)

print("Fixed rprint syntax error on lines 127-133")
