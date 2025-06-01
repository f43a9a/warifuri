"""Corrected unit tests for discovery module with proper mocking strategies."""

import pytest
from pathlib import Path
from typing import List
from unittest.mock import Mock, patch

from warifuri.core.discovery import (
    determine_task_type,
    determine_task_status,
    load_task_instruction,
    discover_task,
    discover_project,
    discover_project_safe,
    discover_all_projects,
    discover_all_projects_safe,
    find_ready_tasks,
    find_task_by_name,
)
from warifuri.core.types import (
    Task,
    TaskInstruction,
    Project,
    TaskType,
    TaskStatus,
)


class TestDetermineTaskType:
    """Test determine_task_type function."""

    @patch('pathlib.Path.glob')
    def test_determine_task_type_machine_with_shell_script(self, mock_glob: Mock) -> None:
        """Test task type determination for machine task with shell script."""
        task_path = Path("/test/project/task")

        # Mock glob to return shell script for first call
        mock_glob.side_effect = [
            [Path("/test/project/task/script.sh")],  # *.sh pattern
        ]

        result = determine_task_type(task_path)
        assert result == TaskType.MACHINE

    @patch('pathlib.Path.glob')
    def test_determine_task_type_machine_with_python_script(self, mock_glob: Mock) -> None:
        """Test task type determination for machine task with Python script."""
        task_path = Path("/test/project/task")

        # Mock glob to return Python script for second call
        mock_glob.side_effect = [
            [],  # *.sh pattern
            [Path("/test/project/task/script.py")],  # *.py pattern
        ]

        result = determine_task_type(task_path)
        assert result == TaskType.MACHINE

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_determine_task_type_ai_with_prompt_yaml(self, mock_glob: Mock, mock_exists: Mock) -> None:
        """Test task type determination for AI task with prompt.yaml."""
        task_path = Path("/test/project/task")

        # Mock glob to return no scripts
        mock_glob.side_effect = [
            [],  # *.sh pattern
            [],  # *.py pattern
        ]

        # Mock prompt.yaml exists
        mock_exists.return_value = True

        result = determine_task_type(task_path)
        assert result == TaskType.AI

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_determine_task_type_human_default(self, mock_glob: Mock, mock_exists: Mock) -> None:
        """Test task type determination defaults to human."""
        task_path = Path("/test/project/task")

        # Mock glob to return no scripts
        mock_glob.side_effect = [
            [],  # *.sh pattern
            [],  # *.py pattern
        ]

        # Mock prompt.yaml doesn't exist
        mock_exists.return_value = False

        result = determine_task_type(task_path)
        assert result == TaskType.HUMAN


class TestDetermineTaskStatus:
    """Test determine_task_status function."""

    def test_determine_task_status_completed(self) -> None:
        """Test task status determination for completed task."""
        # Create a real Task object with is_completed=True
        mock_instruction = TaskInstruction(
            name="test-task",
            description="Test description",
            dependencies=[],
            inputs=[],
            outputs=[]
        )

        # Create task with a path that has done.md
        task_path = Path("/test/project/task")

        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = True  # done.md exists

            task = Task(
                project="test-project",
                name="test-task",
                path=task_path,
                instruction=mock_instruction,
                task_type=TaskType.MACHINE,
                status=TaskStatus.PENDING,
            )

            result = determine_task_status(task)
            assert result == TaskStatus.COMPLETED

    def test_determine_task_status_ready_when_not_completed(self) -> None:
        """Test task status determination for non-completed task."""
        mock_instruction = TaskInstruction(
            name="test-task",
            description="Test description",
            dependencies=[],
            inputs=[],
            outputs=[]
        )

        task_path = Path("/test/project/task")

        with patch('pathlib.Path.exists') as mock_exists:
            mock_exists.return_value = False  # done.md doesn't exist

            task = Task(
                project="test-project",
                name="test-task",
                path=task_path,
                instruction=mock_instruction,
                task_type=TaskType.MACHINE,
                status=TaskStatus.PENDING,
            )

            result = determine_task_status(task)
            assert result == TaskStatus.READY


