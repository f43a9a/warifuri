"""Machine task execution."""

import logging
import os
import subprocess
from pathlib import Path
from typing import List, TYPE_CHECKING

from ...utils.atomic import safe_rmtree
from ...utils.filesystem import copy_directory_contents, create_temp_dir
from .environment import setup_task_environment
from .errors import ExecutionError
from .file_ops import copy_input_files
from .validation import validate_task_inputs, validate_task_outputs

if TYPE_CHECKING:
    from ...core.types import Task

logger = logging.getLogger(__name__)


def execute_machine_task(task: "Task", dry_run: bool = False) -> bool:
    """Execute machine task in temporary directory with enhanced sandboxing."""
    logger.info(f"Executing machine task: {task.full_name}")

    if dry_run:
        logger.info(f"[DRY RUN] Would execute machine task: {task.full_name}")
        return True

    # Create temporary directory
    temp_dir = create_temp_dir()
    execution_log = []

    try:
        logger.debug(f"Created temporary directory: {temp_dir}")
        execution_log.append(f"Temporary directory: {temp_dir}")

        # Setup environment for machine task
        _setup_machine_task_environment(task, temp_dir, execution_log)

        # Find execution script
        run_script = _find_execution_script(temp_dir, task, execution_log)

        # Build execution command
        cmd = _build_execution_command(run_script, execution_log)

        # Execute script
        result = _execute_script(cmd, temp_dir, task, execution_log)

        if result.returncode != 0:
            # Log failure with detailed execution log
            from .core import log_failure
            log_failure(task, result.stderr, "Machine execution failed", execution_log)
            return False

        # Handle successful execution
        return _handle_machine_task_success(task, temp_dir, execution_log)

    except Exception as e:
        logger.error(f"Machine task failed: {task.full_name} - {e}")
        execution_log.append(f"EXCEPTION: {str(e)}")
        from .core import log_failure
        log_failure(task, str(e), "Machine execution error", execution_log)
        return False
    finally:
        # Clean up temp directory
        logger.debug(f"Cleaning up temporary directory: {temp_dir}")
        execution_log.append(f"Cleaned up temporary directory: {temp_dir}")
        safe_rmtree(temp_dir)


def _setup_machine_task_environment(task: "Task", temp_dir: Path, execution_log: List[str]) -> None:
    """Setup environment for machine task execution."""
    workspace_path = task.path.parent.parent.parent

    # Validate input files before execution
    if not validate_task_inputs(task, execution_log, workspace_path):
        error_msg = "Input validation failed"
        execution_log.append(f"ERROR: {error_msg}")
        raise ExecutionError(error_msg)

    # Copy task directory to temp
    copy_directory_contents(task.path, temp_dir)
    execution_log.append("Copied task files to temporary directory")

    # Copy input files to temp directory maintaining structure
    try:
        execution_log.append("Starting to copy input files...")
        execution_log.append("CRITICAL DEBUG: About to call copy_input_files")
        copy_input_files(task, temp_dir, execution_log, workspace_path)
        execution_log.append("CRITICAL DEBUG: copy_input_files completed")
        execution_log.append("Finished copying input files")
    except Exception as e:
        execution_log.append(f"ERROR in copy_input_files: {e}")
        raise


def _find_execution_script(temp_dir: Path, task: "Task", execution_log: List[str]) -> Path:
    """Find and return the execution script for the task."""
    for pattern in ["run.sh", "run.py"]:
        script_path = temp_dir / pattern
        if script_path.exists():
            execution_log.append(f"Found executable script: {script_path.name}")
            return script_path

    error_msg = f"No executable script found in {task.full_name}"
    execution_log.append(f"ERROR: {error_msg}")
    raise ExecutionError(error_msg)


def _build_execution_command(run_script: Path, execution_log: List[str]) -> List[str]:
    """Build the command to execute the script."""
    if run_script.suffix == ".sh":
        cmd = ["bash", "-euo", "pipefail", str(run_script)]
    elif run_script.suffix == ".py":
        cmd = ["python", str(run_script)]
    else:
        error_msg = f"Unsupported script type: {run_script}"
        execution_log.append(f"ERROR: {error_msg}")
        raise ExecutionError(error_msg)

    execution_log.append(f"Command: {' '.join(cmd)}")
    return cmd


def _execute_script(cmd: List[str], temp_dir: Path, task: "Task", execution_log: List[str]) -> subprocess.CompletedProcess:
    """Execute the script and return the result."""
    env = setup_task_environment(task)
    execution_log.append(f"Environment variables: {list(env.keys())}")
    execution_log.append(f"Working directory: {temp_dir}")

    logger.debug(f"Executing command: {' '.join(cmd)}")
    logger.debug(f"Working directory: {temp_dir}")

    result = subprocess.run(
        cmd,
        cwd=temp_dir,
        env={**dict(os.environ), **env},
        capture_output=True,
        text=True,
    )

    # Log execution results
    execution_log.append(f"Exit code: {result.returncode}")
    if result.stdout:
        execution_log.append(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        execution_log.append(f"STDERR:\n{result.stderr}")

    return result


def _handle_machine_task_success(task: "Task", temp_dir: Path, execution_log: List[str]) -> bool:
    """Handle successful machine task execution."""
    # Validate outputs were created
    if not validate_task_outputs(task, temp_dir, execution_log):
        # Import core functions to avoid circular imports
        from .core import log_failure
        log_failure(
            task, "Expected output files not created", "Output validation failed", execution_log
        )
        return False

    # Copy back outputs
    from .core import copy_outputs_back
    copy_outputs_back(task, temp_dir, execution_log)

    # Validate output files again
    if not validate_task_outputs(task, temp_dir, execution_log):
        error_msg = "Output validation failed"
        execution_log.append(f"ERROR: {error_msg}")
        from .core import log_failure
        log_failure(task, error_msg, "Output validation error", execution_log)
        return False

    # Save execution log
    from .core import save_execution_log, create_done_file
    save_execution_log(task, execution_log, success=True)

    # Create done.md
    create_done_file(task, "Machine task completed successfully")

    logger.info(f"Machine task completed: {task.full_name}")
    return True
