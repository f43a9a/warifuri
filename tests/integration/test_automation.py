"""Tests for automation command."""

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from warifuri.cli.commands.automation import automation_list, check_automation
from warifuri.cli.context import Context
from warifuri.core.types import Project, Task, TaskInstruction, TaskStatus, TaskType


class TestAutomationListCommand:
    """Test automation list command."""

    def setup_method(self) -> None:
        """Set up test data."""
        # Create mock task instruction
        self.mock_instruction = Mock(spec=TaskInstruction)
        self.mock_instruction.description = "Test task description"
        self.mock_instruction.dependencies = ["dep1", "dep2"]

        # Create mock task
        self.mock_task = Mock(spec=Task)
        self.mock_task.name = "test-task"
        self.mock_task.full_name = "test-project/test-task"
        self.mock_task.instruction = self.mock_instruction
        self.mock_task.status = TaskStatus.READY
        self.mock_task.task_type = TaskType.MACHINE
        self.mock_task.path = Path("/test/path")

        # Create mock project
        self.mock_project = Mock(spec=Project)
        self.mock_project.name = "test-project"
        self.mock_project.tasks = [self.mock_task]
        self.mock_project.path = Path("/test/project/path")

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_automation_list_no_tasks(self, mock_discover: Mock, tmp_path: Path) -> None:
        """Test automation list with no tasks."""
        mock_discover.return_value = []

        runner = CliRunner()
        result = runner.invoke(
            automation_list,
            [],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 0
        assert "No tasks found matching criteria." in result.output

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_automation_list_with_tasks(self, mock_discover: Mock, tmp_path: Path) -> None:
        """Test automation list with tasks."""
        mock_discover.return_value = [self.mock_project]

        # Mock auto_merge config file existence
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True

            runner = CliRunner()
            result = runner.invoke(
                automation_list,
                [],
                obj=Context(workspace_path=tmp_path)
            )

            assert result.exit_code == 0
            assert "Automation-Ready Tasks:" in result.output
            assert "test-project/test-task" in result.output
            assert "Type: machine" in result.output
            assert "Status: ready" in result.output

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_automation_list_ready_only_filter(self, mock_discover: Mock, tmp_path: Path) -> None:
        """Test automation list with ready-only filter."""
        # Create a non-ready task
        non_ready_task = Mock(spec=Task)
        non_ready_task.name = "non-ready-task"
        non_ready_task.full_name = "test-project/non-ready-task"
        non_ready_task.status = TaskStatus.PENDING
        non_ready_task.task_type = TaskType.MACHINE
        non_ready_task.path = Path("/test/path2")

        project_with_mixed_tasks = Mock(spec=Project)
        project_with_mixed_tasks.name = "test-project"
        project_with_mixed_tasks.tasks = [self.mock_task, non_ready_task]
        project_with_mixed_tasks.path = Path("/test/project/path")

        mock_discover.return_value = [project_with_mixed_tasks]

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False

            runner = CliRunner()
            result = runner.invoke(
                automation_list,
                ["--ready-only"],
                obj=Context(workspace_path=tmp_path)
            )

            assert result.exit_code == 0
            assert "test-project/test-task" in result.output
            assert "test-project/non-ready-task" not in result.output

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_automation_list_machine_only_filter(self, mock_discover: Mock, tmp_path: Path) -> None:
        """Test automation list with machine-only filter."""
        # Create a human task
        human_task = Mock(spec=Task)
        human_task.name = "human-task"
        human_task.full_name = "test-project/human-task"
        human_task.status = TaskStatus.READY
        human_task.task_type = TaskType.HUMAN
        human_task.path = Path("/test/path2")

        project_with_mixed_tasks = Mock(spec=Project)
        project_with_mixed_tasks.name = "test-project"
        project_with_mixed_tasks.tasks = [self.mock_task, human_task]
        project_with_mixed_tasks.path = Path("/test/project/path")

        mock_discover.return_value = [project_with_mixed_tasks]

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False

            runner = CliRunner()
            result = runner.invoke(
                automation_list,
                ["--machine-only"],
                obj=Context(workspace_path=tmp_path)
            )

            assert result.exit_code == 0
            assert "test-project/test-task" in result.output
            assert "test-project/human-task" not in result.output

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_automation_list_project_filter(self, mock_discover: Mock, tmp_path: Path) -> None:
        """Test automation list with project filter."""
        # Create another project
        other_project = Mock(spec=Project)
        other_project.name = "other-project"
        other_project.tasks = []

        mock_discover.return_value = [self.mock_project, other_project]

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False

            runner = CliRunner()
            result = runner.invoke(
                automation_list,
                ["--project", "test-project"],
                obj=Context(workspace_path=tmp_path)
            )

            assert result.exit_code == 0
            assert "test-project/test-task" in result.output

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_automation_list_json_format(self, mock_discover: Mock, tmp_path: Path) -> None:
        """Test automation list with JSON format."""
        mock_discover.return_value = [self.mock_project]

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True

            runner = CliRunner()
            result = runner.invoke(
                automation_list,
                ["--format", "json"],
                obj=Context(workspace_path=tmp_path)
            )

            assert result.exit_code == 0
            # Should output valid JSON
            import json
            output_data = json.loads(result.output)
            assert len(output_data) == 1
            assert output_data[0]["project"] == "test-project"
            assert output_data[0]["name"] == "test-task"

    def test_automation_list_no_workspace_path(self) -> None:
        """Test when workspace path is None."""
        runner = CliRunner()

        result = runner.invoke(
            automation_list,
            [],
            obj=Context(workspace_path=None)
        )

        # Should fail due to assertion
        assert result.exit_code != 0


class TestCheckAutomationCommand:
    """Test check automation command."""

    def setup_method(self) -> None:
        """Set up test data."""
        # Create mock task instruction
        self.mock_instruction = Mock(spec=TaskInstruction)
        self.mock_instruction.description = "Test task description"
        self.mock_instruction.dependencies = ["dep1", "dep2"]

        # Create mock task
        self.mock_task = Mock(spec=Task)
        self.mock_task.name = "test-task"
        self.mock_task.full_name = "test-project/test-task"
        self.mock_task.instruction = self.mock_instruction
        self.mock_task.status = TaskStatus.READY
        self.mock_task.task_type = TaskType.MACHINE
        self.mock_task.path = Path("/test/path")

        # Create mock project
        self.mock_project = Mock(spec=Project)
        self.mock_project.name = "test-project"
        self.mock_project.tasks = [self.mock_task]
        self.mock_project.path = Path("/test/project/path")

    def test_check_automation_invalid_task_name(self, tmp_path: Path) -> None:
        """Test check automation with invalid task name format."""
        runner = CliRunner()
        result = runner.invoke(
            check_automation,
            ["invalid-task-name"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 1  # click.Abort() exits with code 1
        assert "Error: Task name must be in format 'project/task'" in result.output

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_check_automation_task_not_found(self, mock_discover: Mock, tmp_path: Path) -> None:
        """Test check automation when task is not found."""
        mock_discover.return_value = [self.mock_project]

        runner = CliRunner()
        result = runner.invoke(
            check_automation,
            ["test-project/nonexistent-task"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 1
        assert "Error: Task 'test-project/nonexistent-task' not found" in result.output

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_check_automation_project_not_found(self, mock_discover: Mock, tmp_path: Path) -> None:
        """Test check automation when project is not found."""
        mock_discover.return_value = [self.mock_project]

        runner = CliRunner()
        result = runner.invoke(
            check_automation,
            ["nonexistent-project/test-task"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 1
        assert "Error: Task 'nonexistent-project/test-task' not found" in result.output

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_check_automation_success(self, mock_discover: Mock, tmp_path: Path) -> None:
        """Test successful automation check."""
        mock_discover.return_value = [self.mock_project]

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True

            runner = CliRunner()
            result = runner.invoke(
                check_automation,
                ["test-project/test-task"],
                obj=Context(workspace_path=tmp_path)
            )

            assert result.exit_code == 0
            assert "Task: test-project/test-task" in result.output
            assert "Can automate: ✅ Yes" in result.output

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_check_automation_not_machine_task(self, mock_discover: Mock, tmp_path: Path) -> None:
        """Test automation check with non-machine task."""
        # Create human task
        human_task = Mock(spec=Task)
        human_task.name = "test-task"
        human_task.task_type = TaskType.HUMAN
        human_task.status = TaskStatus.READY
        human_task.path = Path("/test/path")

        human_project = Mock(spec=Project)
        human_project.name = "test-project"
        human_project.tasks = [human_task]
        human_project.path = Path("/test/project/path")

        mock_discover.return_value = [human_project]

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True

            runner = CliRunner()
            result = runner.invoke(
                check_automation,
                ["test-project/test-task"],
                obj=Context(workspace_path=tmp_path)
            )

            assert result.exit_code == 1
            assert "Can automate: ❌ No" in result.output
            assert "Task type is 'human', expected 'machine'" in result.output

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_check_automation_not_ready(self, mock_discover: Mock, tmp_path: Path) -> None:
        """Test automation check with non-ready task."""
        # Create non-ready task
        todo_task = Mock(spec=Task)
        todo_task.name = "test-task"
        todo_task.task_type = TaskType.MACHINE
        todo_task.status = TaskStatus.PENDING
        todo_task.path = Path("/test/path")

        todo_project = Mock(spec=Project)
        todo_project.name = "test-project"
        todo_project.tasks = [todo_task]
        todo_project.path = Path("/test/project/path")

        mock_discover.return_value = [todo_project]

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True

            runner = CliRunner()
            result = runner.invoke(
                check_automation,
                ["test-project/test-task"],
                obj=Context(workspace_path=tmp_path)
            )
        assert result.exit_code == 1
        assert "Can automate: ❌ No" in result.output
        assert "Task status is 'pending', expected 'ready'" in result.output

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_check_automation_no_config(self, mock_discover: Mock, tmp_path: Path) -> None:
        """Test automation check without auto_merge config."""
        mock_discover.return_value = [self.mock_project]

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = False

            runner = CliRunner()
            result = runner.invoke(
                check_automation,
                ["test-project/test-task"],
                obj=Context(workspace_path=tmp_path)
            )

            assert result.exit_code == 1
            assert "Can automate: ❌ No" in result.output
            assert "No auto_merge.yaml configuration found" in result.output

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_check_automation_check_only_mode(self, mock_discover: Mock, tmp_path: Path) -> None:
        """Test automation check in check-only mode (JSON output)."""
        mock_discover.return_value = [self.mock_project]

        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True

            runner = CliRunner()
            result = runner.invoke(
                check_automation,
                ["test-project/test-task", "--check-only"],
                obj=Context(workspace_path=tmp_path)
            )

            assert result.exit_code == 0
            # Should output valid JSON
            import json
            output_data = json.loads(result.output)
            assert output_data["task"] == "test-project/test-task"
            assert output_data["can_automate"] is True
            assert output_data["issues"] == []

    def test_check_automation_no_workspace_path(self) -> None:
        """Test when workspace path is None."""
        runner = CliRunner()

        result = runner.invoke(
            check_automation,
            ["test-project/test-task"],
            obj=Context(workspace_path=None)
        )

        # Should fail due to assertion
        assert result.exit_code != 0
