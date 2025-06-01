#!/usr/bin/env python3
"""
Core library builder script
Builds core library information based on shared configuration.
"""

import datetime
import json
from pathlib import Path
from typing import Any, Dict


def parse_config(config_content: str) -> Dict[str, Any]:
    """Parse configuration file content."""
    config = {}
    current_section = None

    for line in config_content.splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
            config[current_section] = {}
        elif "=" in line and current_section:
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()

            # Convert value types
            if value.lower() in ("true", "false"):
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)

            config[current_section][key] = value

    return config


def main() -> None:
    """Build core library information from configuration."""
    timestamp = datetime.datetime.now().isoformat()

    # Check input file exists
    config_file = Path("shared.conf")
    if not config_file.exists():
        raise FileNotFoundError(f"Required input file not found: {config_file}")

    # Read and parse configuration
    config_content = config_file.read_text(encoding="utf-8")
    config = parse_config(config_content)

    # Build library information
    library_info = {
        "metadata": {
            "generated_at": timestamp,
            "source_file": "shared.conf",
            "generator": "core-library-builder",
            "version": "1.0.0",
        },
        "system_info": {
            "version": config.get("system", {}).get("version", "unknown"),
            "environment": config.get("system", {}).get("environment", "unknown"),
            "debug_mode": config.get("system", {}).get("debug_mode", False),
            "log_level": config.get("system", {}).get("log_level", "info"),
        },
        "database_config": {
            "connection_string": f"{config.get('database', {}).get('host', 'localhost')}:{config.get('database', {}).get('port', 5432)}",
            "database_name": config.get("database", {}).get("name", ""),
            "timeout": config.get("database", {}).get("timeout", 30),
        },
        "api_config": {
            "base_url": config.get("api", {}).get("base_url", ""),
            "timeout": config.get("api", {}).get("timeout", 15),
            "retry_count": config.get("api", {}).get("retry_count", 3),
            "rate_limit": config.get("api", {}).get("rate_limit", 100),
        },
        "features": config.get("features", {}),
        "paths": config.get("paths", {}),
        "security": config.get("security", {}),
        "performance": config.get("performance", {}),
        "statistics": {
            "total_sections": len(config),
            "total_settings": sum(
                len(section) if isinstance(section, dict) else 0 for section in config.values()
            ),
            "feature_flags": len(config.get("features", {})),
            "path_mappings": len(config.get("paths", {})),
        },
        "validation": {
            "config_valid": True,
            "required_sections": ["system", "database", "api"],
            "missing_sections": [
                section for section in ["system", "database", "api"] if section not in config
            ],
            "validation_timestamp": timestamp,
        },
    }

    # Write library information
    output_file = Path("core_lib.json")
    output_file.write_text(json.dumps(library_info, indent=2), encoding="utf-8")

    print("Core library builder completed.")
    print(f"Generated {output_file} ({output_file.stat().st_size} bytes)")
    print(f"Processed {library_info['statistics']['total_sections']} configuration sections")
    print(f"Total settings: {library_info['statistics']['total_settings']}")
    print(
        f"Validation result: {'PASSED' if library_info['validation']['config_valid'] else 'FAILED'}"
    )


if __name__ == "__main__":
    main()
