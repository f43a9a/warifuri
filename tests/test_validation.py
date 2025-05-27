"""Test validation utilities."""

import pytest
import json
from pathlib import Path

from warifuri.utils.validation import (
    validate_instruction_yaml,
    detect_circular_dependencies,
    ValidationError,
)
from warifuri.core.types import Task, TaskInstruction, TaskType, TaskStatus


def test_validate_instruction_yaml_valid(sample_task_instruction):
    """Test validation with valid instruction data."""
    schema = {
        "type": "object",
        "required": ["name", "description"],
        "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "dependencies": {"type": "array"},
            "inputs": {"type": "array"},
            "outputs": {"type": "array"},
            "note": {"type": "string"},
        },
    }
    
    # Should not raise exception
    validate_instruction_yaml(sample_task_instruction, schema)


def test_validate_instruction_yaml_missing_required():
    """Test validation with missing required fields."""
    schema = {
        "type": "object",
        "required": ["name", "description"],
        "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
        },
    }
    
    invalid_data = {"name": "test"}  # Missing description
    
    with pytest.raises(ValidationError, match="Schema validation failed"):
        validate_instruction_yaml(invalid_data, schema, strict=True)


def test_detect_circular_dependencies_none(temp_workspace):
    """Test circular dependency detection with no cycles."""
    # Create tasks: A -> B -> C
    task_a = _create_test_task(temp_workspace, "proj", "a", ["proj/b"])
    task_b = _create_test_task(temp_workspace, "proj", "b", ["proj/c"])
    task_c = _create_test_task(temp_workspace, "proj", "c", [])
    
    tasks = [task_a, task_b, task_c]
    
    cycle = detect_circular_dependencies(tasks)
    assert cycle is None


def test_detect_circular_dependencies_simple_cycle(temp_workspace):
    """Test circular dependency detection with simple cycle."""
    # Create tasks: A -> B -> A
    task_a = _create_test_task(temp_workspace, "proj", "a", ["proj/b"])
    task_b = _create_test_task(temp_workspace, "proj", "b", ["proj/a"])
    
    tasks = [task_a, task_b]
    
    cycle = detect_circular_dependencies(tasks)
    assert cycle is not None
    assert len(cycle) >= 2


def _create_test_task(workspace: Path, project: str, name: str, deps: list) -> Task:
    """Helper to create test task."""
    instruction = TaskInstruction(
        name=name,
        description=f"Test task {name}",
        dependencies=deps,
        inputs=[],
        outputs=[],
    )
    
    task_path = workspace / "projects" / project / name
    task_path.mkdir(parents=True, exist_ok=True)
    
    return Task(
        project=project,
        name=name,
        path=task_path,
        instruction=instruction,
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING,
    )
