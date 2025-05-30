"""Task discovery and management."""

from pathlib import Path
from typing import List, Optional

from ..core.types import Project, Task, TaskInstruction, TaskStatus, TaskType
from ..utils.filesystem import list_projects
from ..utils.yaml_utils import load_yaml


def determine_task_type(task_path: Path) -> TaskType:
    """Determine task type based on files present."""
    # Check for machine task files
    for pattern in ["*.sh", "*.py"]:
        if list(task_path.glob(pattern)):
            return TaskType.MACHINE

    # Check for AI task file
    if (task_path / "prompt.yaml").exists():
        return TaskType.AI

    # Default to human task
    return TaskType.HUMAN


def determine_task_status(task: Task) -> TaskStatus:
    """Determine task status based on completion and dependencies."""
    if task.is_completed:
        return TaskStatus.COMPLETED

    # Check if all dependencies are completed
    # Note: This requires access to all tasks for dependency resolution
    # For now, return READY if not completed
    return TaskStatus.READY


def load_task_instruction(instruction_path: Path) -> TaskInstruction:
    """Load task instruction from instruction.yaml."""
    data = load_yaml(instruction_path)
    return TaskInstruction.from_dict(data)


def discover_task(project_name: str, task_path: Path) -> Task:
    """Discover and load a single task."""
    task_name = task_path.name
    instruction_path = task_path / "instruction.yaml"

    if not instruction_path.exists():
        raise FileNotFoundError(f"instruction.yaml not found in {task_path}")

    instruction = load_task_instruction(instruction_path)
    task_type = determine_task_type(task_path)

    task = Task(
        project=project_name,
        name=task_name,
        path=task_path,
        instruction=instruction,
        task_type=task_type,
        status=TaskStatus.PENDING,  # Will be updated later
    )

    # Update status after task is created
    task.status = determine_task_status(task)

    return task


def discover_project(workspace_path: Path, project_name: str) -> Project:
    """Discover and load a project with all its tasks."""
    from ..utils.validation import detect_circular_dependencies, CircularDependencyError

    project_path = workspace_path / "projects" / project_name

    if not project_path.exists():
        raise FileNotFoundError(f"Project not found: {project_name}")

    tasks = []
    for task_dir in project_path.iterdir():
        if task_dir.is_dir() and not task_dir.name.startswith("."):
            try:
                task = discover_task(project_name, task_dir)
                tasks.append(task)
            except FileNotFoundError:
                # Skip directories without instruction.yaml
                continue

    # Check for circular dependencies
    cycle = detect_circular_dependencies(tasks)
    if cycle:
        # For the graph command, we want to show the graph even with circular dependencies
        # Just raise the error - the safe discovery function will catch it
        raise CircularDependencyError(f"Circular dependency detected: {' -> '.join(cycle)}")

    return Project(
        name=project_name,
        path=project_path,
        tasks=tasks,
    )


def discover_project_safe(workspace_path: Path, project_name: str) -> Optional[Project]:
    """Discover a project without raising exceptions on circular dependencies.

    This is useful for graph visualization where we want to show the structure
    even when there are circular dependencies.
    """
    project_path = workspace_path / "projects" / project_name
    if not project_path.exists():
        return None

    tasks = []
    for task_dir in project_path.iterdir():
        if task_dir.is_dir() and not task_dir.name.startswith("."):
            try:
                task = discover_task(project_name, task_dir)
                tasks.append(task)
            except FileNotFoundError:
                # Skip directories without instruction.yaml
                continue

    # Don't check for circular dependencies - just create the project
    return Project(
        name=project_name,
        path=project_path,
        tasks=tasks,
    )


def discover_all_projects(workspace_path: Path) -> List[Project]:
    """Discover all projects in workspace."""
    projects = []
    project_names = list_projects(workspace_path)

    for project_name in project_names:
        try:
            project = discover_project(workspace_path, project_name)
            projects.append(project)
        except FileNotFoundError:
            # Skip projects without valid tasks
            continue

    return projects


def discover_all_projects_safe(workspace_path: Path) -> List[Project]:
    """Discover all projects without raising exceptions on circular dependencies."""
    projects: List[Project] = []
    projects_dir = workspace_path / "projects"

    if not projects_dir.exists():
        return projects

    for project_dir in projects_dir.iterdir():
        if project_dir.is_dir() and not project_dir.name.startswith("."):
            project = discover_project_safe(workspace_path, project_dir.name)
            if project:
                projects.append(project)

    return projects


def find_ready_tasks(projects: List[Project], workspace_path: Optional[Path] = None) -> List[Task]:
    """Find all ready tasks across projects."""
    if not projects:
        return []

    # Get workspace path from first project if not provided
    if workspace_path is None:
        workspace_path = projects[0].path.parent.parent

    # Build task lookup for dependency checking
    all_tasks = {}
    for project in projects:
        for task in project.tasks:
            all_tasks[task.full_name] = task

    ready_tasks = []
    for project in projects:
        for task in project.tasks:
            if task.is_completed:
                continue

            # Check if all dependencies are completed
            dependencies_ready = True
            for dep_name in task.instruction.dependencies:
                # Try full name first
                dep_task = all_tasks.get(dep_name)

                # If not found and it's a simple name, try project/dep format
                if not dep_task and "/" not in dep_name:
                    full_dep_name = f"{project.name}/{dep_name}"
                    dep_task = all_tasks.get(full_dep_name)

                if not dep_task or not dep_task.is_completed:
                    dependencies_ready = False
                    break

            # Check if all input files exist (if task has inputs)
            inputs_ready = True
            if task.instruction.inputs:
                # Import here to avoid circular import
                from ..utils.validation import validate_file_references

                file_errors = validate_file_references(task, workspace_path, check_inputs=True)
                if file_errors:
                    inputs_ready = False

            if dependencies_ready and inputs_ready:
                task.status = TaskStatus.READY
                ready_tasks.append(task)
            else:
                task.status = TaskStatus.PENDING

    return ready_tasks


def find_task_by_name(
    projects: List[Project], project_name: str, task_name: Optional[str] = None
) -> Optional[Task]:
    """Find task by project and task name."""
    for project in projects:
        if project.name == project_name:
            if task_name is None:
                # Return first ready task in project
                ready_tasks = [t for t in project.tasks if t.status == TaskStatus.READY]
                return ready_tasks[0] if ready_tasks else None
            else:
                return project.get_task(task_name)

    return None