class TestLoadTaskInstruction:
    """Test load_task_instruction function."""

    @patch('warifuri.core.discovery.load_yaml')
    def test_load_task_instruction_success(self, mock_load_yaml: Mock) -> None:
        """Test successful task instruction loading."""
        instruction_path = Path("/test/project/task/instruction.yaml")

        # Mock YAML content
        mock_yaml_data = {
            "name": "test-task",
            "description": "Test task description",
            "dependencies": ["dep1", "dep2"],
            "inputs": ["input1"],
            "outputs": ["output1"],
        }
        mock_load_yaml.return_value = mock_yaml_data

        result = load_task_instruction(instruction_path)

        assert result.name == "test-task"
        assert result.description == "Test task description"
        assert result.dependencies == ["dep1", "dep2"]
        assert result.inputs == ["input1"]
        assert result.outputs == ["output1"]

    @patch('warifuri.core.discovery.load_yaml')
    def test_load_task_instruction_minimal_data(self, mock_load_yaml: Mock) -> None:
        """Test task instruction loading with minimal data."""
        instruction_path = Path("/test/project/task/instruction.yaml")

        # Mock minimal YAML content
        mock_yaml_data = {
            "name": "minimal-task",
            "description": "Minimal description",
        }
        mock_load_yaml.return_value = mock_yaml_data

        result = load_task_instruction(instruction_path)

        assert result.name == "minimal-task"
        assert result.description == "Minimal description"
        assert result.dependencies == []
        assert result.inputs == []
        assert result.outputs == []


class TestDiscoverTask:
    """Test discover_task function."""

    @patch('warifuri.core.discovery.determine_task_status')
    @patch('warifuri.core.discovery.determine_task_type')
    @patch('warifuri.core.discovery.load_task_instruction')
    @patch('pathlib.Path.exists')
    def test_discover_task_success(
        self,
        mock_exists: Mock,
        mock_load_instruction: Mock,
        mock_determine_type: Mock,
        mock_determine_status: Mock,
    ) -> None:
        """Test successful task discovery."""
        project_name = "test-project"
        task_path = Path("/test/project/task")

        # Mock instruction file exists
        mock_exists.return_value = True

        # Mock instruction loading
        mock_instruction = TaskInstruction(
            name="instruction-task",
            description="Test description",
            dependencies=[],
            inputs=[],
            outputs=[],
        )
        mock_load_instruction.return_value = mock_instruction

        # Mock task type determination
        mock_determine_type.return_value = TaskType.MACHINE

        # Mock status determination
        mock_determine_status.return_value = TaskStatus.READY

        result = discover_task(project_name, task_path)

        assert result.project == project_name
        assert result.name == "task"  # Uses path.name
        assert result.path == task_path
        assert result.instruction == mock_instruction
        assert result.task_type == TaskType.MACHINE
        assert result.status == TaskStatus.READY

    @patch('pathlib.Path.exists')
    def test_discover_task_missing_instruction_file(self, mock_exists: Mock) -> None:
        """Test task discovery with missing instruction file."""
        project_name = "test-project"
        task_path = Path("/test/project/task")

        # Mock instruction file doesn't exist
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError, match="instruction.yaml not found"):
            discover_task(project_name, task_path)


