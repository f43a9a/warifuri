"""Unit tests for automation service module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import click
import pytest

from warifuri.cli.context import Context
from warifuri.cli.services.automation_service import (
    AutomationCheckService,
    AutomationListService,
    TaskExecutionService,
)
from warifuri.core.types import Project, Task, TaskInstruction, TaskStatus, TaskType


class TestAutomationListService:
    """Test AutomationListService class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.workspace_path = Path("/test/workspace")
        self.ctx = Mock(spec=Context)
        self.ctx.workspace_path = self.workspace_path
        self.service = AutomationListService(self.ctx)

    def test_init_with_workspace_path(self) -> None:
        """Test successful initialization with workspace path."""
        assert self.service.ctx == self.ctx
        assert self.service.workspace_path == self.workspace_path

    def test_init_without_workspace_path_raises_error(self) -> None:
        """Test initialization fails without workspace path."""
        ctx = Mock(spec=Context)
        ctx.workspace_path = None

        with pytest.raises(click.ClickException, match="Workspace path is required"):
            AutomationListService(ctx)

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_tasks_no_projects(self, mock_discover: Mock) -> None:
        """Test list_tasks when no projects are found."""
        mock_discover.return_value = []

        with patch("click.echo") as mock_echo:
            self.service.list_tasks("table")
            mock_echo.assert_called_with("No projects found in workspace")

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_tasks_no_tasks(self, mock_discover: Mock) -> None:
        """Test list_tasks when projects exist but no tasks."""
        project = Project(name="test-project", path=Path("/test/project"), tasks=[])
        mock_discover.return_value = [project]

        with patch("click.echo") as mock_echo:
            self.service.list_tasks("table")
            mock_echo.assert_called_with("No tasks found in any project")

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    @patch("warifuri.cli.services.automation_service.find_ready_tasks")
    def test_list_tasks_table_format(self, mock_find_ready: Mock, mock_discover: Mock) -> None:
        """Test list_tasks with table format."""
        # Create mock task
        task_instruction = TaskInstruction(
            name="test-task", description="Test task", dependencies=[], inputs=[], outputs=[]
        )
        task = Task(
            project="test-project",
            name="test-task",
            path=Path("/test/workspace/project/test-task"),  # Path under workspace
            instruction=task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY,
        )

        project = Project(name="test-project", path=Path("/test/workspace/project"), tasks=[task])

        mock_discover.return_value = [project]
        mock_find_ready.return_value = [task]

        with patch.object(self.service, "_print_table") as mock_print_table:
            self.service.list_tasks("table")
            mock_print_table.assert_called_once()

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    @patch("warifuri.cli.services.automation_service.find_ready_tasks")
    def test_list_tasks_json_format(self, mock_find_ready: Mock, mock_discover: Mock) -> None:
        """Test list_tasks with JSON format."""
        # Create mock task
        task_instruction = TaskInstruction(
            name="test-task", description="Test task", dependencies=[], inputs=[], outputs=[]
        )
        task = Task(
            project="test-project",
            name="test-task",
            path=Path("/test/workspace/project/test-task"),  # Path under workspace
            instruction=task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY,
        )

        project = Project(name="test-project", path=Path("/test/workspace/project"), tasks=[task])

        mock_discover.return_value = [project]
        mock_find_ready.return_value = [task]

        with patch("click.echo") as mock_echo:
            self.service.list_tasks("json")

            # Verify JSON output was called
            assert mock_echo.called
            json_output = mock_echo.call_args[0][0]
            data = json.loads(json_output)
            assert len(data) == 1
            assert data[0]["project"] == "test-project"
            assert data[0]["task"] == "test-task"

    def test_print_table_with_tasks(self) -> None:
        """Test _print_table method with task data."""
        task_info = [
            {"project": "test-project", "task": "test-task", "status": "ready", "dependencies": 2}
        ]

        with patch("click.echo") as mock_echo:
            self.service._print_table(task_info)

            # Verify table headers and data were printed
            assert mock_echo.called
            calls = mock_echo.call_args_list
            assert len(calls) >= 3  # Header, separator, data row

    def test_print_table_empty(self) -> None:
        """Test _print_table with empty task list."""
        with patch("click.echo") as mock_echo:
            self.service._print_table([])
            # Should not print anything for empty list
            mock_echo.assert_not_called()

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_automation_tasks_basic(self, mock_discover: Mock) -> None:
        """Test list_automation_tasks method."""
        # Create mock task
        task_instruction = TaskInstruction(
            name="test-task", description="Test task", dependencies=[], inputs=[], outputs=[]
        )
        task = Task(
            project="test-project",
            name="test-task",
            path=Path("/test/workspace/project/task.yaml"),
            instruction=task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY,
        )
        # full_name is computed automatically from project and name

        project = Project(name="test-project", path=Path("/test/workspace/project"), tasks=[task])

        mock_discover.return_value = [project]

        result = self.service.list_automation_tasks(ready_only=False, machine_only=False)

        assert len(result) == 1
        assert result[0]["project"] == "test-project"
        assert result[0]["name"] == "test-task"
        assert result[0]["full_name"] == "test-project/test-task"

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_automation_tasks_ready_only(self, mock_discover: Mock) -> None:
        """Test list_automation_tasks with ready_only filter."""
        # Create mock tasks
        ready_task = Task(
            project="test-project",
            name="ready-task",
            path=Path("/test/path1"),
            instruction=TaskInstruction(
                name="ready-task", description="Ready task", dependencies=[], inputs=[], outputs=[]
            ),
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY,
        )

        pending_task = Task(
            project="test-project",
            name="pending-task",
            path=Path("/test/path2"),
            instruction=TaskInstruction(
                name="pending-task",
                description="Pending task",
                dependencies=["ready-task"],
                inputs=[],
                outputs=[],
            ),
            task_type=TaskType.MACHINE,
            status=TaskStatus.PENDING,
        )

        project = Project(
            name="test-project", path=Path("/test/project"), tasks=[ready_task, pending_task]
        )

        mock_discover.return_value = [project]

        result = self.service.list_automation_tasks(ready_only=True)

        assert len(result) == 1
        assert result[0]["name"] == "ready-task"

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_automation_tasks_machine_only(self, mock_discover: Mock) -> None:
        """Test list_automation_tasks with machine_only filter."""
        # Create mock tasks of different types
        machine_task = Task(
            project="test-project",
            name="machine-task",
            path=Path("/test/path1"),
            instruction=TaskInstruction(
                name="machine-task",
                description="Machine task",
                dependencies=[],
                inputs=[],
                outputs=[],
            ),
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY,
        )

        human_task = Task(
            project="test-project",
            name="human-task",
            path=Path("/test/path2"),
            instruction=TaskInstruction(
                name="human-task", description="Human task", dependencies=[], inputs=[], outputs=[]
            ),
            task_type=TaskType.HUMAN,
            status=TaskStatus.READY,
        )

        project = Project(
            name="test-project", path=Path("/test/project"), tasks=[machine_task, human_task]
        )

        mock_discover.return_value = [project]

        result = self.service.list_automation_tasks(machine_only=True)

        assert len(result) == 1
        assert result[0]["name"] == "machine-task"

    def test_output_results_json(self) -> None:
        """Test output_results with JSON format."""
        automation_tasks = [
            {"project": "test-project", "name": "test-task", "automation_ready": True}
        ]

        with patch("click.echo") as mock_echo:
            self.service.output_results(automation_tasks, "json")

            json_output = mock_echo.call_args[0][0]
            data = json.loads(json_output)
            assert data == automation_tasks

    def test_output_results_table_empty(self) -> None:
        """Test output_results with table format and empty tasks."""
        with patch("click.echo") as mock_echo:
            self.service.output_results([], "table")
            mock_echo.assert_called_with("No tasks found matching criteria.")

    def test_output_results_table_with_tasks(self) -> None:
        """Test output_results with table format and tasks."""
        automation_tasks = [
            {
                "full_name": "test-project/test-task",
                "task_type": "machine",
                "status": "ready",
                "automation_ready": True,
                "auto_merge_config": "/path/to/config.yaml",
            }
        ]

        with patch("click.echo") as mock_echo:
            self.service.output_results(automation_tasks, "table")

            # Verify table headers and content were printed
            assert mock_echo.called
            calls = mock_echo.call_args_list
            # Should print header, separator, and task details
            assert len(calls) >= 5

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_tasks_workspace_path_none_raises_error(self, mock_discover: Mock) -> None:
        """Test list_tasks when workspace_path is None."""
        # Create service with context that has None workspace_path after initialization
        self.service.workspace_path = None

        with pytest.raises(click.ClickException, match="Workspace path is required"):
            self.service.list_tasks("table")

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_automation_tasks_workspace_path_none_raises_error(
        self, mock_discover: Mock
    ) -> None:
        """Test list_automation_tasks when workspace_path is None."""
        # Create service with context that has None workspace_path after initialization
        self.service.workspace_path = None

        with pytest.raises(click.ClickException, match="Workspace path is required"):
            self.service.list_automation_tasks()

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_automation_tasks_with_project_filter(self, mock_discover: Mock) -> None:
        """Test list_automation_tasks with project filter."""
        # Create mock projects
        project1 = Mock(spec=Project)
        project1.name = "project1"
        project1.path = Path("/test/project1")
        project1.tasks = []

        project2 = Mock(spec=Project)
        project2.name = "project2"
        project2.path = Path("/test/project2")
        project2.tasks = []

        mock_discover.return_value = [project1, project2]

        # Test with project filter
        result = self.service.list_automation_tasks(project="project1")

        assert isinstance(result, list)
        # Verify mock_discover was called
        mock_discover.assert_called_once_with(self.workspace_path)

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_automation_tasks_auto_merge_config_task_level(self, mock_discover: Mock) -> None:
        """Test list_automation_tasks with auto_merge config at task level."""

        # Create mock task with proper path handling
        task = MagicMock(spec=Task)
        task.name = "test_task"
        task.task_type = TaskType.MACHINE
        task.status = TaskStatus.READY
        task.full_name = "project1/test_task"

        # Create mock path that returns True for task-level auto_merge.yaml
        mock_task_path = MagicMock()
        task.path = mock_task_path

        # Mock the / operator and exists() method
        mock_auto_merge_path = MagicMock()
        mock_auto_merge_path.exists.return_value = True
        mock_auto_merge_path.__str__ = MagicMock(return_value="/test/project/task1/auto_merge.yaml")

        # Configure the task path to return our mock auto_merge path
        mock_task_path.__truediv__ = MagicMock(return_value=mock_auto_merge_path)

        project = Mock(spec=Project)
        project.name = "project1"
        project.path = Path("/test/project")
        project.tasks = [task]

        mock_discover.return_value = [project]

        result = self.service.list_automation_tasks()

        assert len(result) == 1
        assert result[0]["auto_merge_config"] == "/test/project/task1/auto_merge.yaml"

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_automation_tasks_auto_merge_config_project_level(
        self, mock_discover: Mock
    ) -> None:
        """Test list_automation_tasks with auto_merge config at project level."""

        # Create mock task with proper path handling
        task = MagicMock(spec=Task)
        task.name = "test_task"
        task.task_type = TaskType.MACHINE
        task.status = TaskStatus.READY
        task.full_name = "project1/test_task"

        # Create mock path that returns False for task-level auto_merge configs
        mock_task_path = MagicMock()
        task.path = mock_task_path

        # Mock the / operator and exists() method for task paths (return False)
        mock_task_auto_merge_yaml = MagicMock()
        mock_task_auto_merge_yaml.exists.return_value = False
        mock_task_auto_merge_yml = MagicMock()
        mock_task_auto_merge_yml.exists.return_value = False

        # Configure task path to return appropriate mocks
        def task_path_truediv(filename):
            if filename == "auto_merge.yaml":
                return mock_task_auto_merge_yaml
            elif filename == "auto_merge.yml":
                return mock_task_auto_merge_yml
            return MagicMock()

        mock_task_path.__truediv__ = MagicMock(side_effect=task_path_truediv)

        # Create mock project with proper path handling
        project = MagicMock(spec=Project)
        project.name = "project1"
        project.tasks = [task]

        # Create mock project path that returns True for project-level auto_merge.yaml
        mock_project_path = MagicMock()
        project.path = mock_project_path

        mock_project_auto_merge_yaml = MagicMock()
        mock_project_auto_merge_yaml.exists.return_value = True
        mock_project_auto_merge_yaml.__str__ = MagicMock(
            return_value="/test/project/auto_merge.yaml"
        )
        mock_project_auto_merge_yml = MagicMock()
        mock_project_auto_merge_yml.exists.return_value = False

        # Configure project path to return appropriate mocks
        def project_path_truediv(filename):
            if filename == "auto_merge.yaml":
                return mock_project_auto_merge_yaml
            elif filename == "auto_merge.yml":
                return mock_project_auto_merge_yml
            return MagicMock()

        mock_project_path.__truediv__ = MagicMock(side_effect=project_path_truediv)

        mock_discover.return_value = [project]

        result = self.service.list_automation_tasks()

        assert len(result) == 1
        assert result[0]["auto_merge_config"] == "/test/project/auto_merge.yaml"

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_automation_tasks_no_auto_merge_config(self, mock_discover: Mock) -> None:
        """Test list_automation_tasks with no auto_merge config found."""
        # Create mock task
        task = Mock(spec=Task)
        task.name = "test_task"
        task.task_type = TaskType.MACHINE
        task.status = TaskStatus.READY
        task.path = Path("/test/project/task1")
        task.full_name = "project1/test_task"

        project = Mock(spec=Project)
        project.name = "project1"
        project.path = Path("/test/project")
        project.tasks = [task]

        # Mock the exists() method to return False for all paths
        with patch.object(Path, "exists", return_value=False):
            mock_discover.return_value = [project]

            result = self.service.list_automation_tasks()

            assert len(result) == 1
            assert result[0]["auto_merge_config"] is None


