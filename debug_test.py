"""Debug test to see what's happening."""

import tempfile
from pathlib import Path
from warifuri.core.discovery import discover_all_projects, find_ready_tasks
from warifuri.utils.filesystem import safe_write_file
from warifuri.utils.validation import validate_file_references

# Create test workspace
with tempfile.TemporaryDirectory() as temp_dir:
    workspace = Path(temp_dir)
    projects_dir = workspace / "projects"
    project_dir = projects_dir / "test-dependency-bug"

    # Create task A (foundation)
    task_a = project_dir / "task-a-foundation"
    task_a.mkdir(parents=True)
    safe_write_file(task_a / "instruction.yaml", """
name: task-a-foundation
task_type: human
description: "Foundation Task A"
dependencies: []
inputs: []
outputs:
  - "foundation_output.txt"
""")

    # Create task B (dependent)
    task_b = project_dir / "task-b-dependent"
    task_b.mkdir(parents=True)
    safe_write_file(task_b / "instruction.yaml", """
name: task-b-dependent
task_type: human
description: "Dependent Task B"
dependencies: ["task-a-foundation"]
inputs:
  - "foundation_output.txt"
outputs:
  - "dependent_output.txt"
""")

    # Mark task A as completed
    safe_write_file(task_a / "done.md", "Task A completed")

    # Create the required input file
    safe_write_file(workspace / "foundation_output.txt", "Foundation task completed")

    print(f"Workspace: {workspace}")
    print(f"Input file exists: {(workspace / 'foundation_output.txt').exists()}")

    # Discover projects
    projects = discover_all_projects(workspace)
    print(f"Found {len(projects)} projects")

    project = projects[0]
    print(f"Project name: {project.name}")
    print(f"Tasks: {[t.name for t in project.tasks]}")

    # Check task statuses
    for task in project.tasks:
        print(f"Task {task.name}:")
        print(f"  - Is completed: {task.is_completed}")
        print(f"  - Dependencies: {task.instruction.dependencies}")
        print(f"  - Inputs: {task.instruction.inputs}")

        # Check dependencies manually
        if task.instruction.dependencies:
            for dep_name in task.instruction.dependencies:
                dep_task = project.get_task(dep_name)
                if dep_task:
                    print(f"  - Dependency {dep_name} completed: {dep_task.is_completed}")
                else:
                    print(f"  - Dependency {dep_name} NOT FOUND")

        # Check file validation
        if task.instruction.inputs:
            errors = validate_file_references(task, workspace, check_inputs=True)
            print(f"  - File validation errors: {errors}")

    # Find ready tasks
    ready_tasks = find_ready_tasks(projects, workspace)
    print(f"Ready tasks: {[t.name for t in ready_tasks]}")
