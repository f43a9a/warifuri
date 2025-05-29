#!/usr/bin/env python3
"""
Foundation task script
Generates a simple text file with timestamp and basic content.
"""

import datetime
from pathlib import Path


def main() -> None:
    """Generate foundation file with current timestamp."""
    timestamp = datetime.datetime.now().isoformat()

    content = f"""Foundation File Generated
========================

Generated at: {timestamp}
Content: This is the foundation data for the simple chain test.
Status: SUCCESS

This file serves as input for the consumer task.
"""

    output_file = Path("base.txt")
    output_file.write_text(content, encoding="utf-8")

    print(f"Foundation task completed. Generated {output_file}")
    print(f"File size: {output_file.stat().st_size} bytes")


if __name__ == "__main__":
    main()