class TestAutomationCheckService:
    """Test AutomationCheckService class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.workspace_path = Path("/test/workspace")
        self.ctx = Mock(spec=Context)
        self.ctx.workspace_path = self.workspace_path
        self.service = AutomationCheckService(self.ctx)

    def test_init_with_workspace_path(self) -> None:
        """Test successful initialization with workspace path."""
        assert self.service.ctx == self.ctx
        assert self.service.workspace_path == self.workspace_path

    def test_init_without_workspace_path_raises_error(self) -> None:
        """Test initialization fails without workspace path."""
        ctx = Mock(spec=Context)
        ctx.workspace_path = None

        with pytest.raises(click.ClickException, match="Workspace path is required"):
            AutomationCheckService(ctx)

    def test_check_task_invalid_format(self) -> None:
        """Test check_task with invalid task name format."""
        with patch("click.echo") as mock_echo, pytest.raises(click.Abort):
            self.service.check_task("invalid-task-name", verbose=False)
            mock_echo.assert_called_with(
                "Error: Task name must be in format 'project/task'", err=True
            )

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_check_task_project_not_found(self, mock_discover: Mock) -> None:
        """Test check_task when project is not found."""
        mock_discover.return_value = []

        with patch("click.echo") as mock_echo, pytest.raises(click.Abort):
            self.service.check_task("nonexistent/task", verbose=False)
            mock_echo.assert_called_with("❌ Project 'nonexistent' not found", err=True)

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_check_task_task_not_found(self, mock_discover: Mock) -> None:
        """Test check_task when task is not found in project."""
        project = Project(name="test-project", path=Path("/test/project"), tasks=[])
        mock_discover.return_value = [project]

        with patch("click.echo") as mock_echo, pytest.raises(click.Abort):
            self.service.check_task("test-project/nonexistent", verbose=False)
            mock_echo.assert_called_with(
                "❌ Task 'nonexistent' not found in project 'test-project'", err=True
            )

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    @patch("warifuri.cli.services.automation_service.find_ready_tasks")
    def test_check_task_ready(self, mock_find_ready: Mock, mock_discover: Mock) -> None:
        """Test check_task for a ready task."""
        # Create mock task
        task_instruction = TaskInstruction(
            name="test-task", description="Test task", dependencies=[], inputs=[], outputs=[]
        )
        task = Task(
            project="test-project",
            name="test-task",
            path=Path("/test/path"),
            instruction=task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY,
        )

        project = Project(name="test-project", path=Path("/test/project"), tasks=[task])

        mock_discover.return_value = [project]
        mock_find_ready.return_value = [task]

        with patch("click.echo") as mock_echo:
            self.service.check_task("test-project/test-task", verbose=False)
            mock_echo.assert_called_with("✅ Task 'test-project/test-task' is ready for automation")

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    @patch("warifuri.cli.services.automation_service.find_ready_tasks")
    def test_check_task_not_ready(self, mock_find_ready: Mock, mock_discover: Mock) -> None:
        """Test check_task for a task that is not ready."""
        # Create mock task
        task_instruction = TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=["other-task"],
            inputs=[],
            outputs=[],
        )
        task = Task(
            project="test-project",
            name="test-task",
            path=Path("/test/path"),
            instruction=task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.PENDING,
        )

        project = Project(name="test-project", path=Path("/test/project"), tasks=[task])

        mock_discover.return_value = [project]
        mock_find_ready.return_value = []  # No ready tasks

        with patch("click.echo") as mock_echo:
            self.service.check_task("test-project/test-task", verbose=False)
            mock_echo.assert_called_with(
                "⏳ Task 'test-project/test-task' is not ready for automation"
            )

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    @patch("warifuri.cli.services.automation_service.find_ready_tasks")
    def test_check_task_verbose(self, mock_find_ready: Mock, mock_discover: Mock) -> None:
        """Test check_task with verbose output."""
        # Create mock task
        task_instruction = TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=["other-task"],
            inputs=[],
            outputs=[],
        )
        task = Task(
            project="test-project",
            name="test-task",
            path=Path("/test/path"),
            instruction=task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.PENDING,
        )

        project = Project(name="test-project", path=Path("/test/project"), tasks=[task])

        mock_discover.return_value = [project]
        mock_find_ready.return_value = []

        with patch.object(self.service, "_show_verbose_info") as mock_verbose:
            self.service.check_task("test-project/test-task", verbose=True)
            mock_verbose.assert_called_once()

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_check_task_automation_machine_ready(self, mock_discover: Mock) -> None:
        """Test check_task_automation for machine task that's ready."""
        task_instruction = TaskInstruction(
            name="test-task", description="Test task", dependencies=[], inputs=[], outputs=[]
        )
        task = Task(
            project="test-project",
            name="test-task",
            path=Path("/test/workspace/project/task"),
            instruction=task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY,
        )

        project = Project(name="test-project", path=Path("/test/workspace/project"), tasks=[task])

        mock_discover.return_value = [project]

        # Mock auto_merge config file existence
        with patch.object(Path, "exists", return_value=True):
            can_automate, issues, config = self.service.check_task_automation(
                "test-project/test-task"
            )

            assert can_automate is True
            assert len(issues) == 0
            assert config is not None

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_check_task_automation_human_task(self, mock_discover: Mock) -> None:
        """Test check_task_automation for human task."""
        task_instruction = TaskInstruction(
            name="test-task", description="Test task", dependencies=[], inputs=[], outputs=[]
        )
        task = Task(
            project="test-project",
            name="test-task",
            path=Path("/test/workspace/project/task"),
            instruction=task_instruction,
            task_type=TaskType.HUMAN,
            status=TaskStatus.READY,
        )

        project = Project(name="test-project", path=Path("/test/workspace/project"), tasks=[task])

        mock_discover.return_value = [project]

        can_automate, issues, config = self.service.check_task_automation("test-project/test-task")

        assert can_automate is False
        assert "Task type is 'human', expected 'machine'" in issues

    def test_output_check_results_json(self) -> None:
        """Test output_check_results with JSON format."""
        with patch("click.echo") as mock_echo:
            self.service.output_check_results(
                "test-project/test-task", True, [], "/path/to/config.yaml", check_only=True
            )

            json_output = mock_echo.call_args[0][0]
            data = json.loads(json_output)
            assert data["task"] == "test-project/test-task"
            assert data["can_automate"] is True

    def test_output_check_results_table(self) -> None:
        """Test output_check_results with table format."""
        with patch("click.echo") as mock_echo:
            self.service.output_check_results(
                "test-project/test-task",
                False,
                ["Task not ready", "No config found"],
                None,
                check_only=False,
            )

            # Should print multiple lines for table format
            assert mock_echo.call_count >= 3

    @patch("warifuri.cli.services.automation_service.find_ready_tasks")
    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_show_verbose_info_workspace_path_none(
        self, mock_discover: Mock, mock_find_ready: Mock
    ) -> None:
        """Test _show_verbose_info when workspace_path is None."""
        task = Mock(spec=Task)
        task.name = "test_task"
        task.project = "project1"
        task.path = Path("/test/project/task")

        instruction = Mock(spec=TaskInstruction)
        instruction.dependencies = []
        task.instruction = instruction

        # Set workspace_path to None
        self.service.workspace_path = None

        with pytest.raises(click.ClickException, match="Workspace path is required"):
            self.service._show_verbose_info(task, [], True)

    @patch("warifuri.cli.services.automation_service.find_ready_tasks")
    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_show_verbose_info_with_dependencies_workspace_path_none(
        self, mock_discover: Mock, mock_find_ready: Mock
    ) -> None:
        """Test _show_verbose_info with dependencies when workspace_path is None inside dependency loop."""
        task = Mock(spec=Task)
        task.name = "test_task"
        task.project = "project1"
        task.path = Path("/test/project/task")

        instruction = Mock(spec=TaskInstruction)
        instruction.dependencies = ["project1/dep_task"]
        task.instruction = instruction

        # Mock discover_all_projects to work initially but fail on second call
        call_count = 0

        def mock_discover_side_effect(workspace_path):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return [Mock()]  # Return some projects for first call
            else:
                # This should not happen due to guard clause, but let's test it anyway
                return [Mock()]

        mock_discover.side_effect = mock_discover_side_effect

        with patch("click.echo"):
            # Set workspace_path to None after the first guard passes
            original_workspace_path = self.service.workspace_path

            def mock_echo_side_effect(text):
                if "Dependencies" in text:
                    # Simulate workspace_path becoming None during execution
                    self.service.workspace_path = None

            with patch("click.echo", side_effect=mock_echo_side_effect):
                with pytest.raises(click.ClickException, match="Workspace path is required"):
                    self.service._show_verbose_info(task, [], True)

            # Restore workspace_path for other tests
            self.service.workspace_path = original_workspace_path

    @patch("warifuri.cli.services.automation_service.find_ready_tasks")
    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_show_verbose_info_dependency_not_found(
        self, mock_discover: Mock, mock_find_ready: Mock
    ) -> None:
        """Test _show_verbose_info with dependency not found."""
        task = Mock(spec=Task)
        task.name = "test_task"
        task.project = "project1"
        task.path = Path("/test/project/task")

        instruction = Mock(spec=TaskInstruction)
        instruction.dependencies = ["project1/nonexistent_task"]
        task.instruction = instruction

        mock_discover.return_value = [Mock()]
        mock_find_ready.return_value = []

        with patch("click.echo") as mock_echo:
            # all_tasks is empty, so dependency won't be found
            self.service._show_verbose_info(task, [], True)

            # Verify that the "not found" message was displayed
            calls = [call[0][0] for call in mock_echo.call_args_list]
            assert any("❓ project1/nonexistent_task (not found)" in call for call in calls)

    @patch("warifuri.cli.services.automation_service.find_ready_tasks")
    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_show_verbose_info_dependency_found_ready(
        self, mock_discover: Mock, mock_find_ready: Mock
    ) -> None:
        """Test _show_verbose_info with dependency found and ready."""
        task = Mock(spec=Task)
        task.name = "test_task"
        task.project = "project1"
        task.path = Path("/test/project/task")

        instruction = Mock(spec=TaskInstruction)
        instruction.dependencies = ["project1/dep_task"]
        task.instruction = instruction

        # Create dependency task
        dep_task = Mock(spec=Task)
        dep_task.name = "dep_task"
        dep_task.project = "project1"

        mock_discover.return_value = [Mock()]
        mock_find_ready.return_value = [dep_task]  # Dependency is ready

        with patch("click.echo") as mock_echo:
            self.service._show_verbose_info(task, [dep_task], True)

            # Verify that the ready status was displayed
            calls = [call[0][0] for call in mock_echo.call_args_list]
            assert any("✅ project1/dep_task" in call for call in calls)

    @patch("warifuri.cli.services.automation_service.find_ready_tasks")
    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_show_verbose_info_dependency_found_not_ready(
        self, mock_discover: Mock, mock_find_ready: Mock
    ) -> None:
        """Test _show_verbose_info with dependency found but not ready."""
        task = Mock(spec=Task)
        task.name = "test_task"
        task.project = "project1"
        task.path = Path("/test/project/task")

        instruction = Mock(spec=TaskInstruction)
        instruction.dependencies = ["project1/dep_task"]
        task.instruction = instruction

        # Create dependency task
        dep_task = Mock(spec=Task)
        dep_task.name = "dep_task"
        dep_task.project = "project1"

        mock_discover.return_value = [Mock()]
        mock_find_ready.return_value = []  # Dependency is not ready

        with patch("click.echo") as mock_echo:
            self.service._show_verbose_info(task, [dep_task], True)

            # Verify that the not ready status was displayed
            calls = [call[0][0] for call in mock_echo.call_args_list]
            assert any("❌ project1/dep_task" in call for call in calls)

    @patch("warifuri.cli.services.automation_service.find_ready_tasks")
    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_show_verbose_info_task_blocked_with_dependencies(
        self, mock_discover: Mock, mock_find_ready: Mock
    ) -> None:
        """Test _show_verbose_info with task blocked and having dependencies."""
        task = Mock(spec=Task)
        task.name = "test_task"
        task.project = "project1"
        task.path = Path("/test/project/task")

        instruction = Mock(spec=TaskInstruction)
        instruction.dependencies = ["project1/dep_task"]
        task.instruction = instruction

        mock_discover.return_value = [Mock()]
        mock_find_ready.return_value = []

        with patch("click.echo") as mock_echo:
            # Task is not ready (blocked)
            self.service._show_verbose_info(task, [], False)

            # Verify that the blocking message was displayed
            calls = [call[0][0] for call in mock_echo.call_args_list]
            assert any("⚠️  Task is blocked by unfinished dependencies" in call for call in calls)
            assert any(
                "Run 'warifuri graph' to see the full dependency tree" in call for call in calls
            )


