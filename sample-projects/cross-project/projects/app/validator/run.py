#!/usr/bin/env python3
"""Validator: Validates application output against version requirements"""

from datetime import datetime
from pathlib import Path

def main():
    print("Running validator task...")

    # Check required input files
    required_files = ["app_output.txt", "version.txt"]
    missing_files = []

    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"Error: Missing required files: {missing_files}")
        return 1

    # Read app output
    with open("app_output.txt", "r") as f:
        app_content = f.read()

    # Read version info
    with open("version.txt", "r") as f:
        version_content = f.read()

    # Perform validation
    validation_results = []
    validation_results.append(f"Validation Report - {datetime.now()}")
    validation_results.append("=" * 50)
    validation_results.append("")

    # File existence checks
    validation_results.append("File Existence Validation:")
    validation_results.append("  ✓ app_output.txt found")
    validation_results.append("  ✓ version.txt found")

    # Content validation
    validation_results.append("")
    validation_results.append("Content Validation:")

    # Check if app output contains expected sections
    checks = [
        ("Core Library Information", "Core Library Information:" in app_content),
        ("Configuration Summary", "Configuration Summary:" in app_content),
        ("Features Section", "Available Features:" in app_content),
        ("Dependencies Section", "Dependencies:" in app_content),
        ("Success Message", "successfully!" in app_content)
    ]

    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        validation_results.append(f"  {status} {check_name}")
        if not passed:
            all_passed = False

    # Version validation
    validation_results.append("")
    validation_results.append("Version Validation:")
    if "Version: 1.0.0" in version_content:
        validation_results.append("  ✓ Version format correct")
    else:
        validation_results.append("  ✗ Version format incorrect")
        all_passed = False

    # Summary
    validation_results.append("")
    validation_results.append("Validation Summary:")
    if all_passed:
        validation_results.append("  Status: PASSED")
        validation_results.append("  All validation checks completed successfully!")
    else:
        validation_results.append("  Status: FAILED")
        validation_results.append("  Some validation checks failed!")

    validation_results.append("")
    validation_results.append(f"App output size: {len(app_content)} characters")
    validation_results.append(f"Version info size: {len(version_content)} characters")

    # Write validation report
    with open("validation_report.txt", "w") as f:
        f.write("\n".join(validation_results))

    print("Generated validation_report.txt")
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
