"""Validation utilities."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import jsonschema

from ..core.types import Task


class ValidationError(Exception):
    """Validation error."""

    pass


class CircularDependencyError(ValidationError):
    """Circular dependency error."""

    pass


def load_schema(workspace_path: Path) -> Dict[str, Any]:
    """Load instruction schema, preferring workspace-local version."""
    # Try workspace-local schema first
    local_schema_path = workspace_path / "schemas" / "instruction.schema.json"
    if local_schema_path.exists():
        data: Dict[str, Any] = json.loads(local_schema_path.read_text(encoding="utf-8"))
        return data

    # Fall back to embedded schema
    from ..schemas import embedded

    embedded_path = Path(embedded.__file__).parent / "instruction.schema.json"
    data = json.loads(embedded_path.read_text(encoding="utf-8"))
    return data


def validate_instruction_yaml(
    instruction_data: Dict[str, Any], schema: Dict[str, Any], strict: bool = False
) -> None:
    """Validate instruction.yaml data against schema."""
    try:
        jsonschema.validate(instruction_data, schema)
    except jsonschema.ValidationError as e:
        if strict:
            raise ValidationError(f"Schema validation failed: {e.message}") from e
        # In non-strict mode, only fail on critical errors
        if isinstance(e.validator, str) and e.validator in ("required", "type"):
            raise ValidationError(f"Critical validation error: {e.message}") from e


def detect_circular_dependencies(tasks: List[Task]) -> Optional[List[str]]:
    """Detect circular dependencies using DFS."""
    # Build task name mapping (task name -> full name within same project)
    name_to_full_name = {}
    for task in tasks:
        task_name = task.name
        # Map both simple name and full name to full name
        name_to_full_name[task_name] = task.full_name
        name_to_full_name[task.full_name] = task.full_name

    # Build dependency graph with full names
    graph: Dict[str, Set[str]] = {}
    for task in tasks:
        deps = set()
        for dep_name in task.instruction.dependencies:
            # Convert dependency name to full name if it exists in this project
            if dep_name in name_to_full_name:
                deps.add(name_to_full_name[dep_name])
            else:
                # Keep external dependencies as-is (they might be from other projects)
                deps.add(dep_name)
        graph[task.full_name] = deps

    # DFS to detect cycles
    WHITE, GRAY, BLACK = 0, 1, 2
    colors: Dict[str, int] = {task.full_name: WHITE for task in tasks}

    def dfs(node: str, path: List[str]) -> Optional[List[str]]:
        if colors.get(node, BLACK) == GRAY:
            # Found cycle - return the cycle path
            cycle_start = path.index(node)
            return path[cycle_start:] + [node]

        if colors.get(node, BLACK) == BLACK:
            return None

        colors[node] = GRAY

        for neighbor in graph.get(node, set()):
            if neighbor in colors:  # Only check dependencies that exist in this project
                cycle = dfs(neighbor, path + [node])
                if cycle:
                    return cycle

        colors[node] = BLACK
        return None

    for task_name in graph:
        if colors[task_name] == WHITE:
            cycle = dfs(task_name, [])
            if cycle:
                return cycle

    return None


def validate_file_references(
    task: Task, workspace_path: Path, check_inputs: bool = True, check_outputs: bool = False
) -> List[str]:
    """Validate input/output file references."""
    errors = []

    if check_inputs:
        for input_file in task.instruction.inputs:
            input_path = task.path / input_file
            if not input_path.exists():
                errors.append(f"Input file not found: {input_file}")

    if check_outputs:
        for output_file in task.instruction.outputs:
            output_path = task.path / output_file
            if not output_path.exists():
                errors.append(f"Output file not found: {output_file}")

    return errors
