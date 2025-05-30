"""Path security and validation utilities."""

import logging
from pathlib import Path
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.types import Task

logger = logging.getLogger(__name__)


def _resolve_input_path_safely(input_file: str, task_path: Path, projects_base: Path) -> tuple[Path | None, str]:
    """Safely resolve input file path preventing path traversal attacks.

    Args:
        input_file: Input file path (potentially with ../)
        task_path: Current task directory
        projects_base: Base projects directory

    Returns:
        Tuple of (resolved_path, log_message) or (None, error_message)
    """
    try:
        if input_file.startswith("../"):
            # Count ../ sequences and check for excessive traversal
            clean_path = input_file
            traversal_count = 0
            while clean_path.startswith("../"):
                clean_path = clean_path[3:]
                traversal_count += 1
                # Prevent excessive path traversal
                if traversal_count > 10:
                    return None, f"SECURITY: Excessive path traversal detected in {input_file}"

            # Build expected path from projects base
            source_path = task_path
            for _ in range(traversal_count):
                source_path = source_path.parent
                # Ensure we don't traverse above projects directory
                if not str(source_path).startswith(str(projects_base)):
                    return None, f"SECURITY: Path traversal outside projects directory: {input_file}"

            source_path = source_path / clean_path

            # Additional security check: ensure resolved path is within projects
            if not str(source_path.resolve()).startswith(str(projects_base.resolve())):
                return None, f"SECURITY: Resolved path outside projects directory: {input_file}"

            return source_path, f"Resolved cross-project input: {input_file} -> {source_path}"
        else:
            # Regular file within task directory
            return task_path / input_file, f"Local input file: {input_file}"

    except Exception as e:
        return None, f"ERROR resolving path {input_file}: {e}"


def validate_task_inputs(task: "Task", execution_log: List[str], workspace_path: Optional[Path] = None) -> bool:
    """Validate that all input files exist before task execution."""
    if not task.instruction.inputs:
        execution_log.append("No input files to validate")
        return True

    if workspace_path is None:
        workspace_path = task.path.parent.parent.parent
    projects_base = workspace_path / "projects"

    all_inputs_valid = True
    execution_log.append("Validating input files...")

    for input_file in task.instruction.inputs:
        source_path, log_message = _resolve_input_path_safely(input_file, task.path, projects_base)
        execution_log.append(log_message)

        if source_path is None:
            all_inputs_valid = False
            continue

        if not source_path.exists():
            execution_log.append(f"ERROR: Input file not found: {source_path}")
            all_inputs_valid = False
        else:
            execution_log.append(f"✓ Input file exists: {source_path}")

    return all_inputs_valid


def validate_task_outputs(task: "Task", temp_dir: Path, execution_log: List[str]) -> bool:
    """Validate that all expected output files were created."""
    if not task.instruction.outputs:
        execution_log.append("No output files to validate")
        return True

    all_outputs_valid = True
    execution_log.append("Validating output files...")

    for output_file in task.instruction.outputs:
        output_path = temp_dir / output_file
        if not output_path.exists():
            execution_log.append(f"ERROR: Expected output file not created: {output_file}")
            all_outputs_valid = False
        else:
            execution_log.append(f"✓ Output file created: {output_file}")

    return all_outputs_valid
