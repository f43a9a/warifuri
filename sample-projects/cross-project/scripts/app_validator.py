#!/usr/bin/env python3
"""
Application validator script
Validates application output against version requirements.
"""

import datetime
import re
from pathlib import Path
from typing import Dict, Any


def check_input_files() -> None:
    """Verify all required input files exist."""
    required_files = ["app_output.txt", "version.txt"]
    missing_files = []

    for file_name in required_files:
        if not Path(file_name).exists():
            missing_files.append(file_name)

    if missing_files:
        raise FileNotFoundError(f"Required input files not found: {missing_files}")


def parse_version_info(version_content: str) -> Dict[str, str]:
    """Parse version information from version.txt."""
    version_info = {}

    for line in version_content.splitlines():
        if ':' in line and not line.startswith('---') and not line.startswith('==='):
            key, value = line.split(':', 1)
            version_info[key.strip()] = value.strip()

    return version_info


def validate_app_output(app_content: str) -> Dict[str, Any]:
    """Validate application output content."""
    validation_results = {
        "structure_valid": True,
        "required_sections": [],
        "missing_sections": [],
        "metrics": {},
        "issues": []
    }

    # Required sections
    required_sections = [
        "Application Processing Report",
        "Configuration Summary",
        "Processing Results",
        "Application Metrics",
        "Status"
    ]

    found_sections = []
    for section in required_sections:
        if section in app_content:
            found_sections.append(section)
        else:
            validation_results["missing_sections"].append(section)

    validation_results["required_sections"] = found_sections
    validation_results["structure_valid"] = len(validation_results["missing_sections"]) == 0

    # Extract metrics
    success_rate_match = re.search(r'Success Rate: ([\d.]+)%', app_content)
    if success_rate_match:
        validation_results["metrics"]["success_rate"] = float(success_rate_match.group(1))

    error_count_match = re.search(r'Error Count: (\d+)', app_content)
    if error_count_match:
        validation_results["metrics"]["error_count"] = int(error_count_match.group(1))

    # Check for completion status
    if "COMPLETED" in app_content:
        validation_results["metrics"]["completion_status"] = "COMPLETED"
    else:
        validation_results["issues"].append("Application did not complete successfully")

    # Check for processing steps
    if "Processing Steps:" in app_content:
        steps_match = re.search(r'Total Processing Steps: (\d+)', app_content)
        if steps_match:
            validation_results["metrics"]["total_steps"] = int(steps_match.group(1))

    return validation_results


