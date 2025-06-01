"""
Test complex task validation
"""

import json
from pathlib import Path

import pytest
import yaml


def test_complex_task_schema_validation():
    """複雑タスクのスキーマ検証"""
    try:
        from jsonschema import ValidationError, validate
    except ImportError:
        pytest.skip("jsonschema not available")

    # Load test data and schema
    data_path = Path(__file__).parent.parent / "data" / "tasks" / "complex_task.yaml"
    schema_path = Path(__file__).parent.parent / "data" / "schemas" / "task_schema.yaml"

    with open(data_path, "r", encoding="utf-8") as f:
        task_data = yaml.safe_load(f)

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    # Validate
    try:
        validate(instance=task_data, schema=schema)
        print("✅ Complex task schema validation passed!")
    except ValidationError as e:
        pytest.fail(f"Complex task schema validation failed: {e.message}")


def test_error_cases_loading():
    """エラーケースデータの読み込みテスト"""
    data_path = Path(__file__).parent.parent / "data" / "tasks" / "error_cases.yaml"

    assert data_path.exists(), f"Error cases file not found: {data_path}"

    with open(data_path, "r", encoding="utf-8") as f:
        # Load multiple documents
        documents = list(yaml.safe_load_all(f))

    assert len(documents) > 0, "No documents found"
    valid_docs = [doc for doc in documents if doc is not None]
    assert len(valid_docs) > 0, "No valid documents found"
    print(f"✅ Loaded {len(valid_docs)} error case documents")


def test_all_data_files_loadable():
    """すべてのテストデータファイルが読み込み可能かテスト"""
    data_dir = Path(__file__).parent.parent / "data"

    yaml_files = list(data_dir.glob("**/*.yaml"))
    json_files = list(data_dir.glob("**/*.json"))

    all_files = yaml_files + json_files
    assert len(all_files) > 0, "No test data files found"

    failed_files = []

    for file_path in all_files:
        # Skip schema and README files
        if file_path.name in ["README.md"] or "schema" in str(file_path):
            continue

        relative_path = file_path.relative_to(data_dir)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if file_path.suffix.lower() == ".json":
                json.loads(content)
            elif "error_cases" in str(file_path) or "---" in content:
                # Handle multi-document YAML files and error cases
                list(yaml.safe_load_all(content))
            else:
                # Handle single-document YAML files
                yaml.safe_load(content)
        except Exception as e:
            failed_files.append((relative_path, str(e)))

    if failed_files:
        error_msg = "\\n".join([f"{path}: {error}" for path, error in failed_files])
        pytest.fail(f"Failed to load files:\\n{error_msg}")

    print(f"✅ Successfully loaded {len(all_files)} test data files")
