"""Path security and validation utilities."""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from ...core.types import Task

logger = logging.getLogger(__name__)


def _resolve_input_path_safely(
    input_file: str, task_path: Path, projects_base: Path
) -> tuple[Path | None, str]:
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
                    return (
                        None,
                        f"SECURITY: Path traversal outside projects directory: {input_file}",
                    )

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


def validate_task_inputs(
    task: "Task", execution_log: List[str], workspace_path: Optional[Path] = None
) -> bool:
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
        # When validating inputs for a task, the paths in `task.instruction.inputs`
        # are relative to the task's own directory (`task.path`).
        # The `_resolve_input_path_safely` function handles resolving these,
        # including cases like `../other_project/file.txt`.
        # The `source_path` returned is the absolute path to the input file
        # in the *original* workspace structure.
        source_path, log_message = _resolve_input_path_safely(input_file, task.path, projects_base)
        execution_log.append(log_message)

        if source_path is None:  # Indicates a security or resolution error
            all_inputs_valid = False
            # The error message from _resolve_input_path_safely is already in execution_log
            continue

        if not source_path.exists():
            # This is the critical check: does the resolved source file exist in the workspace?
            execution_log.append(
                f"ERROR: Missing input file: {input_file} (resolved to {source_path})"
            )
            all_inputs_valid = False
        else:
            execution_log.append(f"✓ Input file exists: {input_file} (resolved to {source_path})")

    return all_inputs_valid


def validate_task_outputs(task: "Task", temp_dir: Path, execution_log: List[str]) -> bool:
    """Validate that all expected output files were created."""
    if not task.instruction.outputs:
        execution_log.append("No output files to validate")
        return True

    all_outputs_valid = True
    execution_log.append("Validating output files...")

    for output_file in task.instruction.outputs:
        # Output files are expected to be in the `temp_dir` (or `temp_dir/output` if using WARIFURI_OUTPUT_DIR)
        # For now, let's assume they are directly in temp_dir as per current logic.
        # If WARIFURI_OUTPUT_DIR is consistently "output", this should be temp_dir / "output" / output_file

        # Check if the output is expected in a subdirectory (e.g. "data/result.json")
        # The `output_file` string itself can contain subdirectories.
        output_path = temp_dir / output_file

        if not output_path.exists():
            execution_log.append(
                f"ERROR: Missing expected output: {output_file} (expected at {output_path})"
            )
            all_outputs_valid = False
        else:
            execution_log.append(f"✓ Output file created: {output_file} (at {output_path})")

    return all_outputs_valid