def main() -> None:
    """Validate application output against version requirements."""
    timestamp = datetime.datetime.now().isoformat()

    # Check input files
    check_input_files()

    # Read input files
    app_content = Path("app_output.txt").read_text(encoding="utf-8")
    version_content = Path("version.txt").read_text(encoding="utf-8")

    # Parse version information
    version_info = parse_version_info(version_content)

    # Validate application output
    validation_results = validate_app_output(app_content)

    # Cross-reference with version requirements
    core_version = version_info.get("Version", "unknown")
    build_type = version_info.get("Build Type", "unknown")
    api_version = version_info.get("API Version", "unknown")

    # Generate validation report
    validation_report = f"""Application Validation Report
==============================

Validation Timestamp: {timestamp}
Core Version: {core_version}
Build Type: {build_type}
API Version: {api_version}

=== Version Information ===

Core System Version: {version_info.get('Version', 'N/A')}
Build Date: {version_info.get('Build Date', 'N/A')}
Git Branch: {version_info.get('Git Branch', 'N/A')}
Git Commit: {version_info.get('Git Commit', 'N/A')}
Build Number: {version_info.get('Build Number', 'N/A')}

Component Versions:
- Core Library: {version_info.get('Core Library', 'N/A')}
- Configuration Manager: {version_info.get('Configuration Manager', 'N/A')}
- Database Driver: {version_info.get('Database Driver', 'N/A')}
- API Client: {version_info.get('API Client', 'N/A')}

=== Application Output Validation ===

Structure Validation: {'PASSED' if validation_results['structure_valid'] else 'FAILED'}
Required Sections Found: {len(validation_results['required_sections'])}/5
Missing Sections: {', '.join(validation_results['missing_sections']) if validation_results['missing_sections'] else 'None'}

Application Metrics:
- Success Rate: {validation_results['metrics'].get('success_rate', 'N/A')}%
- Error Count: {validation_results['metrics'].get('error_count', 'N/A')}
- Completion Status: {validation_results['metrics'].get('completion_status', 'N/A')}
- Total Steps: {validation_results['metrics'].get('total_steps', 'N/A')}

=== Validation Results ===

Content Validation: {'PASSED' if not validation_results['issues'] else 'FAILED'}
Issues Found: {len(validation_results['issues'])}
{chr(10).join(f"- {issue}" for issue in validation_results['issues']) if validation_results['issues'] else "No issues found."}

Version Compatibility: {'COMPATIBLE' if core_version != 'unknown' else 'UNKNOWN'}
Build Type: {build_type}
API Compatibility: {'COMPATIBLE' if api_version != 'unknown' else 'UNKNOWN'}

=== File Statistics ===

app_output.txt: {Path('app_output.txt').stat().st_size} bytes
version.txt: {Path('version.txt').stat().st_size} bytes
Total input size: {Path('app_output.txt').stat().st_size + Path('version.txt').stat().st_size} bytes

=== Quality Assessment ===

Overall Quality: {'HIGH' if validation_results['structure_valid'] and not validation_results['issues'] else 'MEDIUM' if validation_results['structure_valid'] else 'LOW'}
Reliability Score: {((len(validation_results['required_sections']) / 5) * 100):.1f}%
Version Compliance: {'COMPLIANT' if core_version != 'unknown' and build_type != 'unknown' else 'PARTIAL'}

=== Validation Summary ===

Total Checks Performed: 8
Passed Checks: {sum([
    validation_results['structure_valid'],
    len(validation_results['issues']) == 0,
    validation_results['metrics'].get('error_count', 1) == 0,
    validation_results['metrics'].get('completion_status') == 'COMPLETED',
    core_version != 'unknown',
    build_type != 'unknown',
    len(validation_results['required_sections']) >= 4,
    validation_results['metrics'].get('success_rate', 0) >= 90
])}
Failed Checks: {8 - sum([
    validation_results['structure_valid'],
    len(validation_results['issues']) == 0,
    validation_results['metrics'].get('error_count', 1) == 0,
    validation_results['metrics'].get('completion_status') == 'COMPLETED',
    core_version != 'unknown',
    build_type != 'unknown',
    len(validation_results['required_sections']) >= 4,
    validation_results['metrics'].get('success_rate', 0) >= 90
])}

Final Status: {'VALIDATION_PASSED' if sum([
    validation_results['structure_valid'],
    len(validation_results['issues']) == 0,
    validation_results['metrics'].get('error_count', 1) == 0,
    validation_results['metrics'].get('completion_status') == 'COMPLETED',
    core_version != 'unknown',
    build_type != 'unknown',
    len(validation_results['required_sections']) >= 4,
    validation_results['metrics'].get('success_rate', 0) >= 90
]) >= 6 else 'VALIDATION_FAILED'}

Validation completed successfully.
"""

    # Write validation report
    output_file = Path("validation_report.txt")
    output_file.write_text(validation_report, encoding="utf-8")

    print("Application validation completed.")
    print(f"Generated {output_file} ({output_file.stat().st_size} bytes)")
    print(f"Core version: {core_version}")
    print(f"Structure validation: {'PASSED' if validation_results['structure_valid'] else 'FAILED'}")
    print(f"Issues found: {len(validation_results['issues'])}")

    final_status = "PASSED" if sum([
        validation_results['structure_valid'],
        len(validation_results['issues']) == 0,
        validation_results['metrics'].get('error_count', 1) == 0,
        validation_results['metrics'].get('completion_status') == 'COMPLETED',
        core_version != 'unknown',
        build_type != 'unknown',
        len(validation_results['required_sections']) >= 4,
        validation_results['metrics'].get('success_rate', 0) >= 90
    ]) >= 6 else "FAILED"

    print(f"Final validation status: {final_status}")


if __name__ == "__main__":
    main()
