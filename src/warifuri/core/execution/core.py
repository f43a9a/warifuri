"""Core execution functions - dependency checking, main execute_task, and output operations."""

import datetime
import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from ...utils.filesystem import get_git_commit_sha, safe_write_file
from .ai import execute_ai_task
from .errors import ExecutionError
from .human import execute_human_task
from .machine import execute_machine_task

if TYPE_CHECKING:
    from ...core.types import Task

logger = logging.getLogger(__name__)


def check_dependencies(task: "Task", all_tasks: List["Task"]) -> bool:
    """Check if task dependencies are satisfied.

    Args:
        task: The task to check dependencies for
        all_tasks: List of all available tasks for dependency lookup

    Returns:
        True if all dependencies are satisfied, False otherwise
    """
    if not task.instruction.dependencies:
        return True

    # Create lookup for all tasks by full name and short name
    task_lookup = {t.full_name: t for t in all_tasks}
    # Also allow matching by task name within the same project
    for t in all_tasks:
        if t.project == task.project:
            task_lookup[t.name] = t

    for dep in task.instruction.dependencies:
        # Try full name first
        dep_task = task_lookup.get(dep)

        # If not found and it's a simple name, try project/dep format
        if not dep_task and "/" not in dep:
            full_dep_name = f"{task.project}/{dep}"
            dep_task = task_lookup.get(full_dep_name)

        if not dep_task:
            logger.warning(f"Dependency '{dep}' not found for task {task.full_name}")
            return False

        if not dep_task.is_completed:
            logger.info(f"Dependency '{dep}' not completed for task {task.full_name}")
            return False

    return True


def execute_task(
    task: "Task",
    dry_run: bool = False,
    force: bool = False,
    all_tasks: Optional[List["Task"]] = None,
) -> bool:
    """Execute task based on its type.

    Args:
        task: The task to execute
        dry_run: If True, only log what would be done
        force: If True, execute even if already completed or dependencies not met
        all_tasks: List of all tasks for dependency checking

    Returns:
        True if execution succeeded, False otherwise
    """
    # Import here to avoid circular imports
    from ...core.types import TaskType

    # Check if task is already completed
    if task.is_completed and not force:
        logger.info(f"Task already completed: {task.full_name}")
        return True

    # Check dependencies (unless forced)
    if not force and all_tasks:
        if not check_dependencies(task, all_tasks):
            logger.error(f"Dependencies not satisfied for task: {task.full_name}")
            return False

    # Execute based on task type
    if task.task_type == TaskType.MACHINE:
        return execute_machine_task(task, dry_run)
    elif task.task_type == TaskType.AI:
        return execute_ai_task(task, dry_run)
    elif task.task_type == TaskType.HUMAN:
        return execute_human_task(task, dry_run)
    else:
        raise ExecutionError(f"Unknown task type: {task.task_type}")


def copy_outputs_back(
    task: "Task", temp_dir: Path, execution_log: Optional[List[str]] = None
) -> None:
    """Copy output files back to task directory with logging.

    Args:
        task: The task whose outputs to copy
        temp_dir: Temporary directory containing outputs
        execution_log: Log list to append copy results to
    """
    if execution_log is None:
        execution_log = []

    copied_files = []

    for output_file in task.instruction.outputs:
        src_file = temp_dir / output_file
        dst_file = task.path / output_file

        if src_file.exists():
            # Ensure destination directory exists
            dst_file.parent.mkdir(parents=True, exist_ok=True)

            if src_file.is_file():
                shutil.copy2(src_file, dst_file)
                copied_files.append(f"File: {output_file}")
            else:
                shutil.copytree(src_file, dst_file, dirs_exist_ok=True)
                copied_files.append(f"Directory: {output_file}")

            logger.debug(f"Copied output: {output_file}")
        else:
            logger.warning(f"Expected output not found: {output_file}")
            execution_log.append(f"WARNING: Expected output not found: {output_file}")

    if copied_files:
        execution_log.append(f"Copied outputs: {', '.join(copied_files)}")
    else:
        execution_log.append("No outputs to copy back")


def save_execution_log(task: "Task", execution_log: List[str], success: bool) -> None:
    """Save detailed execution log to logs directory.

    Args:
        task: The task that was executed
        execution_log: List of log entries from execution
        success: Whether execution was successful
    """
    logs_dir = task.path / "logs"
    logs_dir.mkdir(exist_ok=True)

    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    status = "success" if success else "failed"
    log_file = logs_dir / f"execution_{status}_{timestamp}.log"

    log_content = f"""Task: {task.full_name}
Type: Machine Task Execution
Status: {"SUCCESS" if success else "FAILED"}
Timestamp: {now.isoformat()}
Commit SHA: {get_git_commit_sha() or "unknown"}

EXECUTION LOG:
{"=" * 50}
"""

    for i, log_entry in enumerate(execution_log, 1):
        log_content += f"{i:3d}. {log_entry}\n"

    safe_write_file(log_file, log_content)
    logger.debug(f"Saved execution log to {log_file}")


def log_failure(
    task: "Task", error_message: str, error_type: str, execution_log: Optional[List[str]] = None
) -> None:
    """Log task execution failure with enhanced details.

    Args:
        task: The task that failed
        error_message: Error message to log
        error_type: Type of error that occurred
        execution_log: Optional execution log entries
    """
    logs_dir = task.path / "logs"
    logs_dir.mkdir(exist_ok=True)

    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"failed_{timestamp}.log"

    log_content = f"""Task: {task.full_name}
Type: {error_type}
Timestamp: {now.isoformat()}
Commit SHA: {get_git_commit_sha() or "unknown"}
Error: {error_message}

"""

    if execution_log:
        log_content += "EXECUTION LOG:\n"
        log_content += "=" * 50 + "\n"
        for i, log_entry in enumerate(execution_log, 1):
            log_content += f"{i:3d}. {log_entry}\n"

    safe_write_file(log_file, log_content)
    logger.debug(f"Logged failure to {log_file}")


def create_done_file(task: "Task", message: Optional[str] = None) -> None:
    """Create done.md file with timestamp and commit SHA.

    Args:
        task: The task to mark as done
        message: Optional custom message to include
    """
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    commit_sha = get_git_commit_sha() or "unknown"

    content = f"{timestamp} SHA: {commit_sha}"
    if message:
        content = f"{message}\n\n{content}"

    done_file = task.path / "done.md"
    safe_write_file(done_file, content)

    logger.debug(f"Created done.md for {task.full_name}")
