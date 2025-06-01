#!/usr/bin/env python3
"""Debug error case validation"""

from pathlib import Path

import yaml
from jsonschema import ValidationError, validate


def load_yaml_all(file_path):
    """Load all YAML documents from file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            # First try loading as single document (array)
            data = yaml.safe_load(f)
            if isinstance(data, list):
                return data
            # If not a list, try loading as multiple documents
            f.seek(0)
            return list(yaml.safe_load_all(f))
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []


def load_schema(schema_path):
    """Load schema from YAML file"""
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading schema {schema_path}: {e}")
        return {}


def main():
    base_path = Path("/workspace/tests/data")
    error_documents = load_yaml_all(base_path / "tasks/error_cases.yaml")
    schema = load_schema(base_path / "schemas/task_schema.yaml")

    print(f"Loaded {len(error_documents)} error case documents")
    print(f"Schema type: {type(schema)}")
    print(f"Schema keys: {list(schema.keys()) if isinstance(schema, dict) else 'Not a dict'}")

    # Check required fields in schema
    if isinstance(schema, dict) and "required" in schema:
        print(f"Required fields: {schema['required']}")

    valid_count = 0
    invalid_count = 0

    for i, doc in enumerate(error_documents):
        if not doc or not isinstance(doc, dict):
            print(f"Document {i}: Skipped (not a dict)")
            continue

        doc_id = doc.get("id", f"doc_{i}")
        print(f"\nDocument {i} (id: {doc_id}):")
        print(f"  Keys: {list(doc.keys())}")

        # Check if document has required fields
        for field in ["id", "title", "type", "status"]:
            if field in doc:
                print(f"  {field}: {doc[field]} ({type(doc[field]).__name__})")
            else:
                print(f"  {field}: MISSING")

        try:
            validate(instance=doc, schema=schema)
            print("  Result: VALID (unexpected for error case)")
            valid_count += 1
        except ValidationError as e:
            print(f"  Result: INVALID ({e.message})")
            invalid_count += 1
        except Exception as e:
            print(f"  Result: ERROR ({e})")

    print(f"\nSummary: {valid_count} valid, {invalid_count} invalid")


if __name__ == "__main__":
    main()
