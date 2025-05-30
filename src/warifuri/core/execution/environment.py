"""Environment setup for task execution."""

import os
from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.types import Task


def setup_task_environment(task: "Task") -> Dict[str, str]:
    """Setup environment variables for task execution."""
    env_vars = {
        "TASK_NAME": task.name,
        "TASK_PATH": str(task.path),
        "TASK_TYPE": task.task_type.value,
    }

    if hasattr(task, "project"):
        env_vars["PROJECT_NAME"] = task.project

    return env_vars