class TestDiscoverProject:
    """Test discover_project function."""

    @patch('warifuri.utils.validation.detect_circular_dependencies')
    @patch('warifuri.core.discovery.discover_task')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    def test_discover_project_success(
        self,
        mock_exists: Mock,
        mock_iterdir: Mock,
        mock_discover_task: Mock,
        mock_detect_circular: Mock,
    ) -> None:
        """Test successful project discovery."""
        workspace_path = Path("/test/workspace")
        project_name = "test-project"

        # Mock project path exists
        mock_exists.return_value = True

        # Mock directory iteration
        mock_task_dirs = [
            Mock(spec=Path, name="task1", is_dir=Mock(return_value=True)),
            Mock(spec=Path, name="task2", is_dir=Mock(return_value=True)),
        ]
        mock_task_dirs[0].name = "task1"
        mock_task_dirs[1].name = "task2"
        mock_iterdir.return_value = mock_task_dirs

        # Mock task discovery
        mock_tasks = [
            Mock(spec=Task, name="task1"),
            Mock(spec=Task, name="task2"),
        ]
        mock_discover_task.side_effect = mock_tasks

        # Mock no circular dependencies
        mock_detect_circular.return_value = None

        result = discover_project(workspace_path, project_name)

        assert result.name == project_name
        assert len(result.tasks) == 2

    @patch('pathlib.Path.exists')
    def test_discover_project_not_found(self, mock_exists: Mock) -> None:
        """Test project discovery with non-existent project."""
        workspace_path = Path("/test/workspace")
        project_name = "non-existent"

        # Mock project path doesn't exist
        mock_exists.return_value = False

        with pytest.raises(FileNotFoundError, match="Project not found"):
            discover_project(workspace_path, project_name)

    @patch('warifuri.utils.validation.detect_circular_dependencies')
    @patch('warifuri.core.discovery.discover_task')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    def test_discover_project_with_task_discovery_error(
        self,
        mock_exists: Mock,
        mock_iterdir: Mock,
        mock_discover_task: Mock,
        mock_detect_circular: Mock,
    ) -> None:
        """Test project discovery with task discovery error."""
        workspace_path = Path("/test/workspace")
        project_name = "test-project"

        # Mock project path exists
        mock_exists.return_value = True

        # Mock directory iteration
        mock_task_dir = Mock(spec=Path, name="task1", is_dir=Mock(return_value=True))
        mock_task_dir.name = "task1"
        mock_iterdir.return_value = [mock_task_dir]

        # Mock task discovery failure (skipped, not raised)
        mock_discover_task.side_effect = FileNotFoundError("Task error")

        # Mock no circular dependencies
        mock_detect_circular.return_value = None

        # Should not raise error, just skip the task
        result = discover_project(workspace_path, project_name)
        assert len(result.tasks) == 0


class TestDiscoverProjectSafe:
    """Test discover_project_safe function."""

    @patch('warifuri.core.discovery.discover_task')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    def test_discover_project_safe_success(
        self,
        mock_exists: Mock,
        mock_iterdir: Mock,
        mock_discover_task: Mock,
    ) -> None:
        """Test safe project discovery success."""
        workspace_path = Path("/test/workspace")
        project_name = "test-project"

        # Mock project path exists
        mock_exists.return_value = True

        # Mock directory iteration
        mock_task_dir = Mock(spec=Path, name="task1", is_dir=Mock(return_value=True))
        mock_task_dir.name = "task1"
        mock_iterdir.return_value = [mock_task_dir]

        # Mock task discovery
        mock_task = Mock(spec=Task)
        mock_discover_task.return_value = mock_task

        result = discover_project_safe(workspace_path, project_name)

        assert result is not None
        assert result.name == project_name
        assert len(result.tasks) == 1

    @patch('pathlib.Path.exists')
    def test_discover_project_safe_with_exception(self, mock_exists: Mock) -> None:
        """Test safe project discovery with exception."""
        workspace_path = Path("/test/workspace")
        project_name = "non-existent"

        # Mock project path doesn't exist
        mock_exists.return_value = False

        result = discover_project_safe(workspace_path, project_name)
        assert result is None


class TestDiscoverAllProjects:
    """Test discover_all_projects function."""

    @patch('warifuri.core.discovery.discover_project')
    @patch('warifuri.core.discovery.list_projects')
    def test_discover_all_projects_success(
        self,
        mock_list_projects: Mock,
        mock_discover_project: Mock,
    ) -> None:
        """Test successful discovery of all projects."""
        workspace_path = Path("/test/workspace")

        # Mock project listing
        mock_list_projects.return_value = ["project1", "project2"]

        # Mock project discovery to succeed for both projects
        mock_projects = [
            Mock(spec=Project, name="project1"),
            Mock(spec=Project, name="project2"),
        ]
        mock_discover_project.side_effect = mock_projects

        result = discover_all_projects(workspace_path)

        assert len(result) == 2
        # Verify discover_project was called for each project
        assert mock_discover_project.call_count == 2

    @patch('warifuri.utils.filesystem.list_projects')
    def test_discover_all_projects_empty_workspace(self, mock_list_projects: Mock) -> None:
        """Test discovery with empty workspace."""
        workspace_path = Path("/test/workspace")

        # Mock empty project listing
        mock_list_projects.return_value = []

        result = discover_all_projects(workspace_path)
        assert len(result) == 0


