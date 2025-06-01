"""Unit tests for automation CLI commands."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from warifuri.cli.commands.automation import automation_list, check_automation, create_pr, merge_pr
from warifuri.cli.context import Context
from warifuri.core.types import Project, Task, TaskInstruction, TaskStatus, TaskType


class TestAutomationCommands:
    """Test cases for automation commands."""

    @pytest.fixture
    def runner(self):
        """Click test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_context(self):
        """Mock context for testing."""
        ctx = Mock(spec=Context)
        temp_workspace = Path("/tmp/test_workspace")
        ctx.ensure_workspace_path.return_value = temp_workspace
        ctx.workspace_path = temp_workspace
        return ctx

    @pytest.fixture
    def sample_projects(self):
        """Sample projects for testing."""
        setup_instruction = TaskInstruction(
            name="setup",
            description="Setup task",
            dependencies=[],
            inputs=[],
            outputs=["config.json"],
            note="Setup configuration",
        )

        setup_task = Task(
            project="demo",
            name="setup",
            path=Path("/workspace/projects/demo/setup"),
            instruction=setup_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY,
        )

        project = Project(name="demo", path=Path("/workspace/projects/demo"), tasks=[setup_task])
        return [project]

    def test_automation_list_basic(self, runner, mock_context):
        """Test basic automation list command."""
        with patch("warifuri.cli.commands.automation.AutomationListService") as mock_service:
            mock_service_instance = Mock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.list_automation_tasks.return_value = []
            mock_service_instance.output_results.return_value = None

            with patch("warifuri.cli.commands.automation.pass_context", return_value=lambda f: f):
                result = runner.invoke(automation_list, [], obj=mock_context)

                assert result.exit_code == 0
                mock_service.assert_called_once_with(mock_context)
                mock_service_instance.list_automation_tasks.assert_called_once_with(
                    ready_only=False, machine_only=False, project=None
                )
                mock_service_instance.output_results.assert_called_once_with([], "plain")

    def test_automation_list_with_filters(self, runner, mock_context):
        """Test automation list with various filters."""
        with patch("warifuri.cli.commands.automation.AutomationListService") as mock_service:
            mock_service_instance = Mock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.list_automation_tasks.return_value = []
            mock_service_instance.output_results.return_value = None

            with patch("warifuri.cli.commands.automation.pass_context", return_value=lambda f: f):
                result = runner.invoke(
                    automation_list,
                    ["--ready-only", "--machine-only", "--format", "json", "--project", "demo"],
                    obj=mock_context,
                )

                assert result.exit_code == 0
                mock_service_instance.list_automation_tasks.assert_called_once_with(
                    ready_only=True, machine_only=True, project="demo"
                )
                mock_service_instance.output_results.assert_called_once_with([], "json")

    def test_automation_check_basic(self, runner, mock_context):
        """Test basic automation check command."""
        with patch("warifuri.cli.commands.automation.AutomationCheckService") as mock_service:
            mock_service_instance = Mock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.check_task_automation.return_value = (True, [], None)
            mock_service_instance.output_check_results.return_value = None

            with patch("warifuri.cli.commands.automation.pass_context", return_value=lambda f: f):
                result = runner.invoke(check_automation, ["demo/setup"], obj=mock_context)

                assert result.exit_code == 0
                mock_service.assert_called_once_with(mock_context)
                mock_service_instance.check_task_automation.assert_called_once_with("demo/setup")
                mock_service_instance.output_check_results.assert_called_once_with(
                    task_name="demo/setup",
                    can_automate=True,
                    issues=[],
                    auto_merge_config=None,
                    check_only=False,
                )

    def test_automation_check_with_verbose(self, runner, mock_context):
        """Test automation check with verbose output."""
        with patch("warifuri.cli.commands.automation.AutomationCheckService") as mock_service:
            mock_service_instance = Mock()
            mock_service.return_value = mock_service_instance
            mock_service_instance.check_task_automation.return_value = (True, [], None)
            mock_service_instance.output_check_results.return_value = None

            with patch("warifuri.cli.commands.automation.pass_context", return_value=lambda f: f):
                result = runner.invoke(
                    check_automation, ["--check-only", "demo/setup"], obj=mock_context
                )

                assert result.exit_code == 0
                mock_service_instance.output_check_results.assert_called_once_with(
                    task_name="demo/setup",
                    can_automate=True,
                    issues=[],
                    auto_merge_config=None,
                    check_only=True,
                )

    def test_create_pr_validation_failure_github_prerequisites(self, runner, mock_context):
        """Test create_pr when GitHub prerequisites validation fails."""
        with patch("warifuri.cli.commands.automation.AutomationValidator") as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_github_prerequisites.return_value = False

            with patch("warifuri.cli.commands.automation.pass_context", return_value=lambda f: f):
                result = runner.invoke(create_pr, ["demo/setup"], obj=mock_context)

                assert result.exit_code == 1  # click.Abort()
                mock_validator.validate_github_prerequisites.assert_called_once()

    def test_create_pr_validation_failure_workspace_clean(self, runner, mock_context):
        """Test create_pr when workspace clean validation fails."""
        with patch("warifuri.cli.commands.automation.AutomationValidator") as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_github_prerequisites.return_value = True
            mock_validator.validate_workspace_clean.return_value = False

            with patch("warifuri.cli.commands.automation.pass_context", return_value=lambda f: f):
                result = runner.invoke(create_pr, ["demo/setup"], obj=mock_context)

                assert result.exit_code == 1  # click.Abort()
                mock_validator.validate_github_prerequisites.assert_called_once()
                mock_validator.validate_workspace_clean.assert_called_once()

    def test_create_pr_service_success(self, runner, mock_context):
        """Test successful PR creation."""
        with patch("warifuri.cli.commands.automation.AutomationValidator") as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_github_prerequisites.return_value = True
            mock_validator.validate_workspace_clean.return_value = True

            with patch("warifuri.cli.commands.automation.PullRequestService") as mock_pr_service:
                mock_pr_instance = Mock()
                mock_pr_service.return_value = mock_pr_instance
                mock_pr_instance.create_pr.return_value = True

                with patch(
                    "warifuri.cli.commands.automation.pass_context", return_value=lambda f: f
                ):
                    result = runner.invoke(create_pr, ["demo/setup"], obj=mock_context)

                    assert result.exit_code == 0
                    mock_pr_instance.create_pr.assert_called_once_with(
                        task_name="demo/setup",
                        branch_name=None,
                        commit_message=None,
                        pr_title=None,
                        pr_body=None,
                        base_branch="main",
                        draft=False,
                        auto_merge=False,
                        merge_method="squash",
                        dry_run=False,
                    )

    def test_create_pr_service_failure(self, runner, mock_context):
        """Test PR creation service failure."""
        with patch("warifuri.cli.commands.automation.AutomationValidator") as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_github_prerequisites.return_value = True
            mock_validator.validate_workspace_clean.return_value = True

            with patch("warifuri.cli.commands.automation.PullRequestService") as mock_pr_service:
                mock_pr_instance = Mock()
                mock_pr_service.return_value = mock_pr_instance
                mock_pr_instance.create_pr.return_value = False

                with patch(
                    "warifuri.cli.commands.automation.pass_context", return_value=lambda f: f
                ):
                    result = runner.invoke(create_pr, ["demo/setup"], obj=mock_context)

                    assert result.exit_code == 1  # click.Abort()

    def test_create_pr_with_all_options(self, runner, mock_context):
        """Test PR creation with all command line options."""
        with patch("warifuri.cli.commands.automation.AutomationValidator") as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_github_prerequisites.return_value = True
            mock_validator.validate_workspace_clean.return_value = True

            with patch("warifuri.cli.commands.automation.PullRequestService") as mock_pr_service:
                mock_pr_instance = Mock()
                mock_pr_service.return_value = mock_pr_instance
                mock_pr_instance.create_pr.return_value = True

                with patch(
                    "warifuri.cli.commands.automation.pass_context", return_value=lambda f: f
                ):
                    result = runner.invoke(
                        create_pr,
                        [
                            "demo/setup",
                            "--branch-name",
                            "feature/setup",
                            "--commit-message",
                            "Add setup functionality",
                            "--pr-title",
                            "Setup task implementation",
                            "--pr-body",
                            "Implements the setup task",
                            "--base-branch",
                            "develop",
                            "--draft",
                            "--auto-merge",
                            "--merge-method",
                            "squash",
                            "--dry-run",
                        ],
                        obj=mock_context,
                    )

                    assert result.exit_code == 0
                    mock_pr_instance.create_pr.assert_called_once_with(
                        task_name="demo/setup",
                        branch_name="feature/setup",
                        commit_message="Add setup functionality",
                        pr_title="Setup task implementation",
                        pr_body="Implements the setup task",
                        base_branch="develop",
                        draft=True,
                        auto_merge=True,
                        merge_method="squash",
                        dry_run=True,
                    )

    def test_merge_pr_validation_failure(self, runner, mock_context):
        """Test merge_pr when GitHub prerequisites validation fails."""
        with patch("warifuri.cli.commands.automation.AutomationValidator") as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_github_prerequisites.return_value = False

            with patch("warifuri.cli.commands.automation.pass_context", return_value=lambda f: f):
                result = runner.invoke(
                    merge_pr, ["https://github.com/owner/repo/pull/123"], obj=mock_context
                )

                assert result.exit_code == 1  # click.Abort()
                mock_validator.validate_github_prerequisites.assert_called_once()

    def test_merge_pr_dry_run(self, runner, mock_context):
        """Test merge_pr in dry-run mode."""
        with patch("warifuri.cli.commands.automation.AutomationValidator") as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_github_prerequisites.return_value = True

            with patch("warifuri.cli.commands.automation.pass_context", return_value=lambda f: f):
                result = runner.invoke(
                    merge_pr,
                    ["--dry-run", "https://github.com/owner/repo/pull/123"],
                    obj=mock_context,
                )

                assert result.exit_code == 0
                assert "DRY RUN - Would merge PR:" in result.output
                assert "https://github.com/owner/repo/pull/123" in result.output
                assert "Method: squash" in result.output

    def test_merge_pr_dry_run_with_squash(self, runner, mock_context):
        """Test merge_pr in dry-run mode with squash method."""
        with patch("warifuri.cli.commands.automation.AutomationValidator") as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_github_prerequisites.return_value = True

            with patch("warifuri.cli.commands.automation.pass_context", return_value=lambda f: f):
                result = runner.invoke(
                    merge_pr,
                    [
                        "--dry-run",
                        "--merge-method",
                        "squash",
                        "https://github.com/owner/repo/pull/123",
                    ],
                    obj=mock_context,
                )

                assert result.exit_code == 0
                assert "Method: squash" in result.output

    def test_merge_pr_success(self, runner, mock_context):
        """Test successful PR merge."""
        with patch("warifuri.cli.commands.automation.AutomationValidator") as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_github_prerequisites.return_value = True

            with patch(
                "warifuri.cli.commands.automation.TaskExecutionService"
            ) as mock_task_service:
                mock_task_instance = Mock()
                mock_task_service.return_value = mock_task_instance
                mock_task_instance.merge_pr.return_value = True

                with patch(
                    "warifuri.cli.commands.automation.pass_context", return_value=lambda f: f
                ):
                    result = runner.invoke(
                        merge_pr, ["https://github.com/owner/repo/pull/123"], obj=mock_context
                    )

                    assert result.exit_code == 0
                    mock_task_instance.merge_pr.assert_called_once_with(
                        "https://github.com/owner/repo/pull/123", "squash"
                    )

    def test_merge_pr_failure(self, runner, mock_context):
        """Test PR merge failure."""
        with patch("warifuri.cli.commands.automation.AutomationValidator") as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_github_prerequisites.return_value = True

            with patch(
                "warifuri.cli.commands.automation.TaskExecutionService"
            ) as mock_task_service:
                mock_task_instance = Mock()
                mock_task_service.return_value = mock_task_instance
                mock_task_instance.merge_pr.return_value = False

                with patch(
                    "warifuri.cli.commands.automation.pass_context", return_value=lambda f: f
                ):
                    result = runner.invoke(
                        merge_pr, ["https://github.com/owner/repo/pull/123"], obj=mock_context
                    )

                    assert result.exit_code == 1  # click.Abort()

    def test_merge_pr_with_rebase_method(self, runner, mock_context):
        """Test PR merge with rebase method."""
        with patch("warifuri.cli.commands.automation.AutomationValidator") as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_github_prerequisites.return_value = True

            with patch(
                "warifuri.cli.commands.automation.TaskExecutionService"
            ) as mock_task_service:
                mock_task_instance = Mock()
                mock_task_service.return_value = mock_task_instance
                mock_task_instance.merge_pr.return_value = True

                with patch(
                    "warifuri.cli.commands.automation.pass_context", return_value=lambda f: f
                ):
                    result = runner.invoke(
                        merge_pr,
                        ["--merge-method", "rebase", "https://github.com/owner/repo/pull/123"],
                        obj=mock_context,
                    )

                    assert result.exit_code == 0
                    mock_task_instance.merge_pr.assert_called_once_with(
                        "https://github.com/owner/repo/pull/123", "rebase"
                    )
