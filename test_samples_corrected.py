#!/usr/bin/env python3
"""Test all sample projects with corrected CLI commands."""

import subprocess
import sys
from pathlib import Path

def run_command(cmd: list[str], cwd: Path) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def test_simple_chain():
    """Test the simple chain sample project."""
    print("🧪 Testing simple-chain project...")

    project_dir = Path("/workspace/sample-projects/simple-chain")

    # List all tasks
    success, output = run_command(
        ["python", "-m", "warifuri", "list"],
        project_dir
    )

    print(f"📋 List tasks: {'✅' if success else '❌'}")
    if not success:
        print(f"   Error: {output}")
        return False

    print(f"   Output: {output.strip()}")

    # List ready tasks only
    success, output = run_command(
        ["python", "-m", "warifuri", "list", "--ready"],
        project_dir
    )

    print(f"📋 List ready tasks: {'✅' if success else '❌'}")
    if success:
        print(f"   Ready tasks: {output.strip()}")

    # Check foundation task output
    foundation_output = project_dir / "projects/simple/foundation/base.txt"
    print(f"📁 Foundation output exists: {'✅' if foundation_output.exists() else '❌'}")

    # Try to run foundation task
    success, output = run_command(
        ["python", "-m", "warifuri", "run", "--task", "foundation"],
        project_dir
    )

    print(f"🚀 Run foundation: {'✅' if success else '❌'}")
    if not success:
        print(f"   Error: {output}")

    # Check if consumer task can run (should have dependency resolved)
    success, output = run_command(
        ["python", "-m", "warifuri", "run", "--task", "consumer"],
        project_dir
    )

    print(f"🚀 Run consumer: {'✅' if success else '❌'}")
    if not success:
        print(f"   Error: {output}")
    else:
        print(f"   Success: {output.strip()}")

    return True

def test_multi_file():
    """Test the multi-file sample project."""
    print("\n🧪 Testing multi-file project...")

    project_dir = Path("/workspace/sample-projects/multi-file")

    # List tasks
    success, output = run_command(
        ["python", "-m", "warifuri", "list"],
        project_dir
    )

    print(f"📋 List tasks: {'✅' if success else '❌'}")
    if success:
        print(f"   Output: {output.strip()}")

    # Try to run generator task
    success, output = run_command(
        ["python", "-m", "warifuri", "run", "--task", "generator"],
        project_dir
    )

    print(f"🚀 Run generator: {'✅' if success else '❌'}")
    if not success:
        print(f"   Error: {output}")

    # Try to run processor task (depends on generator)
    success, output = run_command(
        ["python", "-m", "warifuri", "run", "--task", "processor"],
        project_dir
    )

    print(f"🚀 Run processor: {'✅' if success else '❌'}")
    if not success:
        print(f"   Error: {output}")
    else:
        print(f"   Success: {output.strip()}")

    return True

def main():
    """Main function."""
    print("🔍 Testing sample projects with correct CLI commands...\n")

    try:
        test_simple_chain()
        test_multi_file()

        print("\n✅ Sample project testing completed!")
        return 0

    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
