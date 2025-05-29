"""Task execution engine."""

import datetime
import logging
import os
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional

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
        "WARIFURI_TEMP_DIR": ".",  # Current working directory in temp
    }


def validate_task_inputs(task: Task, execution_log: List[str], workspace_path: Optional[Path] = None) -> bool:
    """Validate that all required input files exist with cross-project support."""
    if workspace_path is None:
        # Try to infer workspace path from task path
        # Typical structure: workspace/projects/{project}/{task}
        workspace_path = task.path.parent.parent.parent

    missing_inputs = []

    for input_file in task.instruction.inputs:
        found = False

        # Check workspace root first
        input_path = workspace_path / input_file
        if input_path.exists():
            found = True
            execution_log.append(f"Input file found in workspace root: {input_file}")
        else:
            # Check if it's a relative path
            if input_file.startswith("../"):
                # Try resolving relative to task directory
                task_relative_input = task.path / input_file
                if task_relative_input.exists():
                    found = True
                    execution_log.append(f"Input file found via relative path: {input_file}")
                else:
                    # Try cross-project resolution
                    # Get the projects directory path properly
                    projects_base = task.path.parent.parent  # Go up from task to projects level

                    if projects_base.exists():
                        # Remove the ../ prefix and resolve from projects directory
                        clean_path = input_file
                        while clean_path.startswith("../"):
                            clean_path = clean_path[3:]

                        cross_project_input = projects_base / clean_path

                        execution_log.append(f"Trying cross-project path: {cross_project_input}")
                        if cross_project_input.exists():
                            found = True
                            execution_log.append(f"Input file found via cross-project path: {input_file}")
                        else:
                            execution_log.append(f"Cross-project path not found: {cross_project_input}")

            # Fallback: check in task directory
            if not found:
                fallback_path = task.path / input_file
                if fallback_path.exists():
                    found = True
                    execution_log.append(f"Input file found in task directory: {input_file}")

        if not found:
            missing_inputs.append(input_file)
            execution_log.append(f"ERROR: Missing input file: {input_file}")

    if missing_inputs:
        error_msg = f"Missing required input files: {', '.join(missing_inputs)}"
        execution_log.append(f"VALIDATION FAILED: {error_msg}")
        return False

    execution_log.append("Input validation: PASSED")
    return True


def validate_task_outputs(task: Task, temp_dir: Path, execution_log: List[str]) -> bool:
    """Validate that all expected output files were created."""
    missing_outputs = []

    for output_file in task.instruction.outputs:
        output_path = temp_dir / output_file
        if not output_path.exists():
            missing_outputs.append(output_file)
            execution_log.append(f"ERROR: Missing expected output: {output_file}")
        else:
            execution_log.append(f"Expected output found: {output_file}")

    if missing_outputs:
        error_msg = f"Missing expected output files: {', '.join(missing_outputs)}"
        execution_log.append(f"OUTPUT VALIDATION FAILED: {error_msg}")
        return False

    execution_log.append("Output validation: PASSED")
    return True


def copy_input_files(task: Task, temp_dir: Path, execution_log: List[str], workspace_path: Optional[Path] = None) -> None:
    """Copy input files to temporary directory with cross-project support."""
    execution_log.append(f"copy_input_files called for task {task.name}")

    if not task.instruction or not task.instruction.inputs:
        execution_log.append("No inputs to copy")
        return

    execution_log.append(f"Found {len(task.instruction.inputs)} inputs to copy: {task.instruction.inputs}")

    if workspace_path is None:
        # Try to infer workspace path from task path
        workspace_path = task.path.parent.parent.parent

    execution_log.append(f"Using workspace path: {workspace_path}")

    for input_file in task.instruction.inputs:
        # Find where the input file actually exists
        source_path = None

        # Check workspace root first
        workspace_input = workspace_path / input_file
        if workspace_input.exists():
            source_path = workspace_input
            execution_log.append(f"Found input in workspace root: {input_file}")
        else:
            # Check if it's a relative path
            if input_file.startswith("../"):
                # Try resolving relative to task directory
                task_relative_input = task.path / input_file
                if task_relative_input.exists():
                    source_path = task_relative_input.resolve()
                    execution_log.append(f"Found input via relative path: {input_file}")
                else:
                    # Try cross-project resolution
                    # Get the projects directory path properly
                    projects_base = task.path.parent.parent  # Go up from task to projects level

                    if projects_base.exists():
                        # Remove the ../ prefix and resolve from projects directory
                        clean_path = input_file
                        while clean_path.startswith("../"):
                            clean_path = clean_path[3:]

                        cross_project_input = projects_base / clean_path

                        if cross_project_input.exists():
                            source_path = cross_project_input.resolve()
                            execution_log.append(f"Found input via cross-project path: {input_file}")

        # Fallback: check in task directory
        if source_path is None:
            task_input = task.path / input_file
            if task_input.exists():
                source_path = task_input
                execution_log.append(f"Found input in task directory: {input_file}")

        if source_path is None:
            execution_log.append(f"WARNING: Could not locate input file for copying: {input_file}")
            continue

        # Determine destination path in temp directory
        # For relative paths, we need to make them accessible within the temp directory
        # Instead of preserving ../config-generator/shared.conf structure,
        # we should flatten it to just shared.conf in the temp directory
        if input_file.startswith("../"):
            # Extract just the filename for relative paths
            dest_path = temp_dir / Path(input_file).name
            execution_log.append(f"Flattening relative path {input_file} to {Path(input_file).name}")
        else:
            # For absolute or simple file names, place directly in temp
            dest_path = temp_dir / Path(input_file).name

        # Create parent directories if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy the file
        try:
            if source_path.is_file():
                shutil.copy2(source_path, dest_path)
                execution_log.append(f"Copied input file: {input_file} -> {dest_path}")
            else:
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                execution_log.append(f"Copied input directory: {input_file} -> {dest_path}")
        except Exception as e:
            execution_log.append(f"ERROR copying input {input_file}: {e}")


