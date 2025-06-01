#!/usr/bin/env python3
"""Processor task: Processes all generated files and creates summary"""

import json
from datetime import datetime
from pathlib import Path


def main():
    print("Running processor task...")

    # Check if all input files exist
    required_files = [
        "../generator/data1.txt",
        "../generator/data2.txt",
        "../generator/config.json",
    ]
    missing_files = []

    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"Error: Missing required files: {missing_files}")
        return 1

    # Read and process the input files
    summary_lines = []
    summary_lines.append(f"Processing Summary - {datetime.now()}")
    summary_lines.append("=" * 50)

    # Process data1.txt
    with open("../generator/data1.txt", "r") as f:
        data1_content = f.read()
        summary_lines.append(f"Data1 file size: {len(data1_content)} characters")
        summary_lines.append(f"Data1 line count: {len(data1_content.splitlines())}")

    # Process data2.txt
    with open("../generator/data2.txt", "r") as f:
        data2_content = f.read()
        summary_lines.append(f"Data2 file size: {len(data2_content)} characters")
        summary_lines.append(f"Data2 line count: {len(data2_content.splitlines())}")

    # Process config.json
    with open("../generator/config.json", "r") as f:
        config_data = json.load(f)
        summary_lines.append(f"Config version: {config_data.get('version', 'unknown')}")
        summary_lines.append(f"Config generated at: {config_data.get('generated_at', 'unknown')}")
        summary_lines.append(f"Debug mode: {config_data.get('settings', {}).get('debug', False)}")

    summary_lines.append("")
    summary_lines.append("Processing completed successfully!")

    # Write summary.txt
    with open("summary.txt", "w") as f:
        f.write("\n".join(summary_lines))

    print("Generated summary.txt with processing results")
    return 0


if __name__ == "__main__":
    exit(main())
