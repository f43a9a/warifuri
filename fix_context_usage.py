#!/usr/bin/env python3
"""Fix remaining typing issues in CLI commands."""

import re
import sys
from pathlib import Path

def fix_context_workspace_path_usage(file_path: Path) -> bool:
    """Fix ctx.workspace_path usages that should use ctx.ensure_workspace_path()."""

    if not file_path.exists():
        return False

    content = file_path.read_text()
    original_content = content

    # Pattern to match ctx.workspace_path passed to functions that expect Path
    # Look for function calls with ctx.workspace_path as argument
    patterns = [
        (r'discover_all_projects\(ctx\.workspace_path\)', 'discover_all_projects(ctx.ensure_workspace_path())'),
        (r'_expand_template_to_workspace\(ctx\.workspace_path', '_expand_template_to_workspace(ctx.ensure_workspace_path()'),
        (r'_create_task\(ctx\.workspace_path', '_create_task(ctx.ensure_workspace_path()'),
        (r'_create_project\(ctx\.workspace_path', '_create_project(ctx.ensure_workspace_path()'),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    # Add Any import if needed
    if 'Any' in content and 'from typing import' in content:
        # Find existing typing import line
        typing_import_match = re.search(r'from typing import ([^\n]+)', content)
        if typing_import_match:
            existing_imports = typing_import_match.group(1)
            if 'Any' not in existing_imports:
                new_imports = existing_imports.rstrip() + ', Any'
                content = content.replace(
                    f'from typing import {existing_imports}',
                    f'from typing import {new_imports}'
                )

    if content != original_content:
        file_path.write_text(content)
        print(f"Fixed typing issues in {file_path.relative_to(Path('/workspace'))}")
        return True

    return True

def main():
    """Main function."""
    files_to_fix = [
        "/workspace/src/warifuri/cli/commands/init.py",
        "/workspace/src/warifuri/cli/commands/run.py",
        "/workspace/src/warifuri/cli/commands/list.py",
        "/workspace/src/warifuri/cli/commands/issue.py",
    ]

    print("🔧 Fixing context.workspace_path usages...")

    success_count = 0
    for file_path_str in files_to_fix:
        file_path = Path(file_path_str)
        if fix_context_workspace_path_usage(file_path):
            success_count += 1

    print(f"\n✅ Processed {success_count}/{len(files_to_fix)} files")

    return 0

if __name__ == "__main__":
    sys.exit(main())
