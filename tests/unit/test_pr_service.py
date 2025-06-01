"""Unit tests for PR service module."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import click
import pytest

from warifuri.cli.context import Context
from warifuri.cli.services.pr_service import AutomationValidator, PullRequestService
from warifuri.core.types import Project, Task, TaskInstruction, TaskStatus, TaskType


class TestPullRequestService:
    """Test PullRequestService class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.workspace_path = Path("/test/workspace")
        self.ctx = Mock(spec=Context)
        self.ctx.workspace_path = self.workspace_path
        self.service = PullRequestService(self.ctx)

    def test_init_with_workspace_path(self) -> None:
        """Test successful initialization with workspace path."""
        assert self.service.ctx == self.ctx
        assert self.service.workspace_path == self.workspace_path

    def test_init_without_workspace_path_raises_error(self) -> None:
        """Test initialization fails without workspace path."""
        ctx = Mock(spec=Context)
        ctx.workspace_path = None

        with pytest.raises(click.ClickException, match="Workspace path is required"):
            PullRequestService(ctx)

    @patch("warifuri.cli.services.pr_service.check_github_cli")
    @patch("warifuri.cli.services.pr_service.get_github_repo")
    def test_create_pr_success_minimal(self, mock_get_repo: Mock, mock_check_cli: Mock) -> None:
        """Test successful PR creation with minimal parameters."""
        # Setup mocks
        mock_check_cli.return_value = True
        mock_get_repo.return_value = "owner/repo"

        with (
            patch.object(self.service, "_prepare_pr_details") as mock_prepare,
            patch.object(self.service, "_create_branch_and_commit") as mock_branch,
            patch.object(self.service, "_create_github_pr") as mock_create_pr,
        ):
            mock_prepare.return_value = {"branch_name": "test-branch"}
            mock_branch.return_value = True
            mock_create_pr.return_value = True

            result = self.service.create_pr("test-task")

            assert result is True
            mock_prepare.assert_called_once_with("test-task", None, None, None, None)
            mock_branch.assert_called_once_with({"branch_name": "test-branch"}, False)
            mock_create_pr.assert_called_once_with(
                {"branch_name": "test-branch"}, "main", False, False
            )

    @patch("warifuri.cli.services.pr_service.check_github_cli")
    def test_create_pr_github_cli_validation_fails(self, mock_check_cli: Mock) -> None:
        """Test PR creation fails when GitHub CLI validation fails."""
        mock_check_cli.return_value = False

        result = self.service.create_pr("test-task")

        assert result is False

    @patch("warifuri.cli.services.pr_service.check_github_cli")
    @patch("warifuri.cli.services.pr_service.get_github_repo")
    def test_create_pr_repo_detection_fails(
        self, mock_get_repo: Mock, mock_check_cli: Mock
    ) -> None:
        """Test PR creation fails when repository detection fails."""
        mock_check_cli.return_value = True
        mock_get_repo.return_value = None

        result = self.service.create_pr("test-task")

        assert result is False

    @patch("warifuri.cli.services.pr_service.check_github_cli")
    @patch("warifuri.cli.services.pr_service.get_github_repo")
    def test_create_pr_branch_creation_fails(
        self, mock_get_repo: Mock, mock_check_cli: Mock
    ) -> None:
        """Test PR creation fails when branch creation fails."""
        mock_check_cli.return_value = True
        mock_get_repo.return_value = "owner/repo"

        with (
            patch.object(self.service, "_prepare_pr_details") as mock_prepare,
            patch.object(self.service, "_create_branch_and_commit") as mock_branch,
        ):
            mock_prepare.return_value = {"branch_name": "test-branch"}
            mock_branch.return_value = False

            result = self.service.create_pr("test-task")

            assert result is False

    @patch("warifuri.cli.services.pr_service.check_github_cli")
    @patch("warifuri.cli.services.pr_service.get_github_repo")
    def test_create_pr_github_pr_creation_fails(
        self, mock_get_repo: Mock, mock_check_cli: Mock
    ) -> None:
        """Test PR creation fails when GitHub PR creation fails."""
        mock_check_cli.return_value = True
        mock_get_repo.return_value = "owner/repo"

        with (
            patch.object(self.service, "_prepare_pr_details") as mock_prepare,
            patch.object(self.service, "_create_branch_and_commit") as mock_branch,
            patch.object(self.service, "_create_github_pr") as mock_create_pr,
        ):
            mock_prepare.return_value = {"branch_name": "test-branch"}
            mock_branch.return_value = True
            mock_create_pr.return_value = False

            result = self.service.create_pr("test-task")

            assert result is False

    @patch("warifuri.cli.services.pr_service.check_github_cli")
    @patch("warifuri.cli.services.pr_service.get_github_repo")
    def test_create_pr_with_auto_merge(self, mock_get_repo: Mock, mock_check_cli: Mock) -> None:
        """Test PR creation with auto-merge enabled."""
        mock_check_cli.return_value = True
        mock_get_repo.return_value = "owner/repo"

        with (
            patch.object(self.service, "_prepare_pr_details") as mock_prepare,
            patch.object(self.service, "_create_branch_and_commit") as mock_branch,
            patch.object(self.service, "_create_github_pr") as mock_create_pr,
            patch.object(self.service, "_setup_auto_merge") as mock_auto_merge,
        ):
            mock_prepare.return_value = {"branch_name": "test-branch"}
            mock_branch.return_value = True
            mock_create_pr.return_value = True

            result = self.service.create_pr("test-task", auto_merge=True, merge_method="squash")

            assert result is True
            mock_auto_merge.assert_called_once_with("test-branch", "squash")

    @patch("warifuri.cli.services.pr_service.check_github_cli")
    @patch("warifuri.cli.services.pr_service.get_github_repo")
    def test_create_pr_auto_merge_not_called_for_draft(
        self, mock_get_repo: Mock, mock_check_cli: Mock
    ) -> None:
        """Test auto-merge is not called for draft PRs."""
        mock_check_cli.return_value = True
        mock_get_repo.return_value = "owner/repo"

        with (
            patch.object(self.service, "_prepare_pr_details") as mock_prepare,
            patch.object(self.service, "_create_branch_and_commit") as mock_branch,
            patch.object(self.service, "_create_github_pr") as mock_create_pr,
            patch.object(self.service, "_setup_auto_merge") as mock_auto_merge,
        ):
            mock_prepare.return_value = {"branch_name": "test-branch"}
            mock_branch.return_value = True
            mock_create_pr.return_value = True

            result = self.service.create_pr("test-task", auto_merge=True, draft=True)

            assert result is True
            mock_auto_merge.assert_not_called()

    @patch("warifuri.cli.services.pr_service.check_github_cli")
    def test_validate_github_environment_success(self, mock_check_cli: Mock) -> None:
        """Test successful GitHub environment validation."""
        mock_check_cli.return_value = True

        result = self.service._validate_github_environment()

        assert result is True

    @patch("warifuri.cli.services.pr_service.check_github_cli")
    def test_validate_github_environment_failure(self, mock_check_cli: Mock) -> None:
        """Test GitHub environment validation failure."""
        mock_check_cli.return_value = False

        result = self.service._validate_github_environment()

        assert result is False

    def test_prepare_pr_details_with_defaults(self) -> None:
        """Test PR details preparation with default values."""
        result = self.service._prepare_pr_details("test-task", None, None, None, None)

        expected = {
            "task_name": "test-task",
            "branch_name": "warifuri/automation/test-task",
            "commit_message": "feat: automate task test-task",
            "pr_title": "Automate task: test-task",
            "pr_body": "Automated execution of task `test-task` via Warifuri.",
        }
        assert result == expected

    def test_prepare_pr_details_with_custom_values(self) -> None:
        """Test PR details preparation with custom values."""
        result = self.service._prepare_pr_details(
            "test-task", "custom-branch", "custom commit", "Custom Title", "Custom body"
        )

        expected = {
            "task_name": "test-task",
            "branch_name": "custom-branch",
            "commit_message": "custom commit",
            "pr_title": "Custom Title",
            "pr_body": "Custom body",
        }
        assert result == expected

    @patch("subprocess.run")
    def test_create_branch_and_commit_dry_run(self, mock_run: Mock) -> None:
        """Test branch creation and commit in dry run mode."""
        pr_details = {"branch_name": "test-branch", "commit_message": "test commit"}

        result = self.service._create_branch_and_commit(pr_details, dry_run=True)

        assert result is True
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_create_branch_and_commit_success(self, mock_run: Mock) -> None:
        """Test successful branch creation and commit."""
        pr_details = {"branch_name": "test-branch", "commit_message": "test commit"}

        mock_run.return_value = Mock()

        result = self.service._create_branch_and_commit(pr_details, dry_run=False)

        assert result is True
        assert mock_run.call_count == 4  # checkout, add, commit, push

        # Verify git commands
        calls = mock_run.call_args_list
        assert calls[0][0][0] == ["git", "checkout", "-b", "test-branch"]
        assert calls[1][0][0] == ["git", "add", "."]
        assert calls[2][0][0] == ["git", "commit", "-m", "test commit"]
        assert calls[3][0][0] == ["git", "push", "origin", "test-branch"]

    @patch("subprocess.run")
    def test_create_branch_and_commit_failure(self, mock_run: Mock) -> None:
        """Test branch creation and commit failure."""
        pr_details = {"branch_name": "test-branch", "commit_message": "test commit"}

        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = self.service._create_branch_and_commit(pr_details, dry_run=False)

        assert result is False

    @patch("subprocess.run")
    def test_create_github_pr_dry_run(self, mock_run: Mock) -> None:
        """Test GitHub PR creation in dry run mode."""
        pr_details = {"pr_title": "Test PR", "pr_body": "Test body", "branch_name": "test-branch"}

        result = self.service._create_github_pr(pr_details, "main", False, dry_run=True)

        assert result is True
        mock_run.assert_not_called()

    @patch("subprocess.run")
    def test_create_github_pr_success(self, mock_run: Mock) -> None:
        """Test successful GitHub PR creation."""
        pr_details = {"pr_title": "Test PR", "pr_body": "Test body", "branch_name": "test-branch"}

        mock_run.return_value = Mock(stdout="https://github.com/owner/repo/pull/123")

        result = self.service._create_github_pr(pr_details, "main", False, dry_run=False)

        assert result is True
        mock_run.assert_called_once()

        # Verify gh command
        args = mock_run.call_args[0][0]
        assert args[:3] == ["gh", "pr", "create"]
        assert "--title" in args
        assert "Test PR" in args
        assert "--body" in args
        assert "Test body" in args

    @patch("subprocess.run")
    def test_create_github_pr_with_draft(self, mock_run: Mock) -> None:
        """Test GitHub PR creation with draft flag."""
        pr_details = {"pr_title": "Test PR", "pr_body": "Test body", "branch_name": "test-branch"}

        mock_run.return_value = Mock(stdout="https://github.com/owner/repo/pull/123")

        result = self.service._create_github_pr(pr_details, "main", True, dry_run=False)

        assert result is True

        # Verify draft flag is included
        args = mock_run.call_args[0][0]
        assert "--draft" in args

    @patch("subprocess.run")
    def test_create_github_pr_failure(self, mock_run: Mock) -> None:
        """Test GitHub PR creation failure."""
        pr_details = {"pr_title": "Test PR", "pr_body": "Test body", "branch_name": "test-branch"}

        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        result = self.service._create_github_pr(pr_details, "main", False, dry_run=False)

        assert result is False

    @patch("subprocess.run")
    def test_setup_auto_merge_success(self, mock_run: Mock) -> None:
        """Test successful auto-merge setup."""
        mock_run.return_value = Mock()

        self.service._setup_auto_merge("test-branch", "squash")

        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["gh", "pr", "merge", "test-branch", "--squash", "--auto"]

    @patch("subprocess.run")
    def test_setup_auto_merge_failure(self, mock_run: Mock) -> None:
        """Test auto-merge setup failure (should not raise, just warn)."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        # Should not raise an exception
        self.service._setup_auto_merge("test-branch", "merge")

        mock_run.assert_called_once()


class TestAutomationValidator:
    """Test AutomationValidator class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.workspace_path = Path("/test/workspace")
        self.ctx = Mock(spec=Context)
        self.ctx.workspace_path = self.workspace_path
        self.validator = AutomationValidator(self.ctx)

    def test_init_with_workspace_path(self) -> None:
        """Test successful initialization with workspace path."""
        assert self.validator.ctx == self.ctx
        assert self.validator.workspace_path == self.workspace_path

    def test_init_without_workspace_path_raises_error(self) -> None:
        """Test initialization fails without workspace path."""
        ctx = Mock(spec=Context)
        ctx.workspace_path = None

        with pytest.raises(click.ClickException, match="Workspace path is required"):
            AutomationValidator(ctx)

    @patch("subprocess.run")
    def test_validate_github_prerequisites_success(self, mock_run: Mock) -> None:
        """Test successful GitHub prerequisites validation."""
        mock_run.return_value = Mock()

        result = self.validator.validate_github_prerequisites()

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["git", "rev-parse", "--git-dir"]

    @patch("subprocess.run")
    def test_validate_github_prerequisites_not_git_repo(self, mock_run: Mock) -> None:
        """Test GitHub prerequisites validation when not in git repo."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = self.validator.validate_github_prerequisites()

        assert result is False

    @patch("warifuri.core.discovery.discover_all_projects")
    @patch("warifuri.core.discovery.find_ready_tasks")
    def test_validate_task_ready_success(self, mock_find_ready: Mock, mock_discover: Mock) -> None:
        """Test successful task readiness validation."""
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

        # Create mock project
        project = Project(name="test-project", path=Path("/test/project"), tasks=[task])

        mock_discover.return_value = [project]
        mock_find_ready.return_value = [task]

        result = self.validator.validate_task_ready("test-task")

        assert result is True

    @patch("warifuri.core.discovery.discover_all_projects")
    def test_validate_task_ready_no_projects(self, mock_discover: Mock) -> None:
        """Test task readiness validation when no projects found."""
        mock_discover.return_value = []

        result = self.validator.validate_task_ready("test-task")

        assert result is False

    @patch("warifuri.core.discovery.discover_all_projects")
    @patch("warifuri.core.discovery.find_ready_tasks")
    def test_validate_task_ready_task_not_found(
        self, mock_find_ready: Mock, mock_discover: Mock
    ) -> None:
        """Test task readiness validation when task not found."""
        # Create mock task with different name
        task_instruction = TaskInstruction(
            name="other-task", description="Other task", dependencies=[], inputs=[], outputs=[]
        )
        task = Task(
            project="test-project",
            name="other-task",
            path=Path("/test/path"),
            instruction=task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY,
        )

        project = Project(name="test-project", path=Path("/test/project"), tasks=[task])

        mock_discover.return_value = [project]
        mock_find_ready.return_value = [task]

        result = self.validator.validate_task_ready("test-task")

        assert result is False

    @patch("warifuri.core.discovery.discover_all_projects")
    @patch("warifuri.core.discovery.find_ready_tasks")
    def test_validate_task_ready_task_not_ready(
        self, mock_find_ready: Mock, mock_discover: Mock
    ) -> None:
        """Test task readiness validation when task is not ready."""
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
            status=TaskStatus.PENDING,
        )

        project = Project(name="test-project", path=Path("/test/project"), tasks=[task])

        mock_discover.return_value = [project]
        mock_find_ready.return_value = []  # Task is not in ready tasks

        result = self.validator.validate_task_ready("test-task")

        assert result is False

    @patch("subprocess.run")
    def test_validate_workspace_clean_success(self, mock_run: Mock) -> None:
        """Test successful workspace clean validation."""
        mock_run.return_value = Mock(stdout="")  # Empty output means clean

        result = self.validator.validate_workspace_clean()

        assert result is True
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args == ["git", "status", "--porcelain"]

    @patch("subprocess.run")
    def test_validate_workspace_clean_has_changes(self, mock_run: Mock) -> None:
        """Test workspace clean validation when there are uncommitted changes."""
        mock_run.return_value = Mock(stdout="M file.txt\n")  # Modified file

        result = self.validator.validate_workspace_clean()

        assert result is False

    @patch("subprocess.run")
    def test_validate_workspace_clean_git_error(self, mock_run: Mock) -> None:
        """Test workspace clean validation when git command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = self.validator.validate_workspace_clean()

        assert result is False


class TestIntegration:
    """Integration tests for PR service components."""

    def test_end_to_end_pr_creation_dry_run(self) -> None:
        """Test end-to-end PR creation in dry run mode."""
        workspace_path = Path("/test/workspace")
        ctx = Mock(spec=Context)
        ctx.workspace_path = workspace_path

        service = PullRequestService(ctx)

        with (
            patch("warifuri.cli.services.pr_service.check_github_cli") as mock_check_cli,
            patch("warifuri.cli.services.pr_service.get_github_repo") as mock_get_repo,
        ):
            mock_check_cli.return_value = True
            mock_get_repo.return_value = "owner/repo"

            result = service.create_pr("test-task", dry_run=True)

            assert result is True
