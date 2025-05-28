"""Type definitions for warifuri."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class TaskType(Enum):
    """Task execution type."""

    MACHINE = "machine"
    AI = "ai"
    HUMAN = "human"


class TaskStatus(Enum):
    """Task completion status."""

    READY = "ready"
    PENDING = "pending"
    COMPLETED = "completed"


@dataclass
class TaskInstruction:
    """Task instruction data from instruction.yaml."""

    name: str
    description: str
    dependencies: List[str]
    inputs: List[str]
    outputs: List[str]
    note: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskInstruction":
        """Create TaskInstruction from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            dependencies=data.get("dependencies", []),
            inputs=data.get("inputs", []),
            outputs=data.get("outputs", []),
            note=data.get("note"),
        )


@dataclass
class Task:
    """Complete task information."""

    project: str
    name: str
    path: Path
    instruction: TaskInstruction
    task_type: TaskType
    status: TaskStatus

    @property
    def full_name(self) -> str:
        """Return full task name (project/task)."""
        return f"{self.project}/{self.name}"

    @property
    def is_completed(self) -> bool:
        """Check if task is completed (done.md exists)."""
        return (self.path / "done.md").exists()

    @property
    def has_auto_merge(self) -> bool:
        """Check if auto_merge.yaml exists."""
        return (self.path / "auto_merge.yaml").exists()


@dataclass
class Project:
    """Project information."""

    name: str
    path: Path
    tasks: List[Task]

    def get_task(self, task_name: str) -> Optional[Task]:
        """Get task by name."""
        for task in self.tasks:
            if task.name == task_name:
                return task
        return None


# Type aliases
ProjectName = str
TaskName = str
FullTaskName = str  # project/task format
FilePath = Union[str, Path]
