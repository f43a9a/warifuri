#!/usr/bin/env python3
"""
Generator task script
Generates multiple files with different formats and content.
"""

import datetime
import json
from pathlib import Path


def main() -> None:
    """Generate multiple data files with different formats."""
    timestamp = datetime.datetime.now().isoformat()

    # Generate data1.txt - structured data
    data1_content = f"""Data File 1 - Structured Information
========================================

Generated: {timestamp}
Type: Structured Data
Format: Text

Records:
001: Alpha Data Point - Value: 42.5
002: Beta Data Point - Value: 18.7
003: Gamma Data Point - Value: 91.2
004: Delta Data Point - Value: 63.8
005: Epsilon Data Point - Value: 29.4

Total Records: 5
Average Value: 49.12
Status: COMPLETE
"""

    # Generate data2.txt - log-style data
    data2_content = f"""Data File 2 - Log Style Information
====================================

[{timestamp}] INFO: Generator task started
[{timestamp}] INFO: Processing configuration parameters
[{timestamp}] DEBUG: Memory usage: 45.2 MB
[{timestamp}] DEBUG: CPU usage: 12.4%
[{timestamp}] INFO: Generating synthetic dataset
[{timestamp}] DEBUG: Dataset size: 1000 entries
[{timestamp}] INFO: Applying data transformation
[{timestamp}] DEBUG: Transformation type: normalize
[{timestamp}] INFO: Validation completed successfully
[{timestamp}] INFO: Generator task completed

Log Level Summary:
- INFO messages: 6
- DEBUG messages: 4
- ERROR messages: 0
- WARN messages: 0
"""

    # Generate config.json - configuration data
    config_data = {
        "metadata": {
            "generated_at": timestamp,
            "version": "1.0.0",
            "generator": "multi-file-generator",
        },
        "processing": {
            "data1_file": "data1.txt",
            "data2_file": "data2.txt",
            "output_format": "summary",
            "compression": False,
            "validation": True,
        },
        "parameters": {
            "max_records": 1000,
            "precision": 2,
            "timeout_seconds": 30,
            "retry_count": 3,
        },
        "flags": {"debug_mode": False, "verbose_output": True, "create_backup": False},
    }

    # Write all files
    Path("data1.txt").write_text(data1_content, encoding="utf-8")
    Path("data2.txt").write_text(data2_content, encoding="utf-8")
    Path("config.json").write_text(json.dumps(config_data, indent=2), encoding="utf-8")

    print("Generator task completed. Generated files:")
    print(f"- data1.txt ({Path('data1.txt').stat().st_size} bytes)")
    print(f"- data2.txt ({Path('data2.txt').stat().st_size} bytes)")
    print(f"- config.json ({Path('config.json').stat().st_size} bytes)")


if __name__ == "__main__":
    main()
