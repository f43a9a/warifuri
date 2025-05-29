#!/usr/bin/env python3
"""Check and fix typing issues across the codebase."""

import subprocess
import sys
from pathlib import Path

def run_mypy_check(file_path: str) -> tuple[bool, str]:
    """Run mypy check on a specific file."""
    try:
        result = subprocess.run(
            ["python", "-m", "mypy", "--strict", file_path],
            capture_output=True,
            text=True,
            cwd="/workspace"
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def find_python_files() -> list[Path]:
    """Find all Python files in src/warifuri."""
    src_dir = Path("/workspace/src/warifuri")
    return list(src_dir.rglob("*.py"))

def main():
    """Main function."""
    print("🔍 Checking typing issues across codebase...")

    python_files = find_python_files()

    issues_found = []
    files_checked = 0

    for file_path in python_files:
        if "__pycache__" in str(file_path):
            continue

        files_checked += 1
        success, output = run_mypy_check(str(file_path))

        if not success:
            issues_found.append((file_path, output))
        else:
            print(f"✅ {file_path.relative_to(Path('/workspace'))}")

    print(f"\n📊 Summary:")
    print(f"  Files checked: {files_checked}")
    print(f"  Files with issues: {len(issues_found)}")

    if issues_found:
        print(f"\n❌ Files with typing issues:")
        for file_path, output in issues_found:
            rel_path = file_path.relative_to(Path('/workspace'))
            print(f"\n{rel_path}:")
            # Show only first few lines to avoid spam
            lines = output.strip().split('\n')[:10]
            for line in lines:
                if line.strip():
                    print(f"  {line}")
            if len(output.strip().split('\n')) > 10:
                remaining_lines = len(output.strip().split('\n')) - 10
                print(f"  ... ({remaining_lines} more lines)")

    return 0 if not issues_found else 1

if __name__ == "__main__":
    sys.exit(main())
