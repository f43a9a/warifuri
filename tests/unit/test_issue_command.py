"""Unit tests for CLI issue command."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from warifuri.cli.commands.issue import issue
from warifuri.cli.context import Context
from warifuri.core.types import Project, Task, TaskInstruction, TaskStatus, TaskType


class TestIssueCommand:
    """Test cases for issue command."""

    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_context(self, temp_workspace):
        """Mock context with workspace."""
        ctx = Mock(spec=Context)
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
        return [project]  # Return a list, not a dict

    def test_github_cli_not_available(self, runner, mock_context):
        """Test error when GitHub CLI is not available."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=False):
            with patch("warifuri.cli.commands.issue.pass_context", return_value=lambda f: f):
                result = runner.invoke(issue, ["--project", "demo"], obj=mock_context)

                assert result.exit_code == 0
                assert "GitHub CLI (gh) is not installed" in result.output
                assert "https://cli.github.com/" in result.output

    def test_no_github_repo(self, runner, mock_context):
        """Test error when not in a GitHub repository."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value=None):
                with patch("warifuri.cli.commands.issue.pass_context", return_value=lambda f: f):
                    result = runner.invoke(issue, ["--project", "demo"], obj=mock_context)

                    assert result.exit_code == 0
                    assert "Could not detect GitHub repository" in result.output

    def test_no_options_specified(self, runner, mock_context):
        """Test error when no options are specified."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch("warifuri.cli.commands.issue.pass_context", return_value=lambda f: f):
                    result = runner.invoke(issue, [], obj=mock_context)

                    assert result.exit_code == 0
                    assert "Specify exactly one of" in result.output

    def test_multiple_options_specified(self, runner, mock_context):
        """Test error when multiple mutually exclusive options are specified."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch("warifuri.cli.commands.issue.pass_context", return_value=lambda f: f):
                    result = runner.invoke(
                        issue, ["--project", "demo", "--task", "demo/setup"], obj=mock_context
                    )

                    assert result.exit_code == 0
                    assert "Specify exactly one of" in result.output

    def test_project_not_found(self, runner, mock_context):
        """Test error when project is not found."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch("warifuri.cli.commands.issue.discover_all_projects", return_value={}):
                    with patch(
                        "warifuri.cli.commands.issue.pass_context", return_value=lambda f: f
                    ):
                        result = runner.invoke(
                            issue, ["--project", "nonexistent"], obj=mock_context
                        )

                        assert result.exit_code == 0
                        assert "Project 'nonexistent' not found" in result.output

    def test_task_not_found(self, runner, mock_context, sample_projects):
        """Test error when task is not found."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch(
                    "warifuri.cli.commands.issue.discover_all_projects",
                    return_value=sample_projects,
                ):
                    with patch("warifuri.cli.commands.issue.find_task_by_name", return_value=None):
                        with patch(
                            "warifuri.cli.commands.issue.pass_context", return_value=lambda f: f
                        ):
                            result = runner.invoke(
                                issue, ["--task", "demo/nonexistent"], obj=mock_context
                            )

                            assert result.exit_code == 0
                            assert "Task 'demo/nonexistent' not found" in result.output

    def test_create_project_issue_dry_run(self, runner, mock_context, sample_projects):
        """Test creating project issue in dry-run mode."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch(
                    "warifuri.cli.commands.issue.discover_all_projects",
                    return_value=sample_projects,
                ):
                    with patch(
                        "warifuri.cli.commands.issue.pass_context", return_value=lambda f: f
                    ):
                        result = runner.invoke(
                            issue, ["--project", "demo", "--dry-run"], obj=mock_context
                        )

                        assert result.exit_code == 0
                        assert "[DRY RUN] GitHub issue creation simulation:" in result.output

    def test_create_task_issue_dry_run(self, runner, mock_context, sample_projects):
        """Test creating task issue in dry-run mode."""
        mock_task = sample_projects[0].tasks[0]  # Get first task from first project

        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch(
                    "warifuri.cli.commands.issue.discover_all_projects",
                    return_value=sample_projects,
                ):
                    with patch(
                        "warifuri.cli.commands.issue.find_task_by_name", return_value=mock_task
                    ):
                        with patch(
                            "warifuri.cli.commands.issue.pass_context", return_value=lambda f: f
                        ):
                            result = runner.invoke(
                                issue, ["--task", "demo/setup", "--dry-run"], obj=mock_context
                            )

                            assert result.exit_code == 0
                            assert "[DRY RUN] GitHub issue creation simulation:" in result.output

    def test_create_all_tasks_issues_dry_run(self, runner, mock_context, sample_projects):
        """Test creating all tasks issues in dry-run mode."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch(
                    "warifuri.cli.commands.issue.discover_all_projects",
                    return_value=sample_projects,
                ):
                    with patch(
                        "warifuri.cli.commands.issue.pass_context", return_value=lambda f: f
                    ):
                        result = runner.invoke(
                            issue, ["--all-tasks", "demo", "--dry-run"], obj=mock_context
                        )

                        assert result.exit_code == 0
                        assert "Would create 1 task issues for project 'demo'" in result.output

    def test_create_project_issue_actual(self, runner, mock_context, sample_projects):
        """Test actually creating project issue."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch(
                    "warifuri.cli.commands.issue.discover_all_projects",
                    return_value=sample_projects,
                ):
                    with patch("warifuri.cli.commands.issue.ensure_labels_exist"):
                        with patch(
                            "warifuri.cli.commands.issue.create_issue_safe",
                            return_value=(True, "https://github.com/owner/repo/issues/123"),
                        ) as mock_create:
                            with patch(
                                "warifuri.cli.commands.issue.pass_context", return_value=lambda f: f
                            ):
                                result = runner.invoke(
                                    issue, ["--project", "demo"], obj=mock_context
                                )

                                assert result.exit_code == 0
                                # Verify create_issue_safe was called for project issue
                                mock_create.assert_called_once()

    def test_create_task_issue_actual(self, runner, mock_context, sample_projects):
        """Test actually creating task issue."""
        mock_task = sample_projects[0].tasks[0]  # Get first task from first project

        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch(
                    "warifuri.cli.commands.issue.discover_all_projects",
                    return_value=sample_projects,
                ):
                    with patch(
                        "warifuri.cli.commands.issue.find_task_by_name", return_value=mock_task
                    ):
                        with patch("warifuri.cli.commands.issue.ensure_labels_exist"):
                            with patch(
                                "warifuri.cli.commands.issue.create_issue_safe",
                                return_value=(True, "https://github.com/owner/repo/issues/124"),
                            ) as mock_create:
                                with patch(
                                    "warifuri.cli.commands.issue.format_task_issue_body",
                                    return_value="Task body",
                                ):
                                    with patch(
                                        "warifuri.cli.commands.issue.pass_context",
                                        return_value=lambda f: f,
                                    ):
                                        result = runner.invoke(
                                            issue, ["--task", "demo/setup"], obj=mock_context
                                        )

                                        assert result.exit_code == 0
                                        # Task issue creation doesn't output success message, just verify it was called
                                        mock_create.assert_called_once()

    def test_labels_parsing(self, runner, mock_context, sample_projects):
        """Test proper parsing of comma-separated labels."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch(
                    "warifuri.cli.commands.issue.discover_all_projects",
                    return_value=sample_projects,
                ):
                    with patch("warifuri.cli.commands.issue.ensure_labels_exist") as mock_labels:
                        with patch(
                            "warifuri.cli.commands.issue.create_issue_safe",
                            return_value=(True, "https://github.com/owner/repo/issues/123"),
                        ):
                            with patch(
                                "warifuri.cli.commands.issue.pass_context", return_value=lambda f: f
                            ):
                                result = runner.invoke(
                                    issue,
                                    [
                                        "--project",
                                        "demo",
                                        "--label",
                                        "enhancement,bug,high-priority",
                                    ],
                                    obj=mock_context,
                                )

                                assert result.exit_code == 0
                                # Verify labels were parsed correctly
                                expected_labels = ["enhancement", "bug", "high-priority"]
                                mock_labels.assert_called_once()
                                call_args = mock_labels.call_args[0]
                                assert call_args[0] == "owner/repo"  # First arg is repo
                                assert set(call_args[1]) == set(
                                    expected_labels
                                )  # Second arg is labels

    def test_assignee_option(self, runner, mock_context, sample_projects):
        """Test assignee option is handled correctly."""
        mock_task = sample_projects[0].tasks[0]  # Get first task from first project

        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch(
                    "warifuri.cli.commands.issue.discover_all_projects",
                    return_value=sample_projects,
                ):
                    with patch(
                        "warifuri.cli.commands.issue.find_task_by_name", return_value=mock_task
                    ):
                        with patch("warifuri.cli.commands.issue.ensure_labels_exist"):
                            with patch(
                                "warifuri.cli.commands.issue.create_issue_safe",
                                return_value=(True, "https://github.com/owner/repo/issues/125"),
                            ) as mock_create:
                                with patch(
                                    "warifuri.cli.commands.issue.format_task_issue_body",
                                    return_value="Task body",
                                ):
                                    with patch(
                                        "warifuri.cli.commands.issue.pass_context",
                                        return_value=lambda f: f,
                                    ):
                                        result = runner.invoke(
                                            issue,
                                            ["--task", "demo/setup", "--assignee", "john_doe"],
                                            obj=mock_context,
                                        )

                                        assert result.exit_code == 0
                                        # Verify assignee was passed to create_issue_safe
                                        call_args = mock_create.call_args[1]  # kwargs
                                        assert call_args.get("assignee") == "john_doe"

    def test_discovery_error_handling(self, runner, mock_context):
        """Test handling of discovery errors."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch(
                    "warifuri.cli.commands.issue.discover_all_projects",
                    side_effect=Exception("Discovery failed"),
                ):
                    with patch(
                        "warifuri.cli.commands.issue.pass_context", return_value=lambda f: f
                    ):
                        result = runner.invoke(issue, ["--project", "demo"], obj=mock_context)

                        assert result.exit_code == 0
                        assert "Error during project discovery" in result.output

    def test_issue_creation_error_handling(self, runner, mock_context, sample_projects):
        """Test handling of issue creation errors."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch(
                    "warifuri.cli.commands.issue.discover_all_projects",
                    return_value=sample_projects,
                ):
                    with patch("warifuri.cli.commands.issue.ensure_labels_exist"):
                        with patch(
                            "warifuri.cli.commands.issue.create_issue_safe",
                            return_value=(False, None),
                        ):
                            with patch(
                                "warifuri.cli.commands.issue.pass_context", return_value=lambda f: f
                            ):
                                result = runner.invoke(
                                    issue, ["--project", "demo"], obj=mock_context
                                )

                                assert result.exit_code == 0
                                assert "Failed to create project issue" in result.output

    def test_all_tasks_project_not_found(self, runner, mock_context):
        """Test all-tasks option with nonexistent project."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch("warifuri.cli.commands.issue.discover_all_projects", return_value={}):
                    with patch(
                        "warifuri.cli.commands.issue.pass_context", return_value=lambda f: f
                    ):
                        result = runner.invoke(
                            issue, ["--all-tasks", "nonexistent"], obj=mock_context
                        )

                        assert result.exit_code == 0
                        assert "Project 'nonexistent' not found" in result.output

    def test_empty_labels_handling(self, runner, mock_context, sample_projects):
        """Test handling of empty labels string."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch(
                    "warifuri.cli.commands.issue.discover_all_projects",
                    return_value=sample_projects,
                ):
                    with patch("warifuri.cli.commands.issue.ensure_labels_exist") as mock_labels:
                        with patch(
                            "warifuri.cli.commands.issue.create_issue_safe",
                            return_value=(True, "https://github.com/owner/repo/issues/123"),
                        ):
                            with patch(
                                "warifuri.cli.commands.issue.pass_context", return_value=lambda f: f
                            ):
                                result = runner.invoke(
                                    issue, ["--project", "demo", "--label", ""], obj=mock_context
                                )

                                assert result.exit_code == 0
                                # Should not call ensure_labels_exist with empty labels
                                mock_labels.assert_not_called()

    def test_create_all_tasks_actual(self, runner, mock_context, sample_projects):
        """Test actually creating all task issues for a project."""
        with patch("warifuri.cli.commands.issue.check_github_cli", return_value=True):
            with patch("warifuri.cli.commands.issue.get_github_repo", return_value="owner/repo"):
                with patch(
                    "warifuri.cli.commands.issue.discover_all_projects",
                    return_value=sample_projects,
                ):
                    with patch("warifuri.cli.commands.issue.ensure_labels_exist"):
                        with patch(
                            "warifuri.cli.commands.issue.create_issue_safe",
                            return_value=(True, "https://github.com/owner/repo/issues/126"),
                        ) as mock_create:
                            with patch(
                                "warifuri.cli.commands.issue.format_task_issue_body",
                                return_value="Task body",
                            ):
                                with patch(
                                    "warifuri.cli.commands.issue.pass_context",
                                    return_value=lambda f: f,
                                ):
                                    result = runner.invoke(
                                        issue, ["--all-tasks", "demo"], obj=mock_context
                                    )

                                    assert result.exit_code == 0
                                    assert (
                                        "Successfully created 1/1 task issues for project 'demo'"
                                        in result.output
                                    )
                                    # Should be called once for each task
                                    assert mock_create.call_count == 1
