"""Tests for mark_done command."""

from pathlib import Path
from unittest.mock import Mock, patch

from click.testing import CliRunner

from warifuri.cli.commands.mark_done import mark_done
from warifuri.cli.context import Context
from warifuri.core.types import Task


class TestMarkDoneCommand:
    """Test mark_done command."""

    def test_mark_done_success(self, tmp_path: Path) -> None:
        """Test successful task completion."""
        # Create test task
        mock_task = Mock(spec=Task)
        mock_task.is_completed = False
        mock_task.name = "test-task"
        mock_task.full_name = "test-project/test-task"

        with patch("warifuri.cli.commands.mark_done.discover_all_projects") as mock_discover:
            with patch("warifuri.cli.commands.mark_done.find_task_by_name") as mock_find:
                with patch("warifuri.cli.commands.mark_done.create_done_file") as mock_create:
                    mock_discover.return_value = []
                    mock_find.return_value = mock_task

                    runner = CliRunner()
                    result = runner.invoke(
                        mark_done,
                        ["test-project/test-task", "--message", "Completed successfully"],
                        obj=Context(workspace_path=tmp_path)
                    )

                    assert result.exit_code == 0
                    assert "✅ Marked task as completed: test-project/test-task" in result.output
                    assert "Message: Completed successfully" in result.output

                    mock_create.assert_called_once_with(mock_task, "Completed successfully")

    def test_mark_done_no_message(self, tmp_path: Path) -> None:
        """Test marking task done without custom message."""
        mock_task = Mock(spec=Task)
        mock_task.is_completed = False

        with patch("warifuri.cli.commands.mark_done.discover_all_projects") as mock_discover:
            with patch("warifuri.cli.commands.mark_done.find_task_by_name") as mock_find:
                with patch("warifuri.cli.commands.mark_done.create_done_file") as mock_create:
                    mock_discover.return_value = []
                    mock_find.return_value = mock_task

                    runner = CliRunner()
                    result = runner.invoke(
                        mark_done,
                        ["test-project/test-task"],
                        obj=Context(workspace_path=tmp_path)
                    )

                    assert result.exit_code == 0
                    assert "✅ Marked task as completed: test-project/test-task" in result.output
                    assert "Message:" not in result.output

                    mock_create.assert_called_once_with(mock_task, None)

    def test_mark_done_invalid_task_name_format(self, tmp_path: Path) -> None:
        """Test with invalid task name format."""
        runner = CliRunner()
        result = runner.invoke(
            mark_done,
            ["invalid-task-name"],
            obj=Context(workspace_path=tmp_path)
        )

        assert result.exit_code == 0  # Command doesn't exit with error code
        assert "Error: Task name must be in format 'project/task'." in result.output

    def test_mark_done_task_not_found(self, tmp_path: Path) -> None:
        """Test when task is not found."""
        with patch("warifuri.cli.commands.mark_done.discover_all_projects") as mock_discover:
            with patch("warifuri.cli.commands.mark_done.find_task_by_name") as mock_find:
                mock_discover.return_value = []
                mock_find.return_value = None

                runner = CliRunner()
                result = runner.invoke(
                    mark_done,
                    ["project/nonexistent-task"],
                    obj=Context(workspace_path=tmp_path)
                )

                assert result.exit_code == 0
                assert "Error: Task 'project/nonexistent-task' not found." in result.output

    def test_mark_done_already_completed(self, tmp_path: Path) -> None:
        """Test marking already completed task."""
        mock_task = Mock(spec=Task)
        mock_task.is_completed = True

        with patch("warifuri.cli.commands.mark_done.discover_all_projects") as mock_discover:
            with patch("warifuri.cli.commands.mark_done.find_task_by_name") as mock_find:
                mock_discover.return_value = []
                mock_find.return_value = mock_task

                runner = CliRunner()
                result = runner.invoke(
                    mark_done,
                    ["project/completed-task"],
                    obj=Context(workspace_path=tmp_path)
                )

                assert result.exit_code == 0
                assert "Task 'project/completed-task' is already completed." in result.output

    def test_mark_done_no_workspace_path(self) -> None:
        """Test when workspace path is None."""
        runner = CliRunner()

        result = runner.invoke(
            mark_done,
            ["project/task"],
            obj=Context(workspace_path=None)
        )

        # Should fail due to assertion
        assert result.exit_code != 0

    def test_mark_done_with_slash_in_task_name(self, tmp_path: Path) -> None:
        """Test with task name containing multiple slashes."""
        mock_task = Mock(spec=Task)
        mock_task.is_completed = False

        with patch("warifuri.cli.commands.mark_done.discover_all_projects") as mock_discover:
            with patch("warifuri.cli.commands.mark_done.find_task_by_name") as mock_find:
                with patch("warifuri.cli.commands.mark_done.create_done_file"):
                    mock_discover.return_value = []
                    mock_find.return_value = mock_task

                    runner = CliRunner()
                    result = runner.invoke(
                        mark_done,
                        ["project/nested/task-name"],
                        obj=Context(workspace_path=tmp_path)
                    )

                    assert result.exit_code == 0
                    assert "✅ Marked task as completed: project/nested/task-name" in result.output

                    # Verify that find_task_by_name was called with the right parameters
                    mock_find.assert_called_once_with([], "project", "nested/task-name")
