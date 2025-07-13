#!/usr/bin/env python3
"""
Test script that directly tests the model/temperature formatting
"""
from rich import print as rprint

# Mock the model info for testing
model_info = {"display_name": "sonar-reasoning"}
model = "sonar-reasoning"
temperature = 0.7

# Test the model info formatting directly
print("\nTesting model info formatting:")

# Original format (before our changes)
print("\nOriginal format:")
rprint(f"Model: {model_info['display_name']}")
print(f"Temperature: {temperature}")

# Our new format (after changes)
print("\nNew format:")
model_type = "(default)" if model == "sonar-reasoning" else ""
rprint(f"Model: {model_info['display_name']} {model_type} | Temp: {temperature}")

print("\nTest completed!")
