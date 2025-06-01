#!/usr/bin/env python3
"""Main App: Uses core library functionality"""

import configparser
import json
from datetime import datetime
from pathlib import Path


def main():
    print("Running main-app task...")

    # Check required input files
    required_files = ["shared.conf", "core_lib.json"]
    missing_files = []

    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"Error: Missing required files: {missing_files}")
        return 1

    # Read core library information
    with open("core_lib.json", "r") as f:
        core_lib = json.load(f)

    # Read shared configuration
    config = configparser.ConfigParser()
    config.read("shared.conf")

    # Generate application output
    app_output = []
    app_output.append(f"Application Output - {datetime.now()}")
    app_output.append("=" * 60)
    app_output.append("")

    # Core library info
    app_output.append("Core Library Information:")
    app_output.append(f"  Name: {core_lib.get('name', 'Unknown')}")
    app_output.append(f"  Generated: {core_lib.get('generated_at', 'Unknown')}")

    # Configuration summary
    app_output.append("")
    app_output.append("Configuration Summary:")
    if "database" in config:
        app_output.append(
            f"  Database: {config['database']['name']}@{config['database']['host']}:{config['database']['port']}"
        )
    if "api" in config:
        app_output.append(f"  API Version: {config['api']['version']}")
        app_output.append(f"  API Timeout: {config['api']['timeout']}s")

    # Features
    app_output.append("")
    app_output.append("Available Features:")
    for feature in core_lib.get("features", []):
        app_output.append(f"  - {feature}")

    # Dependencies
    app_output.append("")
    app_output.append("Dependencies:")
    for dep in core_lib.get("dependencies", []):
        app_output.append(f"  - {dep}")

    app_output.append("")
    app_output.append("Application initialized successfully!")

    # Write app_output.txt
    with open("app_output.txt", "w") as f:
        f.write("\n".join(app_output))

    print("Generated app_output.txt with application results")
    return 0


if __name__ == "__main__":
    exit(main())
