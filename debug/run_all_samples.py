#!/usr/bin/env python3
"""
Run all sample projects to test warifuri functionality.
Executes each sample project and reports results.
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add src to path for importing warifuri modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def run_warifuri_command(command: List[str], cwd: Path) -> Tuple[bool, str, str]:
    """Run a warifuri command and return success, stdout, stderr."""
    try:
        result = subprocess.run(
            ["python", "-m", "warifuri"] + command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)


def test_sample_project(sample_name: str, sample_path: Path) -> Dict[str, Any]:
    """Test a single sample project."""
    print(f"\nTesting {sample_name}...")
    print("-" * 50)

    test_results = {
        "sample_name": sample_name,
        "success": True,
        "tests": {},
        "errors": []
    }

    original_cwd = Path.cwd()

    try:
        import os
        os.chdir(sample_path)

        # Test 1: List tasks
        print("1. Testing 'warifuri list'...")
        success, stdout, stderr = run_warifuri_command(["list"], sample_path)
        test_results["tests"]["list"] = {
            "success": success,
            "stdout": stdout,
            "stderr": stderr
        }
        if success:
            print("   ✓ PASSED")
        else:
            print(f"   ✗ FAILED: {stderr}")
            test_results["errors"].append(f"list command failed: {stderr}")
            test_results["success"] = False

        # Test 2: List with status
        print("2. Testing 'warifuri list --show-status'...")
        success, stdout, stderr = run_warifuri_command(["list", "--show-status"], sample_path)
        test_results["tests"]["list_status"] = {
            "success": success,
            "stdout": stdout,
            "stderr": stderr
        }
        if success:
            print("   ✓ PASSED")
        else:
            print(f"   ✗ FAILED: {stderr}")
            test_results["errors"].append(f"list --show-status failed: {stderr}")
            test_results["success"] = False

        # Test 3: Run all tasks
        print("3. Testing 'warifuri run'...")
        success, stdout, stderr = run_warifuri_command(["run"], sample_path)
        test_results["tests"]["run"] = {
            "success": success,
            "stdout": stdout,
            "stderr": stderr
        }
        if success:
            print("   ✓ PASSED")
        else:
            print(f"   ✗ FAILED: {stderr}")
            test_results["errors"].append(f"run command failed: {stderr}")
            test_results["success"] = False

        # Test 4: Verify output files
        print("4. Checking output files...")
        output_files_exist = True
        expected_outputs = get_expected_outputs(sample_name)

        for output_file in expected_outputs:
            if not (sample_path / output_file).exists():
                print(f"   ✗ Missing output file: {output_file}")
                test_results["errors"].append(f"Missing output file: {output_file}")
                output_files_exist = False
            else:
                size = (sample_path / output_file).stat().st_size
                print(f"   ✓ {output_file} ({size} bytes)")

        test_results["tests"]["output_files"] = {
            "success": output_files_exist,
            "expected": expected_outputs,
            "found": [f for f in expected_outputs if (sample_path / f).exists()]
        }

        if not output_files_exist:
            test_results["success"] = False

        # Test 5: Status after completion
        print("5. Testing final status...")
        success, stdout, stderr = run_warifuri_command(["list", "--show-status"], sample_path)
        test_results["tests"]["final_status"] = {
            "success": success,
            "stdout": stdout,
            "stderr": stderr
        }

        if success:
            # Check if all tasks are completed
            if "COMPLETED" in stdout:
                print("   ✓ Tasks completed successfully")
            else:
                print("   ⚠ Some tasks may not be completed")
                test_results["errors"].append("Not all tasks completed")
        else:
            print(f"   ✗ FAILED: {stderr}")
            test_results["errors"].append(f"final status check failed: {stderr}")
            test_results["success"] = False

    except Exception as e:
        print(f"   ✗ EXCEPTION: {str(e)}")
        test_results["errors"].append(f"Exception during testing: {str(e)}")
        test_results["success"] = False

    finally:
        os.chdir(original_cwd)

    return test_results


def get_expected_outputs(sample_name: str) -> List[str]:
    """Get expected output files for each sample project."""
    outputs = {
        "simple-chain": ["base.txt", "processed.txt"],
        "multi-file": ["data1.txt", "data2.txt", "config.json", "summary.txt"],
        "cross-project": ["shared.conf", "version.txt", "core_lib.json", "app_output.txt", "validation_report.txt"]
    }
    return outputs.get(sample_name, [])


def cleanup_sample_outputs(sample_path: Path, sample_name: str) -> None:
    """Clean up output files from previous runs."""
    expected_outputs = get_expected_outputs(sample_name)

    for output_file in expected_outputs:
        output_path = sample_path / output_file
        if output_path.exists():
            output_path.unlink()
            print(f"   Cleaned up: {output_file}")


def main() -> None:
    """Run all sample project tests."""
    print("=" * 70)
    print("WARIFURI SAMPLE PROJECTS TEST RUNNER")
    print("=" * 70)

    samples_dir = Path(__file__).parent.parent / "sample-projects"

    if not samples_dir.exists():
        print("Sample projects directory not found!")
        return

    # Get all sample projects
    sample_projects = []
    for sample_dir in samples_dir.iterdir():
        if sample_dir.is_dir() and any(sample_dir.glob("project-*.yaml")):
            sample_projects.append(sample_dir)

    if not sample_projects:
        print("No sample projects found!")
        return

    print(f"Found {len(sample_projects)} sample project(s):")
    for sample in sample_projects:
        print(f"  - {sample.name}")

    # Test each sample project
    all_results = []

    for sample_dir in sample_projects:
        sample_name = sample_dir.name

        # Cleanup before testing
        print(f"\nCleaning up {sample_name}...")
        cleanup_sample_outputs(sample_dir, sample_name)

        # Run tests
        result = test_sample_project(sample_name, sample_dir)
        all_results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    total_tests = len(all_results)
    passed_tests = sum(1 for r in all_results if r["success"])
    failed_tests = total_tests - passed_tests

    print(f"Total samples tested: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")

    if failed_tests > 0:
        print("\nFailed tests:")
        for result in all_results:
            if not result["success"]:
                print(f"  - {result['sample_name']}:")
                for error in result["errors"]:
                    print(f"    • {error}")

    # Detailed results
    print("\nDetailed results:")
    for result in all_results:
        status = "✓ PASSED" if result["success"] else "✗ FAILED"
        print(f"  {result['sample_name']}: {status}")

        for test_name, test_result in result["tests"].items():
            test_status = "✓" if test_result["success"] else "✗"
            print(f"    {test_status} {test_name}")

    # Save results to file
    results_file = Path(__file__).parent / "test_results.json"
    import json
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nDetailed results saved to: {results_file}")

    # Exit with appropriate code
    sys.exit(0 if failed_tests == 0 else 1)


if __name__ == "__main__":
    main()
