"""Test the original bug case."""

from pathlib import Path
from warifuri.core.discovery import discover_all_projects, find_ready_tasks
from warifuri.utils.validation import validate_file_references

# Test with the original bug workspace
workspace = Path("/workspace/warifuri-test/warifuri-test/workspace")

print(f"Workspace: {workspace}")
print(f"Foundation file exists: {(workspace / 'foundation_output.txt').exists()}")

# Discover projects
projects = discover_all_projects(workspace)
print(f"Found {len(projects)} projects")

if projects:
    project = projects[0]
    print(f"Project name: {project.name}")
    print(f"Tasks: {[t.name for t in project.tasks]}")

    # Find task B
    task_b = project.get_task("task-b-dependent")
    if task_b:
        print("\nTask B details:")
        print(f"  - Name: {task_b.name}")
        print(f"  - Dependencies: {task_b.instruction.dependencies}")
        print(f"  - Inputs: {task_b.instruction.inputs}")
        print(f"  - Is completed: {task_b.is_completed}")

        # Check file validation
        errors = validate_file_references(task_b, workspace, check_inputs=True)
        print(f"  - File validation errors: {errors}")

        # Check dependencies
        dep_task = project.get_task("task-a-foundation")
        if dep_task:
            print(f"  - Dependency task-a-foundation completed: {dep_task.is_completed}")

    # Find ready tasks
    ready_tasks = find_ready_tasks(projects, workspace)
    print(f"\nReady tasks: {[t.name for t in ready_tasks]}")

    if "task-b-dependent" in [t.name for t in ready_tasks]:
        print("✅ Bug fixed! Task B is now ready.")
    else:
        print("❌ Bug still exists! Task B is not ready.")
else:
    print("No projects found")
