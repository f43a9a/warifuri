"""Test task discovery and execution functionality."""

import pytest
from warifuri.core.discovery import (
    discover_task,
    discover_project,
    discover_all_projects,
    determine_task_type,
    find_ready_tasks,
)
from warifuri.core.execution import execute_task
from warifuri.core.types import TaskType
from warifuri.utils import safe_write_file


class TestTaskDiscovery:
    """Test task discovery functionality."""

    @pytest.fixture
    def project_with_tasks(self, temp_workspace):
        """Create a project with multiple tasks."""
        project_dir = temp_workspace / "projects" / "test-project"

        # Create machine task
        machine_task = project_dir / "extract"
        machine_task.mkdir(parents=True)
        safe_write_file(machine_task / "instruction.yaml", """
name: extract
task_type: machine
description: Extract data
auto_merge: false
dependencies: []
inputs: []
outputs: [data.json]
""")
        safe_write_file(machine_task / "run.sh", "#!/bin/bash\necho 'extracted' > data.json")
        (machine_task / "run.sh").chmod(0o755)

        # Create AI task depending on machine task
        ai_task = project_dir / "transform"
        ai_task.mkdir(parents=True)
        safe_write_file(ai_task / "instruction.yaml", """
name: transform
task_type: ai
description: Transform data
auto_merge: false
dependencies: [extract]
inputs: [../extract/data.json]
outputs: [transformed.json]
""")
        safe_write_file(ai_task / "prompt.yaml", "Transform the data from input to output")

        # Create human task
        human_task = project_dir / "review"
        human_task.mkdir(parents=True)
        safe_write_file(human_task / "instruction.yaml", """
name: review
task_type: human
description: Review results
auto_merge: false
dependencies: [transform]
inputs: [../transform/transformed.json]
outputs: []
""")

        return temp_workspace

    def test_determine_task_type_machine(self, temp_workspace):
        """Test task type detection for machine tasks."""
        task_path = temp_workspace / "task"
        task_path.mkdir()
        (task_path / "run.sh").touch()

        task_type = determine_task_type(task_path)
        assert task_type == TaskType.MACHINE

    def test_determine_task_type_ai(self, temp_workspace):
        """Test task type detection for AI tasks."""
        task_path = temp_workspace / "task"
        task_path.mkdir()
        (task_path / "prompt.yaml").touch()

        task_type = determine_task_type(task_path)
        assert task_type == TaskType.AI

    def test_determine_task_type_human(self, temp_workspace):
        """Test task type detection for human tasks."""
        task_path = temp_workspace / "task"
        task_path.mkdir()
        # No specific files = human task

        task_type = determine_task_type(task_path)
        assert task_type == TaskType.HUMAN

    def test_discover_task(self, project_with_tasks):
        """Test task discovery."""
        task = discover_task("test-project", project_with_tasks / "projects" / "test-project" / "extract")

        assert task.name == "extract"
        assert task.project == "test-project"
        assert task.task_type == TaskType.MACHINE
        assert task.instruction.description == "Extract data"
        assert not task.is_completed

    def test_discover_project(self, project_with_tasks):
        """Test project discovery."""
        project = discover_project(project_with_tasks, "test-project")

        assert project.name == "test-project"
        assert len(project.tasks) == 3

        task_names = [task.name for task in project.tasks]
        assert "extract" in task_names
        assert "transform" in task_names
        assert "review" in task_names

    def test_discover_all_projects(self, project_with_tasks):
        """Test discovering all projects."""
        projects = discover_all_projects(project_with_tasks)

        assert len(projects) == 1
        assert projects[0].name == "test-project"

    def test_find_ready_tasks(self, project_with_tasks):
        """Test finding ready tasks."""
        projects = discover_all_projects(project_with_tasks)
        ready_tasks = find_ready_tasks(projects)

        # Only extract should be ready (no dependencies)
        assert len(ready_tasks) == 1
        assert ready_tasks[0].name == "extract"


class TestTaskExecution:
    """Test task execution functionality."""

    @pytest.fixture
    def simple_machine_task(self, temp_workspace):
        """Create simple machine task."""
        task_dir = temp_workspace / "projects" / "test" / "simple"
        task_dir.mkdir(parents=True)

        safe_write_file(task_dir / "instruction.yaml", """
name: simple
task_type: machine
description: Simple test task
auto_merge: false
dependencies: []
inputs: []
outputs: [result.txt]
""")
        safe_write_file(task_dir / "run.sh", "#!/bin/bash\necho 'success' > result.txt")
        (task_dir / "run.sh").chmod(0o755)

        task = discover_task("test", task_dir)
        return task

    @pytest.fixture
    def simple_ai_task(self, temp_workspace):
        """Create simple AI task."""
        task_dir = temp_workspace / "projects" / "test" / "ai"
        task_dir.mkdir(parents=True)

        safe_write_file(task_dir / "instruction.yaml", """
name: ai
task_type: ai
description: Simple AI task
auto_merge: false
dependencies: []
inputs: []
outputs: [ai_result.txt]
""")
        safe_write_file(task_dir / "prompt.yaml", "Generate some text")

        task = discover_task("test", task_dir)
        return task

    def test_execute_machine_task_dry_run(self, simple_machine_task):
        """Test machine task execution in dry run mode."""
        result = execute_task(simple_machine_task, dry_run=True)
        assert result is True

        # Output file should not exist in dry run
        output_file = simple_machine_task.path / "result.txt"
        assert not output_file.exists()

    def test_execute_machine_task(self, simple_machine_task):
        """Test actual machine task execution."""
        result = execute_task(simple_machine_task, dry_run=False)
        assert result is True

        # Check if done.md was created
        done_file = simple_machine_task.path / "done.md"
        assert done_file.exists()

        # Check if output was created
        output_file = simple_machine_task.path / "result.txt"
        assert output_file.exists()
        assert output_file.read_text().strip() == "success"

    def test_execute_ai_task_dry_run(self, simple_ai_task):
        """Test AI task execution in dry run mode."""
        result = execute_task(simple_ai_task, dry_run=True)
        assert result is True

    def test_execute_human_task(self, temp_workspace):
        """Test human task execution."""
        task_dir = temp_workspace / "projects" / "test" / "human"
        task_dir.mkdir(parents=True)

        safe_write_file(task_dir / "instruction.yaml", """
name: human
task_type: human
description: Human task
auto_merge: false
dependencies: []
inputs: []
outputs: []
""")

        task = discover_task("test", task_dir)
        result = execute_task(task, dry_run=False)
        assert result is True


class TestDependencyResolution:
    """Test dependency resolution and validation."""

    def test_circular_dependency_detection(self, temp_workspace):
        """Test detection of circular dependencies."""
        project_dir = temp_workspace / "projects" / "circular"

        # Create task A depending on B
        task_a = project_dir / "task_a"
        task_a.mkdir(parents=True)
        safe_write_file(task_a / "instruction.yaml", """
name: task_a
task_type: human
description: Task A
auto_merge: false
dependencies: [task_b]
inputs: []
outputs: []
""")

        # Create task B depending on A (circular)
        task_b = project_dir / "task_b"
        task_b.mkdir(parents=True)
        safe_write_file(task_b / "instruction.yaml", """
name: task_b
task_type: human
description: Task B
auto_merge: false
dependencies: [task_a]
inputs: []
outputs: []
""")

        # This should be detected during project discovery
        from warifuri.utils.validation import CircularDependencyError

        # Should detect circular dependency during project discovery
        with pytest.raises(CircularDependencyError):
            discover_project(temp_workspace, "circular")
