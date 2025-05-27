"""Core package initialization."""

from .discovery import (
    discover_all_projects,
    discover_project,
    discover_task,
    find_ready_tasks,
    find_task_by_name,
)
from .execution import execute_task, ExecutionError
from .types import Task, TaskInstruction, TaskStatus, TaskType, Project

__all__ = [
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
