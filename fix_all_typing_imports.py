#!/usr/bin/env python3
"""Fix missing typing imports in CLI modules."""

import re
import sys
from pathlib import Path

def fix_typing_imports_in_file(file_path: Path) -> bool:
    """Fix missing typing imports in a specific file."""

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return False

    content = file_path.read_text()
    lines = content.split('\n')

    # Check which typing imports are needed
    needed_imports = set()
    if re.search(r'\bDict\b', content):
        needed_imports.add('Dict')
    if re.search(r'\bList\b', content):
        needed_imports.add('List')
    if re.search(r'\bOptional\b', content):
        needed_imports.add('Optional')

    if not needed_imports:
        return True  # No imports needed

    # Check if typing imports already exist
    has_typing_import = False
    typing_line_index = None

    for i, line in enumerate(lines):
        if line.strip().startswith("from typing import"):
            has_typing_import = True
            typing_line_index = i
            # Parse existing imports
            match = re.search(r"from typing import (.+)", line)
            if match:
                existing_imports = [imp.strip() for imp in match.group(1).split(',')]
                for imp in existing_imports:
                    needed_imports.discard(imp)
            break

    if not needed_imports:
        return True  # All needed imports already exist

    # Find insertion point
    insert_index = None

    # Look for pathlib import
    for i, line in enumerate(lines):
        if line.strip() == "from pathlib import Path":
            insert_index = i + 1
            break

    # If no pathlib, look for any import
    if insert_index is None:
        for i, line in enumerate(lines):
            if line.strip().startswith("from ") and "import" in line:
                insert_index = i + 1
                break

    # If no imports found, look for first function/class
    if insert_index is None:
        for i, line in enumerate(lines):
            if line.strip().startswith(("def ", "class ", "@")):
                insert_index = i
                break

    if insert_index is None:
        print(f"Could not find insertion point in {file_path}")
        return False

    # Add or update typing import
    import_line = f"from typing import {', '.join(sorted(needed_imports))}"

    if has_typing_import and typing_line_index is not None:
        # Update existing line
        existing_line = lines[typing_line_index]
        match = re.search(r"from typing import (.+)", existing_line)
        if match:
            existing_imports = [imp.strip() for imp in match.group(1).split(',')]
            all_imports = sorted(set(existing_imports) | needed_imports)
            lines[typing_line_index] = f"from typing import {', '.join(all_imports)}"
    else:
        # Insert new line
        lines.insert(insert_index, import_line)

    # Write back
    file_path.write_text('\n'.join(lines))
    print(f"Fixed typing imports in {file_path.relative_to(Path('/workspace'))}")

    return True

def main():
    """Main function."""
    files_to_fix = [
        "/workspace/src/warifuri/cli/context.py",
        "/workspace/src/warifuri/cli/commands/init.py",
        "/workspace/src/warifuri/cli/commands/issue.py",
        "/workspace/src/warifuri/cli/commands/list.py",
        "/workspace/src/warifuri/cli/commands/run.py",
    ]

    print("🔧 Fixing typing imports...")

    success_count = 0
    for file_path_str in files_to_fix:
        file_path = Path(file_path_str)
        if fix_typing_imports_in_file(file_path):
            success_count += 1
        else:
            print(f"❌ Failed to fix {file_path}")

    print(f"\n✅ Fixed {success_count}/{len(files_to_fix)} files")

    return 0 if success_count == len(files_to_fix) else 1

if __name__ == "__main__":
    sys.exit(main())
