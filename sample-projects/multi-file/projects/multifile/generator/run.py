#!/usr/bin/env python3
"""Generator task: Creates multiple data files"""

import json
from datetime import datetime


def main():
    print("Running generator task...")

    # Generate data1.txt
    with open("data1.txt", "w") as f:
        f.write(f"Data file 1 generated at {datetime.now()}\n")
        f.write("Sample data line 1\n")
        f.write("Sample data line 2\n")

    # Generate data2.txt
    with open("data2.txt", "w") as f:
        f.write(f"Data file 2 generated at {datetime.now()}\n")
        f.write("Different sample data\n")
        f.write("More different data\n")

    # Generate config.json
    config_data = {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "data_files": ["data1.txt", "data2.txt"],
        "settings": {"debug": True, "max_lines": 100},
    }

    with open("config.json", "w") as f:
        json.dump(config_data, f, indent=2)

    print("Generated files: data1.txt, data2.txt, config.json")


if __name__ == "__main__":
    main()