class TestDiscoverAllProjectsSafe:
    """Test discover_all_projects_safe function."""

    @patch('warifuri.core.discovery.discover_project_safe')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    def test_discover_all_projects_safe_success(
        self,
        mock_exists: Mock,
        mock_iterdir: Mock,
        mock_discover_project_safe: Mock,
    ) -> None:
        """Test safe discovery of all projects with all successful."""
        workspace_path = Path("/test/workspace")

        # Mock projects directory exists
        mock_exists.return_value = True

        # Mock directory iteration
        mock_project_dirs = [
            Mock(spec=Path, name="project1", is_dir=Mock(return_value=True)),
            Mock(spec=Path, name="project2", is_dir=Mock(return_value=True)),
        ]
        mock_project_dirs[0].name = "project1"
        mock_project_dirs[1].name = "project2"
        mock_iterdir.return_value = mock_project_dirs

        # Mock successful project discovery
        mock_projects = [
            Mock(spec=Project, name="project1"),
            Mock(spec=Project, name="project2"),
        ]
        mock_discover_project_safe.side_effect = mock_projects

        result = discover_all_projects_safe(workspace_path)

        assert len(result) == 2

    @patch('warifuri.core.discovery.discover_project_safe')
    @patch('pathlib.Path.iterdir')
    @patch('pathlib.Path.exists')
    def test_discover_all_projects_safe_with_failures(
        self,
        mock_exists: Mock,
        mock_iterdir: Mock,
        mock_discover_project_safe: Mock,
    ) -> None:
        """Test safe discovery with some failures."""
        workspace_path = Path("/test/workspace")

        # Mock projects directory exists
        mock_exists.return_value = True

        # Mock directory iteration
        mock_project_dirs = [
            Mock(spec=Path, name="project1", is_dir=Mock(return_value=True)),
            Mock(spec=Path, name="project2", is_dir=Mock(return_value=True)),
            Mock(spec=Path, name="project3", is_dir=Mock(return_value=True)),
        ]
        mock_project_dirs[0].name = "project1"
        mock_project_dirs[1].name = "project2"
        mock_project_dirs[2].name = "project3"
        mock_iterdir.return_value = mock_project_dirs

        # Mock mixed results (one failure)
        mock_project1 = Mock(spec=Project, name="project1")
        mock_project3 = Mock(spec=Project, name="project3")
        mock_discover_project_safe.side_effect = [mock_project1, None, mock_project3]

        result = discover_all_projects_safe(workspace_path)

        # Should only return successful discoveries
        assert len(result) == 2


