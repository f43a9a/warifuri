"""YAML utilities."""

from pathlib import Path
from typing import Any, Dict

import yaml


def load_yaml(file_path: Path) -> Dict[str, Any]:
    """Load YAML file safely."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {file_path}: {e}")
    except FileNotFoundError:
        raise FileNotFoundError(f"YAML file not found: {file_path}")


def save_yaml(data: Dict[str, Any], file_path: Path) -> None:
    """Save data to YAML file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
