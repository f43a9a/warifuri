"""Test dependency resolution with file inputs."""

import pytest
from warifuri.core.discovery import discover_all_projects, find_ready_tasks
from warifuri.core.types import TaskStatus
from warifuri.utils import safe_write_file


class TestDependencyFileResolution:
    """Test dependency resolution with file inputs."""

    @pytest.fixture
    def workspace_with_file_dependencies(self, temp_workspace):
        """Create workspace with file dependency scenario."""
        projects_dir = temp_workspace / "projects"
        project_dir = projects_dir / "test-dependency-bug"

        # Create task A (foundation) - creates output file
        task_a = project_dir / "task-a-foundation"
        task_a.mkdir(parents=True)
        safe_write_file(task_a / "instruction.yaml", """
name: task-a-foundation
task_type: human
description: "Foundation Task A - Creates foundation files with no external dependencies"
dependencies: []
inputs: []
outputs:
  - "foundation_output.txt"
""")

        # Create task B (dependent) - requires output from task A
        task_b = project_dir / "task-b-dependent"
        task_b.mkdir(parents=True)
        safe_write_file(task_b / "instruction.yaml", """
name: task-b-dependent
task_type: human
description: "Dependent Task B - Requires foundation_output.txt from Task A"
dependencies: ["task-a-foundation"]
inputs:
  - "foundation_output.txt"
outputs:
  - "dependent_output.txt"
""")

        # Mark task A as completed
        safe_write_file(task_a / "done.md", "Task A completed")

        return temp_workspace

    def test_ready_task_without_input_file(self, workspace_with_file_dependencies):
        """Test that task with missing input file is not ready."""
        workspace = workspace_with_file_dependencies
        projects = discover_all_projects(workspace)

        # Find ready tasks - task B should NOT be ready yet (missing input file)
        ready_tasks = find_ready_tasks(projects, workspace)

        task_names = [task.name for task in ready_tasks]
        assert "task-b-dependent" not in task_names

        # Verify task B is in PENDING state
        project = projects[0]
        task_b = project.get_task("task-b-dependent")
        assert task_b is not None
        assert task_b.status == TaskStatus.PENDING

    def test_ready_task_with_input_file(self, workspace_with_file_dependencies):
        """Test that task becomes ready when input file exists."""
        workspace = workspace_with_file_dependencies

        # Create the required input file in workspace root
        foundation_output = workspace / "foundation_output.txt"
        safe_write_file(foundation_output, "Foundation task completed")

        projects = discover_all_projects(workspace)

        # Find ready tasks - task B should now be ready
        ready_tasks = find_ready_tasks(projects, workspace)

        task_names = [task.name for task in ready_tasks]
        assert "task-b-dependent" in task_names

        # Verify task B is in READY state
        project = projects[0]
        task_b = project.get_task("task-b-dependent")
        assert task_b is not None
        assert task_b.status == TaskStatus.READY

    def test_multiple_input_files(self, temp_workspace):
        """Test task with multiple input files."""
        projects_dir = temp_workspace / "projects"
        project_dir = projects_dir / "multi-input-test"

        # Create task with multiple inputs
        task_dir = project_dir / "multi-input-task"
        task_dir.mkdir(parents=True)
        safe_write_file(task_dir / "instruction.yaml", """
name: multi-input-task
task_type: human
description: "Task requiring multiple input files"
dependencies: []
inputs:
  - "input1.txt"
  - "input2.txt"
  - "data/input3.json"
outputs:
  - "output.txt"
""")

        projects = discover_all_projects(temp_workspace)

        # Without any input files - should not be ready
        ready_tasks = find_ready_tasks(projects, temp_workspace)
        assert len([t for t in ready_tasks if t.name == "multi-input-task"]) == 0

        # Create partial input files - should still not be ready
        safe_write_file(temp_workspace / "input1.txt", "content1")
        ready_tasks = find_ready_tasks(projects, temp_workspace)
        assert len([t for t in ready_tasks if t.name == "multi-input-task"]) == 0

        # Create all input files - should now be ready
        safe_write_file(temp_workspace / "input2.txt", "content2")
        (temp_workspace / "data").mkdir(exist_ok=True)
        safe_write_file(temp_workspace / "data" / "input3.json", '{"key": "value"}')

        ready_tasks = find_ready_tasks(projects, temp_workspace)
        assert len([t for t in ready_tasks if t.name == "multi-input-task"]) == 1

    def test_input_files_in_subdirectories(self, temp_workspace):
        """Test input files located in subdirectories."""
        projects_dir = temp_workspace / "projects"
        project_dir = projects_dir / "subdir-test"

        # Create task requiring file in subdirectory
        task_dir = project_dir / "subdir-task"
        task_dir.mkdir(parents=True)
        safe_write_file(task_dir / "instruction.yaml", """
name: subdir-task
task_type: human
description: "Task requiring file in subdirectory"
dependencies: []
inputs:
  - "data/processed/result.txt"
outputs:
  - "final.txt"
""")

        projects = discover_all_projects(temp_workspace)

        # Without input file - should not be ready
        ready_tasks = find_ready_tasks(projects, temp_workspace)
        assert len([t for t in ready_tasks if t.name == "subdir-task"]) == 0

        # Create input file in correct subdirectory
        subdir = temp_workspace / "data" / "processed"
        subdir.mkdir(parents=True)
        safe_write_file(subdir / "result.txt", "processed data")

        ready_tasks = find_ready_tasks(projects, temp_workspace)
        assert len([t for t in ready_tasks if t.name == "subdir-task"]) == 1
