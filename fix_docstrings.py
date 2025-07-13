#!/usr/bin/env python3

# Create a new file that will have the fixed content
with open('src/askp/utils.py', 'r') as file:
    lines = file.readlines()

# Create a new Python file to test the syntax
with open('test_syntax.py', 'w') as test_file:
    test_file.writelines(lines)

# Try to compile the file to check for syntax errors
import py_compile
try:
    py_compile.compile('test_syntax.py', doraise=True)
    print("No syntax errors found when compiling!")
except py_compile.PyCompileError as e:
    print(f"Compilation error: {e}")

# Clean up
import os
os.remove('test_syntax.py')