class TestFindReadyTasks:
    """Test find_ready_tasks function."""

    def create_mock_task(self, name: str, dependencies: List[str], completed: bool = False) -> Mock:
        """Create a mock task with proper attributes."""
        mock_task = Mock(spec=Task)
        mock_task.name = name
        mock_task.full_name = f"test-project/{name}"
        mock_task.is_completed = completed

        # Create mock instruction with dependencies
        mock_instruction = Mock(spec=TaskInstruction)
        mock_instruction.dependencies = dependencies
        mock_instruction.inputs = []
        mock_task.instruction = mock_instruction

        return mock_task

    def create_mock_project_with_tasks(self, project_name: str, task_specs: List[tuple]) -> Mock:
        """Create a mock project with specified tasks."""
        tasks = []
        for name, deps, completed in task_specs:
            task = self.create_mock_task(name, deps, completed)
            task.full_name = f"{project_name}/{name}"
            tasks.append(task)

        mock_project = Mock(spec=Project)
        mock_project.name = project_name
        mock_project.tasks = tasks

        # Create a proper mock path structure
        mock_path = Mock(spec=Path)
        mock_parent = Mock(spec=Path)
        mock_parent.parent = Path("/test/workspace")
        mock_path.parent = mock_parent
        mock_project.path = mock_path

        return mock_project

    @patch('warifuri.utils.validation.validate_file_references')
    def test_find_ready_tasks_no_dependencies(self, mock_validate_files: Mock) -> None:
        """Test finding ready tasks with no dependencies."""
        # Mock file validation to always pass
        mock_validate_files.return_value = []

        project = self.create_mock_project_with_tasks("test-project", [
            ("task1", [], False),
            ("task2", [], False),
        ])

        result = find_ready_tasks([project])

        # All tasks should be ready (no dependencies)
        assert len(result) == 2

    @patch('warifuri.utils.validation.validate_file_references')
    def test_find_ready_tasks_with_completed_dependencies(self, mock_validate_files: Mock) -> None:
        """Test finding ready tasks with completed dependencies."""
        # Mock file validation to always pass
        mock_validate_files.return_value = []

        project = self.create_mock_project_with_tasks("test-project", [
            ("task1", [], True),  # completed dependency
            ("task2", ["test-project/task1"], False),  # depends on completed task
        ])

        result = find_ready_tasks([project])

        # Only task2 should be ready (task1 is completed, task2 has completed deps)
        assert len(result) == 1
        assert result[0].name == "task2"

    @patch('warifuri.utils.validation.validate_file_references')
    def test_find_ready_tasks_with_incomplete_dependencies(self, mock_validate_files: Mock) -> None:
        """Test finding ready tasks with incomplete dependencies."""
        # Mock file validation to always pass
        mock_validate_files.return_value = []

        project = self.create_mock_project_with_tasks("test-project", [
            ("task1", [], False),  # incomplete dependency
            ("task2", ["test-project/task1"], False),  # depends on incomplete task
        ])

        result = find_ready_tasks([project])

        # Only task1 should be ready (no dependencies)
        assert len(result) == 1
        assert result[0].name == "task1"

    @patch('warifuri.utils.validation.validate_file_references')
    def test_find_ready_tasks_cross_project_dependencies(self, mock_validate_files: Mock) -> None:
        """Test finding ready tasks with cross-project dependencies."""
        # Mock file validation to always pass
        mock_validate_files.return_value = []

        project1 = self.create_mock_project_with_tasks("project1", [
            ("task1", [], True),  # completed task in project1
        ])

        project2 = self.create_mock_project_with_tasks("project2", [
            ("task2", ["project1/task1"], False),  # depends on task in project1
        ])

        result = find_ready_tasks([project1, project2])

        # task2 should be ready (depends on completed task1 from project1)
        ready_names = [task.name for task in result]
        assert "task2" in ready_names

    @patch('warifuri.utils.validation.validate_file_references')
    def test_find_ready_tasks_exclude_completed(self, mock_validate_files: Mock) -> None:
        """Test that completed tasks are excluded from ready tasks."""
        # Mock file validation to always pass
        mock_validate_files.return_value = []

        project = self.create_mock_project_with_tasks("test-project", [
            ("task1", [], True),  # completed task
            ("task2", [], False),  # incomplete task
        ])

        result = find_ready_tasks([project])

        # Only incomplete tasks should be returned
        assert len(result) == 1
        assert result[0].name == "task2"


class TestFindTaskByName:
    """Test find_task_by_name function."""

    def test_find_task_by_name_found(self) -> None:
        """Test finding task by name when it exists."""
        mock_task = Mock(spec=Task)
        mock_task.name = "target-task"

        mock_project = Mock(spec=Project)
        mock_project.name = "test-project"
        mock_project.get_task.return_value = mock_task

        result = find_task_by_name([mock_project], "test-project", "target-task")

        assert result == mock_task

    def test_find_task_by_name_not_found_wrong_project(self) -> None:
        """Test finding task when project doesn't exist."""
        mock_project = Mock(spec=Project)
        mock_project.name = "other-project"

        result = find_task_by_name([mock_project], "test-project", "target-task")

        assert result is None

    def test_find_task_by_name_not_found_wrong_task(self) -> None:
        """Test finding task when task doesn't exist."""
        mock_project = Mock(spec=Project)
        mock_project.name = "test-project"
        mock_project.get_task.return_value = None

        result = find_task_by_name([mock_project], "test-project", "target-task")

        assert result is None

    def test_find_task_by_name_empty_projects(self) -> None:
        """Test finding task with empty project list."""
        result = find_task_by_name([], "test-project", "target-task")

        assert result is None
