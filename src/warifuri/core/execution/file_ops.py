"""File operations for task execution."""

import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from .validation import _resolve_input_path_safely

if TYPE_CHECKING:
    from ...core.types import Task

logger = logging.getLogger(__name__)


def copy_input_files(
    task: "Task", temp_dir: Path, execution_log: List[str], workspace_path: Optional[Path] = None
) -> None:
    """Copy input files to temporary directory for task execution."""
    if not task.instruction.inputs:
        execution_log.append("No input files to copy")
        return

    if workspace_path is None:
        workspace_path = task.path.parent.parent.parent
    projects_base = workspace_path / "projects"

    execution_log.append("Copying input files to temporary directory...")

    for input_file in task.instruction.inputs:
        source_path, log_message = _resolve_input_path_safely(input_file, task.path, projects_base)
        execution_log.append(log_message)

        if source_path is None:
            continue

        if not source_path.exists():
            execution_log.append(f"ERROR: Input file not found during copy: {source_path}")
            continue

        # Create destination path in temp directory
        if input_file.startswith("../"):
            # For cross-project files, flatten the path structure
            dest_filename = input_file.replace("../", "").replace("/", "_")
            dest_path = temp_dir / dest_filename
        else:
            # Preserve relative structure for local files
            dest_path = temp_dir / input_file

        # Ensure destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file or directory
        _copy_file_or_directory(source_path, dest_path, input_file, execution_log)


def _copy_file_or_directory(
    source_path: Path, dest_path: Path, input_file: str, execution_log: List[str]
) -> None:
    """Copy a single file or directory."""
    try:
        if source_path.is_file():
            shutil.copy2(source_path, dest_path)
            execution_log.append(f"Copied input file: {input_file} -> {dest_path}")
        else:
            shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
            execution_log.append(f"Copied input directory: {input_file} -> {dest_path}")
    except Exception as e:
        execution_log.append(f"ERROR copying input {input_file}: {e}")
