#!/usr/bin/env python3
"""
Application main script
Uses core shared configuration and library for main processing.
"""

import datetime
import json
from pathlib import Path
from typing import Any, Dict


def check_input_files() -> None:
    """Verify all required input files exist."""
    required_files = ["shared.conf", "core_lib.json"]
    missing_files = []

    for file_name in required_files:
        if not Path(file_name).exists():
            missing_files.append(file_name)

    if missing_files:
        raise FileNotFoundError(f"Required input files not found: {missing_files}")


def parse_config_value(value: str) -> Any:
    """Parse configuration value from string."""
    value = value.strip()

    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    elif value.isdigit():
        return int(value)
    elif value.replace(".", "").isdigit():
        return float(value)
    else:
        return value


def load_shared_config() -> Dict[str, Any]:
    """Load and parse shared configuration file."""
    config_content = Path("shared.conf").read_text(encoding="utf-8")
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
            config[current_section][key.strip()] = parse_config_value(value)

    return config


def main() -> None:
    """Main application processing using core components."""
    timestamp = datetime.datetime.now().isoformat()

    # Check input files
    check_input_files()

    # Load core components
    shared_config = load_shared_config()
    core_lib_content = Path("core_lib.json").read_text(encoding="utf-8")
    core_lib = json.loads(core_lib_content)

    # Process application logic
    system_version = core_lib["system_info"]["version"]
    debug_mode = core_lib["system_info"]["debug_mode"]
    environment = core_lib["system_info"]["environment"]

    # Simulate application processing
    processing_results = {
        "initialization": "SUCCESS",
        "configuration_loading": "SUCCESS",
        "core_library_integration": "SUCCESS",
        "business_logic": "SUCCESS",
        "data_processing": "SUCCESS",
        "output_generation": "SUCCESS",
    }

    # Calculate metrics
    total_features = len(core_lib.get("features", {}))
    enabled_features = sum(
        1 for feature, enabled in core_lib.get("features", {}).items() if enabled
    )

    # Generate application output
    app_output = f"""Application Processing Report
============================

Processing Timestamp: {timestamp}
Core System Version: {system_version}
Environment: {environment}
Debug Mode: {debug_mode}

=== Configuration Summary ===

Shared Config Sections: {len(shared_config)}
Core Library Version: {core_lib["metadata"]["version"]}
Core Generated At: {core_lib["metadata"]["generated_at"]}

System Configuration:
- Database: {core_lib["database_config"]["connection_string"]}
- API Base URL: {core_lib["api_config"]["base_url"]}
- API Timeout: {core_lib["api_config"]["timeout"]}s
- Rate Limit: {core_lib["api_config"]["rate_limit"]} req/min

Feature Status:
- Total Features: {total_features}
- Enabled Features: {enabled_features}
- Feature Flags: {", ".join(name for name, enabled in core_lib.get("features", {}).items() if enabled)}

Performance Settings:
- Max Workers: {core_lib["performance"].get("max_workers", "N/A")}
- Batch Size: {core_lib["performance"].get("batch_size", "N/A")}
- Cache Size: {core_lib["performance"].get("cache_size", "N/A")}
- Memory Limit: {core_lib["performance"].get("memory_limit", "N/A")}

=== Processing Results ===

{chr(10).join(f"{step}: {result}" for step, result in processing_results.items())}

=== Application Metrics ===

Total Processing Steps: {len(processing_results)}
Successful Steps: {sum(1 for result in processing_results.values() if result == "SUCCESS")}
Failed Steps: {sum(1 for result in processing_results.values() if result != "SUCCESS")}
Success Rate: {(sum(1 for result in processing_results.values() if result == "SUCCESS") / len(processing_results) * 100):.1f}%

Configuration Validation: {"PASSED" if core_lib["validation"]["config_valid"] else "FAILED"}
Missing Sections: {", ".join(core_lib["validation"]["missing_sections"]) if core_lib["validation"]["missing_sections"] else "None"}

=== Resource Usage ===

Memory Usage: Optimal
CPU Usage: Normal
Disk Usage: Minimal
Network Usage: Moderate

=== Status ===

Application Status: COMPLETED
Error Count: 0
Warning Count: 0
Performance: Optimal

Processing completed successfully.
"""

    # Write application output
    output_file = Path("app_output.txt")
    output_file.write_text(app_output, encoding="utf-8")

    print("Application main processing completed.")
    print(f"Generated {output_file} ({output_file.stat().st_size} bytes)")
    print(f"Used core system version: {system_version}")
    print(f"Processed {len(processing_results)} steps successfully")
    print(f"Environment: {environment}")


if __name__ == "__main__":
    main()
