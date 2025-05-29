#!/usr/bin/env python3
"""Fix missing typing imports in execution.py."""

import sys
from pathlib import Path

def fix_typing_imports():
    """Fix missing typing imports in execution.py."""

    execution_file = Path("/workspace/src/warifuri/core/execution.py")

    if not execution_file.exists():
        print(f"File not found: {execution_file}")
        return False

    # Read current content
    content = execution_file.read_text()
    lines = content.split('\n')

    # Find the pathlib import line and insert typing import after it
    insert_index = None
    has_typing_import = False

    for i, line in enumerate(lines):
        if line.strip().startswith("from typing import"):
            has_typing_import = True
            break
        if line.strip() == "from pathlib import Path":
            insert_index = i + 1

    if has_typing_import:
        print("Typing imports already exist")
        return True

    if insert_index is None:
        print("Could not find pathlib import line")
        return False

    # Insert the typing import
    lines.insert(insert_index, "from typing import Dict, List, Optional")

    # Write back
    execution_file.write_text('\n'.join(lines))
    print("Added typing imports to execution.py")

    return True

def main():
    """Main function."""
    if fix_typing_imports():
        print("✅ Fixed typing imports")
        return 0
    else:
        print("❌ Failed to fix typing imports")
        return 1

if __name__ == "__main__":
    sys.exit(main())
