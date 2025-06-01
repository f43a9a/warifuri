#!/usr/bin/env python3
"""
Consumer task script
Reads the foundation file and processes it to create output.
"""

import datetime
from pathlib import Path


def main() -> None:
    """Process foundation file and generate output."""
    input_file = Path("base.txt")
    output_file = Path("processed.txt")

    # Check if input file exists
    if not input_file.exists():
        raise FileNotFoundError(f"Required input file not found: {input_file}")

    # Read foundation content
    foundation_content = input_file.read_text(encoding="utf-8")

    # Process the content
    timestamp = datetime.datetime.now().isoformat()

    processed_content = f"""Processed Foundation Data
=========================

Processing timestamp: {timestamp}
Original file size: {input_file.stat().st_size} bytes

--- Original Content ---
{foundation_content}

--- Processing Results ---
- Line count: {len(foundation_content.splitlines())}
- Character count: {len(foundation_content)}
- Contains 'SUCCESS': {"YES" if "SUCCESS" in foundation_content else "NO"}

Processing Status: COMPLETED
"""

    # Write processed output
    output_file.write_text(processed_content, encoding="utf-8")

    print(f"Consumer task completed. Processed {input_file} -> {output_file}")
    print(f"Output file size: {output_file.stat().st_size} bytes")


if __name__ == "__main__":
    main()