def execute_machine_task(task: Task, dry_run: bool = False) -> bool:
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

        # Validate input files before execution
        workspace_path = task.path.parent.parent.parent
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

        # Find execution script
        run_script = None
        for pattern in ["run.sh", "run.py"]:
            script_path = temp_dir / pattern
            if script_path.exists():
                run_script = script_path
                break

        if not run_script:
            error_msg = f"No executable script found in {task.full_name}"
            execution_log.append(f"ERROR: {error_msg}")
            raise ExecutionError(error_msg)

        execution_log.append(f"Found executable script: {run_script.name}")

        # Setup environment
        env = setup_task_environment(task)
        execution_log.append(f"Environment variables: {list(env.keys())}")

        # Execute script with enhanced bash safety
        if run_script.suffix == ".sh":
            cmd = ["bash", "-euo", "pipefail", str(run_script)]
        elif run_script.suffix == ".py":
            cmd = ["python", str(run_script)]
        else:
            error_msg = f"Unsupported script type: {run_script}"
            execution_log.append(f"ERROR: {error_msg}")
            raise ExecutionError(error_msg)

        logger.debug(f"Executing command: {' '.join(cmd)}")
        logger.debug(f"Working directory: {temp_dir}")
        execution_log.append(f"Command: {' '.join(cmd)}")
        execution_log.append(f"Working directory: {temp_dir}")

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

        if result.returncode != 0:
            # Log failure with detailed execution log
            log_failure(task, result.stderr, "Machine execution failed", execution_log)
            return False

        # Validate outputs were created
        if not validate_task_outputs(task, temp_dir, execution_log):
            log_failure(
                task, "Expected output files not created", "Output validation failed", execution_log
            )
            return False

        # Copy back outputs
        copy_outputs_back(task, temp_dir, execution_log)

        # Validate output files
        if not validate_task_outputs(task, temp_dir, execution_log):
            error_msg = "Output validation failed"
            execution_log.append(f"ERROR: {error_msg}")
            log_failure(task, error_msg, "Output validation error", execution_log)
            return False

        # Save execution log
        save_execution_log(task, execution_log, success=True)

        # Create done.md
        create_done_file(task, "Machine task completed successfully")

        logger.info(f"Machine task completed: {task.full_name}")
        return True

    except Exception as e:
        logger.error(f"Machine task failed: {task.full_name} - {e}")
        execution_log.append(f"EXCEPTION: {str(e)}")
        log_failure(task, str(e), "Machine execution error", execution_log)
        return False
    finally:
        # Clean up temp directory
        logger.debug(f"Cleaning up temporary directory: {temp_dir}")
        execution_log.append(f"Cleaned up temporary directory: {temp_dir}")
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


def check_dependencies(task: Task, all_tasks: List[Task]) -> bool:
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
    task: Task, dry_run: bool = False, force: bool = False, all_tasks: Optional[List[Task]] = None
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


def copy_outputs_back(
    task: Task, temp_dir: Path, execution_log: Optional[List[str]] = None
) -> None:
    """Copy output files back to task directory with logging."""
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


def save_execution_log(task: Task, execution_log: List[str], success: bool) -> None:
    """Save detailed execution log to logs directory."""
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
    task: Task, error_message: str, error_type: str, execution_log: Optional[List[str]] = None
) -> None:
    """Log task execution failure with enhanced details."""
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
