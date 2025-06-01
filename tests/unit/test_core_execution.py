"""Unit tests for core execution functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from warifuri.core.execution.core import (
    copy_outputs_back,
    create_done_file,
    log_failure,
    save_execution_log,
)
from warifuri.core.types import Task, TaskInstruction, TaskStatus, TaskType


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        project="test-project",
        name="test-task",
        task_type=TaskType.MACHINE,
        path=Path("/test/project/test-task"),
        instruction=TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=[],
            inputs=["input.txt"],
            outputs=["output.txt"],
        ),
        status=TaskStatus.PENDING,
    )


@patch("warifuri.utils.filesystem.get_git_commit_sha", return_value="test123")
def test_copy_outputs_back_no_outputs(mock_git_sha, sample_task):
    """Test copy_outputs_back when task has no outputs."""
    # Modify task to have no outputs
    sample_task.instruction.outputs = []
    temp_dir = Path("/tmp/temp")
    execution_log = []

    copy_outputs_back(sample_task, temp_dir, execution_log)

    assert "No outputs to copy back" in execution_log


@patch("warifuri.utils.filesystem.get_git_commit_sha", return_value="test123")
@patch("pathlib.Path.exists")
def test_copy_outputs_back_missing_output(mock_exists, mock_git_sha, sample_task):
    """Test copy_outputs_back when output file is missing."""
    temp_dir = Path("/tmp/temp")
    execution_log = []

    # Mock output file doesn't exist
    mock_exists.return_value = False

    # This should not raise an exception, just log a warning
    copy_outputs_back(sample_task, temp_dir, execution_log)

    assert "WARNING: Expected output not found: output.txt" in execution_log
    assert "No outputs to copy back" in execution_log


@patch("warifuri.utils.filesystem.get_git_commit_sha", return_value="test123")
@patch("warifuri.core.execution.core.shutil.copy2")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.is_file")
def test_copy_outputs_back_copy_error(
    mock_is_file, mock_exists, mock_copy, mock_git_sha, sample_task
):
    """Test copy_outputs_back when copy operation fails."""
    temp_dir = Path("/tmp/temp")
    execution_log = []

    # Mock output file exists and is a file
    mock_exists.return_value = True
    mock_is_file.return_value = True
    mock_copy.side_effect = Exception("Copy failed")

    # This should raise an exception during copy
    with pytest.raises(Exception, match="Copy failed"):
        copy_outputs_back(sample_task, temp_dir, execution_log)


@patch("warifuri.utils.filesystem.get_git_commit_sha", return_value="test123")
@patch("warifuri.core.execution.core.shutil.copy2")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.mkdir")
@patch("pathlib.Path.is_file", return_value=True)
def test_copy_outputs_back_success(
    mock_is_file, mock_mkdir, mock_exists, mock_copy, mock_git_sha, sample_task
):
    """Test successful copy_outputs_back."""
    temp_dir = Path("/tmp/temp")
    execution_log = []

    # Mock output file exists
    def mock_exists_side_effect():
        # Both temp source and destination files exist
        return True

    mock_exists.side_effect = mock_exists_side_effect

    copy_outputs_back(sample_task, temp_dir, execution_log)

    mock_copy.assert_called_once()
    assert "Copied outputs: File: output.txt" in execution_log


@patch("warifuri.core.execution.core.get_git_commit_sha", return_value="test123")
@patch("warifuri.core.execution.core.datetime")
@patch("warifuri.core.execution.core.safe_write_file")
def test_save_execution_log_success(mock_safe_write, mock_datetime, mock_git_sha, sample_task):
    """Test save_execution_log with success=True."""
    # Mock datetime to have consistent timestamp
    mock_now = Mock()
    mock_now.strftime.return_value = "20240101_120000"
    mock_now.isoformat.return_value = "2024-01-01T12:00:00"
    mock_datetime.datetime.now.return_value = mock_now

    execution_log = ["Step 1", "Step 2", "Success"]

    save_execution_log(sample_task, execution_log, success=True)

    # Check that safe_write_file was called with expected args
    mock_safe_write.assert_called_once()
    call_args = mock_safe_write.call_args
    log_file_path = call_args[0][0]
    log_content = call_args[0][1]

    assert str(log_file_path).endswith("execution_success_20240101_120000.log")
    assert "SUCCESS" in log_content
    assert "test123" in log_content


@patch("warifuri.core.execution.core.get_git_commit_sha", return_value="test123")
@patch("warifuri.core.execution.core.datetime")
@patch("warifuri.core.execution.core.safe_write_file")
def test_save_execution_log_failure(mock_safe_write, mock_datetime, mock_git_sha, sample_task):
    """Test save_execution_log with success=False."""
    # Mock datetime to have consistent timestamp
    mock_now = Mock()
    mock_now.strftime.return_value = "20240101_120000"
    mock_now.isoformat.return_value = "2024-01-01T12:00:00"
    mock_datetime.datetime.now.return_value = mock_now

    execution_log = ["Step 1", "Error occurred"]

    save_execution_log(sample_task, execution_log, success=False)

    # Check that safe_write_file was called with expected args
    mock_safe_write.assert_called_once()
    call_args = mock_safe_write.call_args
    log_file_path = call_args[0][0]
    log_content = call_args[0][1]

    assert str(log_file_path).endswith("execution_failed_20240101_120000.log")
    assert "FAILED" in log_content
    assert "test123" in log_content


@patch("warifuri.core.execution.core.safe_write_file")
def test_save_execution_log_write_error(mock_safe_write, sample_task):
    """Test save_execution_log when file write fails."""
    execution_log = ["Test log"]
    mock_safe_write.side_effect = IOError("Write failed")

    # Should raise exception, not handle gracefully
    with pytest.raises(IOError, match="Write failed"):
        save_execution_log(sample_task, execution_log, success=True)


@patch("warifuri.core.execution.core.get_git_commit_sha", return_value="test123")
@patch("warifuri.core.execution.core.datetime")
@patch("warifuri.core.execution.core.safe_write_file")
def test_create_done_file_success(mock_safe_write, mock_datetime, mock_git_sha, sample_task):
    """Test successful create_done_file."""
    # Mock datetime to have consistent timestamp
    mock_now = Mock()
    mock_now.isoformat.return_value = "2024-01-01T12:00:00"
    mock_datetime.datetime.now.return_value = mock_now

    message = "Task completed successfully"

    create_done_file(sample_task, message)

    # Check that safe_write_file was called with expected args
    mock_safe_write.assert_called_once()
    call_args = mock_safe_write.call_args
    done_file_path = call_args[0][0]
    done_content = call_args[0][1]

    assert str(done_file_path).endswith("done.md")
    assert message in done_content
    assert "test123" in done_content


@patch("warifuri.core.execution.core.safe_write_file")
def test_create_done_file_write_error(mock_safe_write, sample_task):
    """Test create_done_file when file write fails."""
    message = "Task completed"
    mock_safe_write.side_effect = IOError("Write failed")

    # Should raise exception, not handle gracefully
    with pytest.raises(IOError, match="Write failed"):
        create_done_file(sample_task, message)


@patch("warifuri.core.execution.core.get_git_commit_sha", return_value="test123")
@patch("warifuri.core.execution.core.datetime")
@patch("warifuri.core.execution.core.safe_write_file")
def test_log_failure_success(mock_safe_write, mock_datetime, mock_git_sha, sample_task):
    """Test successful log_failure."""
    # Mock datetime to have consistent timestamp
    mock_now = Mock()
    mock_now.strftime.return_value = "20240101_120000"
    mock_now.isoformat.return_value = "2024-01-01T12:00:00"
    mock_datetime.datetime.now.return_value = mock_now

    error_msg = "Something went wrong"
    error_type = "ValidationError"
    execution_log = ["Step 1", "Error occurred"]

    log_failure(sample_task, error_msg, error_type, execution_log)

    # Check that safe_write_file was called with expected args
    mock_safe_write.assert_called_once()
    call_args = mock_safe_write.call_args
    log_file_path = call_args[0][0]
    log_content = call_args[0][1]

    assert str(log_file_path).endswith("failed_20240101_120000.log")
    assert "TASK EXECUTION FAILED" not in log_content  # This header doesn't exist
    assert error_msg in log_content
    assert error_type in log_content
    assert "test123" in log_content


def test_log_failure_write_error(sample_task):
    """Test log_failure when file write fails."""
    error_msg = "Something went wrong"
    error_type = "ValidationError"
    execution_log = ["Step 1"]

    with patch("builtins.open", side_effect=IOError("Write failed")):
        # Should not raise exception, just handle gracefully
        log_failure(sample_task, error_msg, error_type, execution_log)


@patch("warifuri.utils.filesystem.get_git_commit_sha", return_value="test123")
@patch("warifuri.core.execution.core.shutil.copy2")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.is_file", return_value=True)
def test_copy_outputs_back_with_subdirectories(
    mock_is_file, mock_exists, mock_copy, mock_git_sha, sample_task
):
    """Test copy_outputs_back with output files in subdirectories."""
    # Modify task to have output in subdirectory
    sample_task.instruction.outputs = ["subdir/output.txt"]
    temp_dir = Path("/tmp/temp")
    execution_log = []

    # Mock output file exists
    mock_exists.return_value = True

    with patch("pathlib.Path.mkdir") as mock_mkdir:
        copy_outputs_back(sample_task, temp_dir, execution_log)

        # Should create parent directory
        mock_mkdir.assert_called()
        mock_copy.assert_called_once()
        assert "Copied outputs: File: subdir/output.txt" in execution_log
