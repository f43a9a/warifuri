"""Tests for issue command."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from warifuri.cli.commands.issue import issue
from warifuri.cli.context import Context
from warifuri.core.types import Project, Task, TaskInstruction, TaskStatus, TaskType


class TestIssueCommand:
    """Test issue command."""

    def setup_method(self) -> None:
        """Set up test data."""
        # Create mock task
        self.mock_instruction = Mock(spec=TaskInstruction)
        self.mock_instruction.description = "Test task description"
        self.mock_instruction.dependencies = ["dep1", "dep2"]

        self.mock_task = Mock(spec=Task)
        self.mock_task.name = "test-task"
        self.mock_task.full_name = "test-project/test-task"
        self.mock_task.instruction = self.mock_instruction
        self.mock_task.status = TaskStatus.READY
        self.mock_task.task_type = TaskType.HUMAN

        # Create mock project
        self.mock_project = Mock(spec=Project)
        self.mock_project.name = "test-project"
        self.mock_project.tasks = [self.mock_task]

    @patch("warifuri.cli.commands.issue.check_github_cli")
    def test_issue_github_cli_not_available(self, mock_check: Mock, tmp_path: Path) -> None:
        """Test when GitHub CLI is not available."""
        mock_check.return_value = False

        runner = CliRunner()
        result = runner.invoke(
            issue,
            ["--project", "test-project"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 0
        assert "Error: GitHub CLI (gh) is not installed or not authenticated." in result.output
        assert "Please install GitHub CLI: https://cli.github.com/" in result.output

    @patch("warifuri.cli.commands.issue.check_github_cli")
    @patch("warifuri.cli.commands.issue.get_github_repo")
    def test_issue_no_github_repo(self, mock_get_repo: Mock, mock_check: Mock, tmp_path: Path) -> None:
        """Test when GitHub repository cannot be detected."""
        mock_check.return_value = True
        mock_get_repo.return_value = None

        runner = CliRunner()
        result = runner.invoke(
            issue,
            ["--project", "test-project"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 0
        assert "Error: Could not detect GitHub repository." in result.output
        assert "Make sure you're in a Git repository with a GitHub remote." in result.output

    @patch("warifuri.cli.commands.issue.check_github_cli")
    @patch("warifuri.cli.commands.issue.get_github_repo")
    def test_issue_no_options_specified(self, mock_get_repo: Mock, mock_check: Mock, tmp_path: Path) -> None:
        """Test when no options are specified."""
        mock_check.return_value = True
        mock_get_repo.return_value = "user/repo"

        runner = CliRunner()
        result = runner.invoke(
            issue,
            [],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 0
        assert "Error: Specify exactly one of --project, --task, or --all-tasks." in result.output

    @patch("warifuri.cli.commands.issue.check_github_cli")
    @patch("warifuri.cli.commands.issue.get_github_repo")
    def test_issue_multiple_options_specified(self, mock_get_repo: Mock, mock_check: Mock, tmp_path: Path) -> None:
        """Test when multiple options are specified."""
        mock_check.return_value = True
        mock_get_repo.return_value = "user/repo"

        runner = CliRunner()
        result = runner.invoke(
            issue,
            ["--project", "test-project", "--task", "test-project/test-task"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 0
        assert "Error: Specify exactly one of --project, --task, or --all-tasks." in result.output

    @patch("warifuri.cli.commands.issue.check_github_cli")
    @patch("warifuri.cli.commands.issue.get_github_repo")
    @patch("warifuri.cli.commands.issue.discover_all_projects")
    @patch("warifuri.cli.commands.issue._create_project_issue")
    def test_issue_create_project_issue(self, mock_create: Mock, mock_discover: Mock,
                                       mock_get_repo: Mock, mock_check: Mock, tmp_path: Path) -> None:
        """Test creating project issue."""
        mock_check.return_value = True
        mock_get_repo.return_value = "user/repo"
        mock_discover.return_value = [self.mock_project]

        runner = CliRunner()
        result = runner.invoke(
            issue,
            ["--project", "test-project", "--assignee", "testuser", "--label", "bug,enhancement"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 0
        mock_create.assert_called_once_with(
            [self.mock_project],
            "test-project",
            "testuser",
            ["bug", "enhancement"],
            "user/repo",
            False
        )

    @patch("warifuri.cli.commands.issue.check_github_cli")
    @patch("warifuri.cli.commands.issue.get_github_repo")
    @patch("warifuri.cli.commands.issue.discover_all_projects")
    @patch("warifuri.cli.commands.issue._create_task_issue")
    def test_issue_create_task_issue(self, mock_create: Mock, mock_discover: Mock,
                                    mock_get_repo: Mock, mock_check: Mock, tmp_path: Path) -> None:
        """Test creating task issue."""
        mock_check.return_value = True
        mock_get_repo.return_value = "user/repo"
        mock_discover.return_value = [self.mock_project]

        runner = CliRunner()
        result = runner.invoke(
            issue,
            ["--task", "test-project/test-task"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 0
        mock_create.assert_called_once_with(
            [self.mock_project],
            "test-project/test-task",
            None,
            [],
            "user/repo",
            False
        )

    @patch("warifuri.cli.commands.issue.check_github_cli")
    @patch("warifuri.cli.commands.issue.get_github_repo")
    @patch("warifuri.cli.commands.issue.discover_all_projects")
    @patch("warifuri.cli.commands.issue._create_all_tasks_issues")
    def test_issue_create_all_tasks_issues(self, mock_create: Mock, mock_discover: Mock,
                                          mock_get_repo: Mock, mock_check: Mock, tmp_path: Path) -> None:
        """Test creating all tasks issues."""
        mock_check.return_value = True
        mock_get_repo.return_value = "user/repo"
        mock_discover.return_value = [self.mock_project]

        runner = CliRunner()
        result = runner.invoke(
            issue,
            ["--all-tasks", "test-project"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 0
        mock_create.assert_called_once_with(
            [self.mock_project],
            "test-project",
            None,
            [],
            "user/repo",
            False
        )

    @patch("warifuri.cli.commands.issue.check_github_cli")
    @patch("warifuri.cli.commands.issue.get_github_repo")
    @patch("warifuri.cli.commands.issue.discover_all_projects")
    def test_issue_discovery_error(self, mock_discover: Mock, mock_get_repo: Mock,
                                  mock_check: Mock, tmp_path: Path) -> None:
        """Test when project discovery fails."""
        mock_check.return_value = True
        mock_get_repo.return_value = "user/repo"
        mock_discover.side_effect = Exception("Discovery error")

        runner = CliRunner()
        result = runner.invoke(
            issue,
            ["--project", "test-project"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 0
        assert "Warning: Error during project discovery: Discovery error" in result.output
        assert "Attempting to continue with limited functionality..." in result.output

    @patch("warifuri.cli.commands.issue.check_github_cli")
    @patch("warifuri.cli.commands.issue.get_github_repo")
    @patch("warifuri.cli.commands.issue.discover_all_projects")
    @patch("warifuri.cli.commands.issue._create_project_issue")
    def test_issue_dry_run(self, mock_create: Mock, mock_discover: Mock,
                          mock_get_repo: Mock, mock_check: Mock, tmp_path: Path) -> None:
        """Test dry run mode."""
        mock_check.return_value = True
        mock_get_repo.return_value = "user/repo"
        mock_discover.return_value = [self.mock_project]

        runner = CliRunner()
        result = runner.invoke(
            issue,
            ["--project", "test-project", "--dry-run"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 0
        assert "[DRY RUN] GitHub issue creation simulation:" in result.output
        mock_create.assert_called_once_with(
            [self.mock_project],
            "test-project",
            None,
            [],
            "user/repo",
            True  # dry_run = True
        )

    def test_issue_no_workspace_path(self) -> None:
        """Test when workspace path is None."""
        runner = CliRunner()

        result = runner.invoke(
            issue,
            ["--project", "test-project"],
            obj=Context(workspace_path=None)
        )

        # Should fail due to assertion
        assert result.exit_code != 0

    @patch("warifuri.cli.commands.issue.check_github_cli")
    @patch("warifuri.cli.commands.issue.get_github_repo")
    @patch("warifuri.cli.commands.issue.discover_all_projects")
    @patch("warifuri.cli.commands.issue._create_project_issue")
    def test_issue_labels_parsing(self, mock_create: Mock, mock_discover: Mock,
                                 mock_get_repo: Mock, mock_check: Mock, tmp_path: Path) -> None:
        """Test label parsing."""
        mock_check.return_value = True
        mock_get_repo.return_value = "user/repo"
        mock_discover.return_value = [self.mock_project]

        # Test with multiple labels
        runner = CliRunner()
        result = runner.invoke(
            issue,
            ["--project", "test-project", "--label", "bug,enhancement,priority:high"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 0
        mock_create.assert_called_once_with(
            [self.mock_project],
            "test-project",
            None,
            ["bug", "enhancement", "priority:high"],
            "user/repo",
            False
        )

    @patch("warifuri.cli.commands.issue.check_github_cli")
    @patch("warifuri.cli.commands.issue.get_github_repo")
    @patch("warifuri.cli.commands.issue.discover_all_projects")
    @patch("warifuri.cli.commands.issue._create_project_issue")
    def test_issue_no_labels(self, mock_create: Mock, mock_discover: Mock,
                            mock_get_repo: Mock, mock_check: Mock, tmp_path: Path) -> None:
        """Test without labels."""
        mock_check.return_value = True
        mock_get_repo.return_value = "user/repo"
        mock_discover.return_value = [self.mock_project]

        runner = CliRunner()
        result = runner.invoke(
            issue,
            ["--project", "test-project"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 0
        mock_create.assert_called_once_with(
            [self.mock_project],
            "test-project",
            None,
            [],  # Empty labels list
            "user/repo",
            False
        )
