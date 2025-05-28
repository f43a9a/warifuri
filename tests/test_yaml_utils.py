"""Tests for YAML utilities."""

from pathlib import Path
from unittest.mock import mock_open, patch, Mock

import pytest

from warifuri.utils.yaml_utils import load_yaml, save_yaml


class TestLoadYaml:
    """Test load_yaml function."""

    def test_load_yaml_success(self, tmp_path: Path) -> None:
        """Test loading valid YAML file."""
        yaml_file = tmp_path / "test.yaml"
        yaml_content = """
name: test
value: 123
items:
  - item1
  - item2
nested:
  key: value
"""
        yaml_file.write_text(yaml_content, encoding="utf-8")

        result = load_yaml(yaml_file)

        assert result["name"] == "test"
        assert result["value"] == 123
        assert result["items"] == ["item1", "item2"]
        assert result["nested"]["key"] == "value"

    def test_load_yaml_empty_file(self, tmp_path: Path) -> None:
        """Test loading empty YAML file."""
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("", encoding="utf-8")

        result = load_yaml(yaml_file)
        assert result == {}

    def test_load_yaml_null_content(self, tmp_path: Path) -> None:
        """Test loading YAML file with null content."""
        yaml_file = tmp_path / "null.yaml"
        yaml_file.write_text("null", encoding="utf-8")

        result = load_yaml(yaml_file)
        assert result == {}

    def test_load_yaml_file_not_found(self, tmp_path: Path) -> None:
        """Test loading non-existent YAML file."""
        yaml_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError, match="YAML file not found"):
            load_yaml(yaml_file)

    def test_load_yaml_invalid_syntax(self, tmp_path: Path) -> None:
        """Test loading YAML file with invalid syntax."""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("invalid: yaml: content: [", encoding="utf-8")

        with pytest.raises(ValueError, match="Invalid YAML"):
            load_yaml(yaml_file)

    def test_load_yaml_complex_data(self, tmp_path: Path) -> None:
        """Test loading YAML with complex data structures."""
        yaml_file = tmp_path / "complex.yaml"
        yaml_content = """
database:
  host: localhost
  port: 5432
  credentials:
    username: admin
    password: secret

features:
  - authentication
  - logging
  - monitoring

settings:
  debug: true
  timeout: 30.5
  retries: null
"""
        yaml_file.write_text(yaml_content, encoding="utf-8")

        result = load_yaml(yaml_file)

        assert result["database"]["host"] == "localhost"
        assert result["database"]["port"] == 5432
        assert result["database"]["credentials"]["username"] == "admin"
        assert result["features"] == ["authentication", "logging", "monitoring"]
        assert result["settings"]["debug"] is True
        assert result["settings"]["timeout"] == 30.5
        assert result["settings"]["retries"] is None


class TestSaveYaml:
    """Test save_yaml function."""

    def test_save_yaml_success(self, tmp_path: Path) -> None:
        """Test saving data to YAML file."""
        yaml_file = tmp_path / "output.yaml"
        data = {
            "name": "test",
            "value": 123,
            "items": ["item1", "item2"],
            "nested": {"key": "value"}
        }

        save_yaml(data, yaml_file)

        assert yaml_file.exists()

        # Verify content by loading it back
        loaded = load_yaml(yaml_file)
        assert loaded == data

    def test_save_yaml_creates_directories(self, tmp_path: Path) -> None:
        """Test that save_yaml creates parent directories."""
        yaml_file = tmp_path / "nested" / "deep" / "directory" / "file.yaml"
        data = {"test": "data"}

        save_yaml(data, yaml_file)

        assert yaml_file.exists()
        assert yaml_file.parent.exists()

        loaded = load_yaml(yaml_file)
        assert loaded == data

    def test_save_yaml_overwrites_existing(self, tmp_path: Path) -> None:
        """Test that save_yaml overwrites existing file."""
        yaml_file = tmp_path / "existing.yaml"

        # Create initial file
        initial_data = {"old": "data"}
        save_yaml(initial_data, yaml_file)

        # Overwrite with new data
        new_data = {"new": "data", "more": "content"}
        save_yaml(new_data, yaml_file)

        loaded = load_yaml(yaml_file)
        assert loaded == new_data
        assert "old" not in loaded

    def test_save_yaml_complex_data(self, tmp_path: Path) -> None:
        """Test saving complex data structures."""
        yaml_file = tmp_path / "complex.yaml"
        data = {
            "string": "text",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "null_value": None,
            "list": [1, 2, 3, "mixed", True],
            "nested_dict": {
                "level2": {
                    "level3": "deep value"
                }
            },
            "mixed_list": [
                {"name": "item1", "value": 1},
                {"name": "item2", "value": 2}
            ]
        }

        save_yaml(data, yaml_file)

        loaded = load_yaml(yaml_file)
        assert loaded == data

    def test_save_yaml_empty_data(self, tmp_path: Path) -> None:
        """Test saving empty dictionary."""
        yaml_file = tmp_path / "empty.yaml"
        data = {}

        save_yaml(data, yaml_file)

        loaded = load_yaml(yaml_file)
        assert loaded == {}

    @patch("builtins.open", new_callable=mock_open)
    @patch("warifuri.utils.yaml_utils.yaml.safe_dump")
    def test_save_yaml_dump_options(self, mock_dump: Mock, mock_file: Mock, tmp_path: Path) -> None:
        """Test that save_yaml uses correct yaml.safe_dump options."""
        yaml_file = tmp_path / "test.yaml"
        data = {"test": "data"}

        save_yaml(data, yaml_file)

        # Verify yaml.safe_dump was called with correct options
        mock_dump.assert_called_once_with(
            data,
            mock_file.return_value.__enter__.return_value,
            default_flow_style=False,
            sort_keys=False
        )
