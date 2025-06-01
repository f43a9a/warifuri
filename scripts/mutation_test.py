#!/usr/bin/env python3
"""
Mutation Testing Helper Script for Warifuri

This script facilitates running mutmut (mutation testing) and provides
utilities for analyzing mutation test results.

Usage:
    python scripts/mutation_test.py [command]

Commands:
    run     - Run mutation tests (local development only)
    status  - Show current mutation test status
    results - Show detailed results of last mutation run
    check   - Check if mutation score meets threshold (CI-friendly)
    clean   - Clean mutation testing cache
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple


class MutationTestRunner:
    """Handles mutation testing operations with mutmut"""

    def __init__(self, workspace_root: Path) -> None:
        self.workspace_root = workspace_root
        self.mutmut_cache = workspace_root / ".mutmut-cache"
        self.config_file = workspace_root / ".mutmut.toml"

    def run_tests(self, dry_run: bool = False) -> Tuple[bool, str]:
        """Run mutation tests (local development only)"""
        if dry_run:
            return True, "DRY RUN: Would run mutation tests with mutmut"

        print("🧬 Starting mutation testing with mutmut...")
        print("⚠️  This may take a while. Use Ctrl+C to interrupt.")

        try:
            # First ensure tests pass normally
            print("\n📋 1. Running normal tests first...")
            test_result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-x", "--tb=short", "--no-cov"],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )

            if test_result.returncode != 0:
                return False, f"❌ Normal tests failed, cannot proceed:\n{test_result.stdout}\n{test_result.stderr}"

            print("✅ Normal tests passed, proceeding with mutation testing...")

            # Run mutation tests
            print("\n🧬 2. Running mutation tests...")
            mutmut_result = subprocess.run(
                ["mutmut", "run"],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )

            return True, f"Mutation testing completed.\nOutput:\n{mutmut_result.stdout}\n{mutmut_result.stderr}"

        except Exception as e:
            return False, f"❌ Error running mutation tests: {e}"

    def get_status(self) -> Tuple[bool, str]:
        """Get current mutation test status"""
        try:
            # Use mutmut results to get status information
            result = subprocess.run(
                ["mutmut", "results"],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return True, f"Mutation test cache found:\n{result.stdout.strip()}"
            else:
                return False, "No mutation test data found. Run 'python scripts/mutation_test.py run' first."

        except Exception as e:
            return False, f"Error getting status: {e}"

    def get_results(self) -> Tuple[bool, Dict[str, int]]:
        """Get detailed mutation test results"""
        try:
            result = subprocess.run(
                ["mutmut", "results"],
                cwd=self.workspace_root,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return False, {"error": "No results available"}

            # Parse mutmut results output
            lines = result.stdout.strip().split('\n')
            results = {}

            for line in lines:
                if 'killed' in line.lower():
                    # Extract numbers from lines like "123 killed"
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == 'killed':
                        results['killed'] = int(parts[0])
                elif 'survived' in line.lower():
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == 'survived':
                        results['survived'] = int(parts[0])
                elif 'timeout' in line.lower():
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == 'timeout':
                        results['timeout'] = int(parts[0])
                elif 'suspicious' in line.lower():
                    parts = line.split()
                    if len(parts) >= 2 and parts[1] == 'suspicious':
                        results['suspicious'] = int(parts[0])

            return True, results

        except Exception as e:
            return False, {"error": str(e)}

    def check_score_threshold(self, threshold: float = 90.0) -> Tuple[bool, str, Optional[float]]:
        """Check if mutation score meets threshold (CI-friendly)"""
        success, results = self.get_results()

        if not success:
            return False, "❌ No mutation test results available", None

        if 'error' in results:
            return False, f"❌ Error getting results: {results['error']}", None

        killed = results.get('killed', 0)
        survived = results.get('survived', 0)
        total = killed + survived

        if total == 0:
            return False, "❌ No mutation tests found", None

        score = (killed / total) * 100
        passed = score >= threshold

        status = "✅" if passed else "⚠️"
        message = f"{status} Mutation score: {score:.1f}% ({killed}/{total} killed), threshold: {threshold}%"

        return passed, message, score

    def clean_cache(self) -> Tuple[bool, str]:
        """Clean mutation testing cache"""
        try:
            if self.mutmut_cache.exists():
                import shutil
                shutil.rmtree(self.mutmut_cache)
                return True, "✅ Mutation test cache cleaned"
            else:
                return True, "ℹ️  No mutation test cache found"

        except Exception as e:
            return False, f"❌ Error cleaning cache: {e}"


def main() -> None:
    """Main CLI entry point"""
    workspace_root = Path(__file__).parent.parent
    runner = MutationTestRunner(workspace_root)

    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == "run":
        dry_run = "--dry-run" in sys.argv
        success, message = runner.run_tests(dry_run=dry_run)
        print(message)
        if not success:
            sys.exit(1)

    elif command == "status":
        success, message = runner.get_status()
        print(message)
        if not success:
            sys.exit(1)

    elif command == "results":
        success, results = runner.get_results()
        if success and 'error' not in results:
            print("🧬 Mutation Test Results:")
            print(f"  Killed: {results.get('killed', 0)}")
            print(f"  Survived: {results.get('survived', 0)}")
            print(f"  Timeout: {results.get('timeout', 0)}")
            print(f"  Suspicious: {results.get('suspicious', 0)}")

            total = results.get('killed', 0) + results.get('survived', 0)
            if total > 0:
                score = (results.get('killed', 0) / total) * 100
                print(f"  Score: {score:.1f}%")
        else:
            print(f"❌ {results.get('error', 'Unknown error')}")
            sys.exit(1)

    elif command == "check":
        threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 90.0
        passed, message, score = runner.check_score_threshold(threshold)
        print(message)
        if not passed:
            sys.exit(1)

    elif command == "clean":
        success, message = runner.clean_cache()
        print(message)
        if not success:
            sys.exit(1)

    else:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
