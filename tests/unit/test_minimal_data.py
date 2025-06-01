"""
Test Data Validation Tests
テストデータの読み込みとバリデーションのテスト
"""

# Import directly without relative imports
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, "/workspace/src")

from warifuri.core.types import TaskInstruction


def test_basic_test_data_loading():
    """基本的なテストデータ読み込みテスト"""
    data_path = Path(__file__).parent.parent / "data" / "tasks" / "simple_task.yaml"

    assert data_path.exists(), f"Test data file not found: {data_path}"

    with open(data_path, "r", encoding="utf-8") as f:
        task_data = yaml.safe_load(f)

    assert task_data is not None
    assert "id" in task_data
    assert "title" in task_data
    assert "type" in task_data
    assert "status" in task_data


def test_schema_loading():
    """スキーマファイル読み込みテスト"""
    schema_path = Path(__file__).parent.parent / "data" / "schemas" / "task_schema.yaml"

    assert schema_path.exists(), f"Schema file not found: {schema_path}"

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    assert schema is not None
    assert "type" in schema
    assert "properties" in schema


def test_jsonschema_validation():
    """JSONスキーマ検証テスト"""
    try:
        from jsonschema import ValidationError, validate
    except ImportError:
        pytest.skip("jsonschema not available")

    # Load test data and schema
    data_path = Path(__file__).parent.parent / "data" / "tasks" / "simple_task.yaml"
    schema_path = Path(__file__).parent.parent / "data" / "schemas" / "task_schema.yaml"

    with open(data_path, "r", encoding="utf-8") as f:
        task_data = yaml.safe_load(f)

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    # Validate
    try:
        validate(instance=task_data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Schema validation failed: {e.message}")


def test_task_instruction_creation():
    """TaskInstruction作成テスト"""
    data_path = Path(__file__).parent.parent / "data" / "tasks" / "simple_task.yaml"

    with open(data_path, "r", encoding="utf-8") as f:
        task_data = yaml.safe_load(f)

    # Create TaskInstruction with correct parameters
    task_instruction = TaskInstruction(
        name=task_data["title"],
        description=task_data.get("description", ""),
        dependencies=task_data.get("dependencies", []),
        inputs=task_data.get("inputs", []),
        outputs=task_data.get("outputs", []),
        note=task_data.get("note"),
    )

    assert task_instruction.name == task_data["title"]
    assert task_instruction.description == task_data.get("description", "")
