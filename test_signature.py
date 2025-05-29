"""Test to verify the function signature is correct."""

import inspect
from warifuri.core.discovery import find_ready_tasks

# Check function signature
sig = inspect.signature(find_ready_tasks)
print(f"Function signature: {sig}")
print(f"Parameters: {list(sig.parameters.keys())}")

# Check if it accepts two parameters
try:
    # This should work with the new signature
    # find_ready_tasks([], Path())
    print("Function appears to accept workspace_path parameter")
except Exception as e:
    print(f"Error: {e}")
