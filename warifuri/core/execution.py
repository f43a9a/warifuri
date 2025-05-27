"""Task execution engine."""

import datetime
import logging
import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Optional

from ..core.types import Task, TaskType
from ..utils.filesystem import (
    copy_directory_contents,
    create_temp_dir,
    get_git_commit_sha,
    safe_write_file,
)

logger = logging.getLogger(__name__)


class ExecutionError(Exception):
    """Task execution error."""

    pass


def setup_task_environment(task: Task) -> Dict[str, str]:
    """Setup environment variables for task execution."""
    workspace_path = task.path.parent.parent.parent  # Go up from task to workspace

    return {
        "WARIFURI_PROJECT_NAME": task.project,
        "WARIFURI_TASK_NAME": task.name,
        "WARIFURI_WORKSPACE_DIR": str(workspace_path.absolute()),
        "WARIFURI_INPUT_DIR": "input",
        "WARIFURI_OUTPUT_DIR": "output",
    }


def execute_machine_task(task: Task, dry_run: bool = False) -> bool:
    """Execute machine task in temporary directory."""
    logger.info(f"Executing machine task: {task.full_name}")

    if dry_run:
        logger.info(f"[DRY RUN] Would execute machine task: {task.full_name}")
        return True

    # Create temporary directory
    temp_dir = create_temp_dir()
    try:
        # Copy task directory to temp
        copy_directory_contents(task.path, temp_dir)

        # Find execution script
        run_script = None
        for pattern in ["run.sh", "run.py"]:
            script_path = temp_dir / pattern
            if script_path.exists():
                run_script = script_path
                break

        if not run_script:
            raise ExecutionError(f"No executable script found in {task.full_name}")

        # Setup environment
        env = setup_task_environment(task)

        # Execute script
        if run_script.suffix == ".sh":
            cmd = ["bash", "-euo", "pipefail", str(run_script)]
        elif run_script.suffix == ".py":
            cmd = ["python", str(run_script)]
        else:
            raise ExecutionError(f"Unsupported script type: {run_script}")

        logger.debug(f"Executing command: {' '.join(cmd)}")
        logger.debug(f"Working directory: {temp_dir}")

        result = subprocess.run(
            cmd,
            cwd=temp_dir,
            env={**dict(os.environ), **env},
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # Log failure
            log_failure(task, result.stderr, "Machine execution failed")
            return False

        # Copy back outputs
        copy_outputs_back(task, temp_dir)

        # Create done.md
        create_done_file(task, "Machine task completed successfully")

        logger.info(f"Machine task completed: {task.full_name}")
        return True

    except Exception as e:
        logger.error(f"Machine task failed: {task.full_name} - {e}")
        log_failure(task, str(e), "Machine execution error")
        return False
    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def execute_ai_task(task: Task, dry_run: bool = False) -> bool:
    """Execute AI task using LLM API."""
    logger.info(f"Executing AI task: {task.full_name}")

    if dry_run:
        logger.info(f"[DRY RUN] Would execute AI task: {task.full_name}")
        return True

    try:
        from ..utils.llm import LLMClient, load_prompt_config, save_ai_response, log_ai_error

        # Load prompt configuration
        prompt_config = load_prompt_config(task.path)

        # Initialize LLM client
        llm_client = LLMClient(
            model=prompt_config.get("model", "gpt-3.5-turbo"),
            temperature=prompt_config.get("temperature", 0.7),
        )

        # Build prompts
        system_prompt = prompt_config.get("system_prompt", "You are a helpful AI assistant.")

        # Combine system prompt with task description if no explicit prompt provided
        if "prompt" in prompt_config:
            user_prompt = prompt_config["prompt"]
        else:
            user_prompt = task.instruction.description

        # Add context from task instruction
        if task.instruction.note:
            user_prompt += f"\n\nAdditional context:\n{task.instruction.note}"

        # Generate response
        logger.info(f"Generating AI response for {task.full_name}")
        response = llm_client.generate_response(system_prompt, user_prompt)

        # Save response
        save_ai_response(response, task.path)

        # Create done.md
        create_done_file(task, "AI task completed successfully")

        logger.info(f"AI task completed: {task.full_name}")
        return True

    except Exception as e:
        logger.error(f"AI task failed: {task.full_name}: {e}")
        log_ai_error(e, task.path)
        return False


def execute_human_task(task: Task, dry_run: bool = False) -> bool:
    """Handle human task execution."""
    logger.info(f"Human task: {task.full_name}")

    if dry_run:
        logger.info(f"[DRY RUN] Human task requires manual intervention: {task.full_name}")
    else:
        print(f"Human task '{task.full_name}' requires manual intervention.")
        print(f"Description: {task.instruction.description}")
        print("Please complete the task manually and run 'warifuri mark-done' when finished.")

    return True


def check_dependencies(task: Task, all_tasks: list) -> bool:
    """Check if task dependencies are satisfied."""
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
    task: Task, dry_run: bool = False, force: bool = False, all_tasks: Optional[list] = None
) -> bool:
    """Execute task based on its type."""
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


def copy_outputs_back(task: Task, temp_dir: Path) -> None:
    """Copy output files back to task directory."""
    for output_file in task.instruction.outputs:
        src_file = temp_dir / output_file
        dst_file = task.path / output_file

        if src_file.exists():
            # Ensure destination directory exists
            dst_file.parent.mkdir(parents=True, exist_ok=True)

            if src_file.is_file():
                shutil.copy2(src_file, dst_file)
            else:
                shutil.copytree(src_file, dst_file, dirs_exist_ok=True)

            logger.debug(f"Copied output: {output_file}")


def create_done_file(task: Task, message: Optional[str] = None) -> None:
    """Create done.md file with timestamp and commit SHA."""
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    commit_sha = get_git_commit_sha() or "unknown"

    content = f"{timestamp} SHA: {commit_sha}"
    if message:
        content = f"{message}\n\n{content}"

    done_file = task.path / "done.md"
    safe_write_file(done_file, content)

    logger.debug(f"Created done.md for {task.full_name}")


def log_failure(task: Task, error_message: str, error_type: str) -> None:
    """Log task execution failure."""
    logs_dir = task.path / "logs"
    logs_dir.mkdir(exist_ok=True)

    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"failed_{timestamp}.log"

    log_content = f"""Task: {task.full_name}
Type: {error_type}
Timestamp: {now.isoformat()}
Error: {error_message}
"""

    safe_write_file(log_file, log_content)
    logger.debug(f"Logged failure to {log_file}")
