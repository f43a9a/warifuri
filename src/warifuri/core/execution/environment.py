"""Environment setup for task execution."""

from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from ...core.types import Task


def setup_task_environment(task: "Task") -> Dict[str, str]:
    """Setup environment variables for task execution."""
    workspace_dir = task.path.parent.parent.parent

    env_vars = {
        "TASK_NAME": task.name,
        "TASK_PATH": str(task.path),
        "TASK_TYPE": task.task_type.value,
        "PROJECT_NAME": task.project,  # Retained for compatibility if used elsewhere
        "WARIFURI_PROJECT_NAME": task.project,
        "WARIFURI_TASK_NAME": task.name,
        "WARIFURI_WORKSPACE_DIR": str(workspace_dir),
        "WARIFURI_INPUT_DIR": "input",
        "WARIFURI_OUTPUT_DIR": "output",
    }

    return env_vars
