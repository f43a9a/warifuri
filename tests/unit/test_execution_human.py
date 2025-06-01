"""Unit tests for human task execution module."""

from unittest.mock import Mock, patch
from pathlib import Path

from warifuri.core.execution.human import execute_human_task
from warifuri.core.types import Task, TaskInstruction, TaskType, TaskStatus


class TestExecuteHumanTask:
    """Test execute_human_task function."""

    def create_mock_task(self, name: str = "test-task", description: str = "Test description") -> Task:
        """Create a mock task for testing."""
        instruction = TaskInstruction(
            name=name,
            description=description,
            dependencies=[],
            inputs=[],
            outputs=[],
            note=None
        )

        return Task(
            project="test-project",
            name=name,
            path=Path(f"/test/test-project/{name}"),
            instruction=instruction,
            task_type=TaskType.HUMAN,
            status=TaskStatus.READY
        )

    @patch("warifuri.core.execution.human.logger")
    def test_execute_human_task_normal_mode(self, mock_logger: Mock) -> None:
        """Test human task execution in normal mode."""
        task = self.create_mock_task("manual-task", "Please do this manually")

        result = execute_human_task(task, dry_run=False)

        assert result is True

        # Verify logging calls
        mock_logger.info.assert_any_call("Human task: test-project/manual-task")
        mock_logger.info.assert_any_call("Human task 'test-project/manual-task' requires manual intervention.")
        mock_logger.info.assert_any_call("Description: Please do this manually")
        mock_logger.info.assert_any_call("Please complete the task manually and run 'warifuri mark-done' when finished.")

    @patch("warifuri.core.execution.human.logger")
    def test_execute_human_task_dry_run_mode(self, mock_logger: Mock) -> None:
        """Test human task execution in dry run mode."""
        task = self.create_mock_task("manual-task", "Please do this manually")

        result = execute_human_task(task, dry_run=True)

        assert result is True

        # Verify logging calls
        mock_logger.info.assert_any_call("Human task: test-project/manual-task")
        mock_logger.info.assert_any_call("[DRY RUN] Human task requires manual intervention: test-project/manual-task")

    @patch("warifuri.core.execution.human.logger")
    def test_execute_human_task_complex_name(self, mock_logger: Mock) -> None:
        """Test human task execution with complex task name."""
        task = self.create_mock_task("complex-task-name-with-hyphens")

        result = execute_human_task(task, dry_run=False)

        assert result is True
        mock_logger.info.assert_any_call("Human task: test-project/complex-task-name-with-hyphens")

    @patch("warifuri.core.execution.human.logger")
    def test_execute_human_task_empty_description(self, mock_logger: Mock) -> None:
        """Test human task execution with empty description."""
        task = self.create_mock_task("test-task", "")

        result = execute_human_task(task, dry_run=False)

        assert result is True
        mock_logger.info.assert_any_call("Description: ")

    @patch("warifuri.core.execution.human.logger")
    def test_execute_human_task_long_description(self, mock_logger: Mock) -> None:
        """Test human task execution with long description."""
        long_description = "This is a very long description " * 10
        task = self.create_mock_task("test-task", long_description)

        result = execute_human_task(task, dry_run=False)

        assert result is True
        mock_logger.info.assert_any_call(f"Description: {long_description}")

    def test_execute_human_task_return_value(self) -> None:
        """Test that human task execution always returns True."""
        task = self.create_mock_task()

        # Normal mode
        assert execute_human_task(task, dry_run=False) is True

        # Dry run mode
        assert execute_human_task(task, dry_run=True) is True

    @patch("warifuri.core.execution.human.logger")
    def test_execute_human_task_logging_order(self, mock_logger: Mock) -> None:
        """Test the order of logging calls."""
        task = self.create_mock_task("test-task", "Test description")

        execute_human_task(task, dry_run=False)

        # Get all the info calls made to logger
        info_calls = [call.args[0] for call in mock_logger.info.call_args_list]

        # Verify the order
        assert info_calls[0] == "Human task: test-project/test-task"
        assert info_calls[1] == "Human task 'test-project/test-task' requires manual intervention."
        assert info_calls[2] == "Description: Test description"
        assert info_calls[3] == "Please complete the task manually and run 'warifuri mark-done' when finished."

    @patch("warifuri.core.execution.human.logger")
    def test_execute_human_task_dry_run_logging_order(self, mock_logger: Mock) -> None:
        """Test the order of logging calls in dry run mode."""
        task = self.create_mock_task("test-task", "Test description")

        execute_human_task(task, dry_run=True)

        # Get all the info calls made to logger
        info_calls = [call.args[0] for call in mock_logger.info.call_args_list]

        # Verify the order
        assert info_calls[0] == "Human task: test-project/test-task"
        assert info_calls[1] == "[DRY RUN] Human task requires manual intervention: test-project/test-task"

        # Should not have the additional messages in dry run mode
        assert len(info_calls) == 2
