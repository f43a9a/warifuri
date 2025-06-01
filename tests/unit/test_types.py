"""Test core types and models."""

from warifuri.core.types import Task, TaskInstruction, TaskStatus, TaskType


def test_task_instruction_from_dict(sample_task_instruction):
    """Test TaskInstruction creation from dictionary."""
    instruction = TaskInstruction.from_dict(sample_task_instruction)

    assert instruction.name == "test_task"
    assert instruction.description == "A test task for validation"
    assert instruction.dependencies == []
    assert instruction.inputs == ["input.txt"]
    assert instruction.outputs == ["output.txt"]
    assert instruction.note == "Test note"


def test_task_instruction_minimal():
    """Test TaskInstruction with minimal required fields."""
    data = {
        "name": "minimal_task",
        "description": "Minimal task description",
    }

    instruction = TaskInstruction.from_dict(data)

    assert instruction.name == "minimal_task"
    assert instruction.description == "Minimal task description"
    assert instruction.dependencies == []
    assert instruction.inputs == []
    assert instruction.outputs == []
    assert instruction.note is None


def test_task_full_name(temp_workspace, sample_task_instruction):
    """Test Task full_name property."""
    instruction = TaskInstruction.from_dict(sample_task_instruction)
    task_path = temp_workspace / "projects" / "test_project" / "test_task"

    task = Task(
        project="test_project",
        name="test_task",
        path=task_path,
        instruction=instruction,
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING,
    )

    assert task.full_name == "test_project/test_task"


def test_task_is_completed(temp_workspace, sample_task_instruction):
    """Test Task is_completed property."""
    instruction = TaskInstruction.from_dict(sample_task_instruction)
    task_path = temp_workspace / "projects" / "test_project" / "test_task"
    task_path.mkdir(parents=True)

    task = Task(
        project="test_project",
        name="test_task",
        path=task_path,
        instruction=instruction,
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING,
    )

    # Initially not completed
    assert not task.is_completed

    # Create done.md
    (task_path / "done.md").touch()

    # Now completed
    assert task.is_completed
