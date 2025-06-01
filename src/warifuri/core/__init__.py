"""Core package initialization."""

from .discovery import (
    discover_all_projects,
    discover_project,
    discover_task,
    find_ready_tasks,
    find_task_by_name,
)
from .execution import ExecutionError, execute_task
from .types import Project, Task, TaskInstruction, TaskStatus, TaskType

__all__: list[str] = [
    "Task",
    "TaskInstruction",
    "TaskStatus",
    "TaskType",
    "Project",
    "discover_all_projects",
    "discover_project",
    "discover_task",
    "find_ready_tasks",
    "find_task_by_name",
    "execute_task",
    "ExecutionError",
]