class TestTaskExecutionService:
    """Test TaskExecutionService class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.workspace_path = Path("/test/workspace")
        self.ctx = Mock(spec=Context)
        self.ctx.workspace_path = self.workspace_path
        self.service = TaskExecutionService(self.ctx)

    def test_init_with_workspace_path(self) -> None:
        """Test successful initialization with workspace path."""
        assert self.service.ctx == self.ctx
        assert self.service.workspace_path == self.workspace_path

    def test_init_without_workspace_path_raises_error(self) -> None:
        """Test initialization fails without workspace path."""
        ctx = Mock(spec=Context)
        ctx.workspace_path = None

        with pytest.raises(click.ClickException, match="Workspace path is required"):
            TaskExecutionService(ctx)

    def test_execute_task_safely_invalid_format(self) -> None:
        """Test execute_task_safely with invalid task name format."""
        result = self.service.execute_task_safely("invalid-task-name")
        assert result is False

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_execute_task_safely_task_not_found(self, mock_discover: Mock) -> None:
        """Test execute_task_safely when task is not found."""
        mock_discover.return_value = []

        result = self.service.execute_task_safely("nonexistent/task")
        assert result is False

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    @patch("warifuri.cli.services.automation_service.execute_task")
    def test_execute_task_safely_success(self, mock_execute: Mock, mock_discover: Mock) -> None:
        """Test execute_task_safely with successful execution."""
        # Create mock task
        task_instruction = TaskInstruction(
            name="test-task", description="Test task", dependencies=[], inputs=[], outputs=[]
        )
        task = Task(
            project="test-project",
            name="test-task",
            path=Path("/test/path"),
            instruction=task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY,
        )

        project = Project(name="test-project", path=Path("/test/project"), tasks=[task])

        mock_discover.return_value = [project]
        mock_execute.return_value = True

        result = self.service.execute_task_safely("test-project/test-task")
        assert result is True

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    @patch("warifuri.cli.services.automation_service.execute_task")
    def test_execute_task_safely_execution_fails(
        self, mock_execute: Mock, mock_discover: Mock
    ) -> None:
        """Test execute_task_safely when execution raises exception."""
        # Create mock task
        task_instruction = TaskInstruction(
            name="test-task", description="Test task", dependencies=[], inputs=[], outputs=[]
        )
        task = Task(
            project="test-project",
            name="test-task",
            path=Path("/test/path"),
            instruction=task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY,
        )

        project = Project(name="test-project", path=Path("/test/project"), tasks=[task])

        mock_discover.return_value = [project]
        mock_execute.side_effect = Exception("Execution failed")

        result = self.service.execute_task_safely("test-project/test-task")
        assert result is False

    def test_merge_pr_not_implemented(self) -> None:
        """Test merge_pr method returns False as not implemented."""
        with patch("click.echo") as mock_echo:
            result = self.service.merge_pr("https://github.com/test/repo/pull/1", "squash")

            assert result is False
            assert mock_echo.call_count >= 2  # Should print two messages

    # TaskExecutionService also has list_automation_tasks and output_results
    # (duplicate methods from AutomationListService)
    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_automation_tasks_duplicate_method(self, mock_discover: Mock) -> None:
        """Test that TaskExecutionService also has list_automation_tasks method."""
        # Create mock task
        task_instruction = TaskInstruction(
            name="test-task", description="Test task", dependencies=[], inputs=[], outputs=[]
        )
        task = Task(
            project="test-project",
            name="test-task",
            path=Path("/test/workspace/project/task.yaml"),
            instruction=task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY,
        )
        # full_name is computed automatically from project and name

        project = Project(name="test-project", path=Path("/test/workspace/project"), tasks=[task])

        mock_discover.return_value = [project]

        result = self.service.list_automation_tasks()

        assert len(result) == 1
        assert result[0]["project"] == "test-project"
        assert result[0]["name"] == "test-task"

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_automation_tasks_duplicate_method_workspace_path_none(
        self, mock_discover: Mock
    ) -> None:
        """Test TaskExecutionService list_automation_tasks when workspace_path is None."""
        # Set workspace_path to None
        self.service.workspace_path = None

        with pytest.raises(click.ClickException, match="Workspace path is required"):
            self.service.list_automation_tasks()

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_list_automation_tasks_duplicate_method_with_filters(self, mock_discover: Mock) -> None:
        """Test TaskExecutionService list_automation_tasks with all filters."""
        # Create mock tasks
        ready_machine_task = Mock(spec=Task)
        ready_machine_task.name = "ready_machine"
        ready_machine_task.task_type = TaskType.MACHINE
        ready_machine_task.status = TaskStatus.READY
        ready_machine_task.path = Path("/test/project/task1")
        ready_machine_task.full_name = "project1/ready_machine"

        not_ready_task = Mock(spec=Task)
        not_ready_task.name = "not_ready"
        not_ready_task.task_type = TaskType.MACHINE
        not_ready_task.status = TaskStatus.PENDING
        not_ready_task.path = Path("/test/project/task2")
        not_ready_task.full_name = "project1/not_ready"

        human_task = Mock(spec=Task)
        human_task.name = "human_task"
        human_task.task_type = TaskType.HUMAN
        human_task.status = TaskStatus.READY
        human_task.path = Path("/test/project/task3")
        human_task.full_name = "project1/human_task"

        project = Mock(spec=Project)
        project.name = "project1"
        project.path = Path("/test/project")
        project.tasks = [ready_machine_task, not_ready_task, human_task]

        mock_discover.return_value = [project]

        # Mock Path.exists to return False for all auto_merge configs
        with patch.object(Path, "exists", return_value=False):
            # Test with ready_only=True, machine_only=True
            result = self.service.list_automation_tasks(ready_only=True, machine_only=True)

            # Should only return the ready machine task
            assert len(result) == 1
            assert result[0]["name"] == "ready_machine"
            assert result[0]["task_type"] == "machine"
            assert result[0]["status"] == "ready"

    def test_output_results_empty_table_format(self) -> None:
        """Test output_results with empty list in table format."""
        with patch("click.echo") as mock_echo:
            self.service.output_results([], "table")
            mock_echo.assert_called_with("No tasks found matching criteria.")

    def test_output_results_with_tasks_table_format(self) -> None:
        """Test output_results with tasks in table format."""
        tasks = [
            {
                "full_name": "project1/task1",
                "task_type": "machine",
                "status": "ready",
                "automation_ready": True,
                "auto_merge_config": "/path/to/config.yaml",
            },
            {
                "full_name": "project1/task2",
                "task_type": "human",
                "status": "pending",
                "automation_ready": False,
                "auto_merge_config": None,
            },
        ]

        with patch("click.echo") as mock_echo:
            self.service.output_results(tasks, "table")

            # Verify various output components were called
            call_args_list = mock_echo.call_args_list
            calls = []
            for call_args in call_args_list:
                if call_args.args:  # Check if there are positional arguments
                    calls.append(call_args.args[0])

            assert any("Automation-Ready Tasks:" in call for call in calls)
            assert any("🤖 project1/task1" in call for call in calls)
            assert any("⏸️ project1/task2" in call for call in calls)
            assert any("Type: machine" in call for call in calls)
            assert any("Type: human" in call for call in calls)
            assert any("Config: /path/to/config.yaml" in call for call in calls)

    def test_output_results_json_format(self) -> None:
        """Test output_results with JSON format."""
        tasks = [{"full_name": "project1/task1", "task_type": "machine", "status": "ready"}]

        with patch("click.echo") as mock_echo:
            self.service.output_results(tasks, "json")

            # Verify JSON output
            expected_json = json.dumps(tasks, indent=2)
            mock_echo.assert_called_once_with(expected_json)

    def test_merge_pr_not_implemented_returns_false(self) -> None:
        """Test merge_pr method returns False (not implemented)."""
        result = self.service.merge_pr("https://github.com/owner/repo/pull/123", "merge")
        assert result is False
