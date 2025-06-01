"""Unit tests for machine task execution."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from warifuri.core.execution.errors import ExecutionError
from warifuri.core.execution.machine import (
    _build_execution_command,
    _find_execution_script,
    execute_machine_task,
)
from warifuri.core.types import Task, TaskInstruction, TaskStatus, TaskType


def test_build_execution_command_python():
    """Test _build_execution_command with Python script."""
    run_script = Path("/tmp/run.py")
    execution_log = []

    cmd = _build_execution_command(run_script, execution_log)

    assert cmd == ["python", "/tmp/run.py"]
    assert "Command: python /tmp/run.py" in execution_log


def test_build_execution_command_bash():
    """Test _build_execution_command with bash script."""
    run_script = Path("/tmp/run.sh")
    execution_log = []

    cmd = _build_execution_command(run_script, execution_log)

    assert cmd == ["bash", "-euo", "pipefail", "/tmp/run.sh"]
    assert "Command: bash -euo pipefail /tmp/run.sh" in execution_log


@pytest.fixture
def sample_task():
    """Create a sample task for testing."""
    return Task(
        project="test-project",
        name="test-task",
        path=Path("/tmp/test-task"),
        instruction=TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=[],
            inputs=["input.txt"],
            outputs=["output.txt"],
        ),
        task_type=TaskType.MACHINE,
        status=TaskStatus.PENDING,
    )


def test_execute_machine_task_dry_run(sample_task):
    """Test execute_machine_task with dry_run=True."""
    result = execute_machine_task(sample_task, dry_run=True)
    assert result is True


@patch("warifuri.core.execution.machine.setup_task_environment")
@patch("warifuri.core.execution.machine.validate_task_outputs")
@patch("warifuri.core.execution.core.log_failure")
@patch("warifuri.core.execution.machine.validate_task_inputs")
@patch("warifuri.core.execution.machine.copy_input_files")
@patch("warifuri.core.execution.machine.copy_directory_contents")
@patch("warifuri.core.execution.machine.safe_rmtree")
@patch("warifuri.core.execution.machine.create_temp_dir")
def test_execute_machine_task_no_script(
    mock_create_temp,
    mock_rmtree,
    mock_copy_dir,
    mock_copy_inputs,
    mock_validate_inputs,
    mock_log_failure,
    mock_validate_outputs,
    mock_setup_env,
    sample_task,
):
    """Test execute_machine_task when no execution script is found."""
    temp_dir = Path("/tmp/temp_dir")
    mock_create_temp.return_value = temp_dir
    mock_validate_inputs.return_value = True

    # Mock that no run.sh or run.py exists
    with patch("pathlib.Path.exists", return_value=False):
        result = execute_machine_task(sample_task, dry_run=False)
        assert result is False
        mock_log_failure.assert_called_once()

    # Verify cleanup was called with temp_dir
    mock_rmtree.assert_called_once_with(temp_dir)


@patch("warifuri.core.execution.machine.create_temp_dir")
@patch("warifuri.core.execution.machine.safe_rmtree")
@patch("warifuri.core.execution.machine.copy_directory_contents")
@patch("warifuri.core.execution.machine.copy_input_files")
@patch("warifuri.core.execution.machine.validate_task_inputs")
@patch("warifuri.core.execution.machine.validate_task_outputs")
@patch("warifuri.core.execution.machine.setup_task_environment")
@patch("warifuri.core.execution.machine.subprocess.run")
def test_execute_machine_task_script_failure(
    mock_subprocess,
    mock_setup_env,
    mock_validate_outputs,
    mock_validate_inputs,
    mock_copy_inputs,
    mock_copy_dir,
    mock_rmtree,
    mock_create_temp,
    sample_task,
):
    """Test execute_machine_task when script execution fails."""
    temp_dir = Path("/tmp/temp_dir")
    mock_create_temp.return_value = temp_dir
    mock_validate_inputs.return_value = True

    # Mock run.sh exists
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.side_effect = lambda path: str(path).endswith("run.sh")

        # Mock subprocess failure
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = "error output"
        mock_result.stderr = "error message"
        mock_subprocess.return_value = mock_result

        with patch("warifuri.core.execution.core.log_failure") as mock_log_failure:
            result = execute_machine_task(sample_task, dry_run=False)

            assert result is False
            mock_log_failure.assert_called_once()

    mock_rmtree.assert_called_once_with(temp_dir)


@patch("warifuri.core.execution.machine.create_temp_dir")
@patch("warifuri.core.execution.machine.safe_rmtree")
@patch("warifuri.core.execution.machine.copy_directory_contents")
@patch("warifuri.core.execution.machine.copy_input_files")
@patch("warifuri.core.execution.machine.validate_task_inputs")
@patch("warifuri.core.execution.machine.validate_task_outputs")
@patch("warifuri.core.execution.machine.setup_task_environment")
@patch("warifuri.core.execution.machine.subprocess.run")
def test_execute_machine_task_success(
    mock_subprocess,
    mock_setup_env,
    mock_validate_outputs,
    mock_validate_inputs,
    mock_copy_inputs,
    mock_copy_dir,
    mock_rmtree,
    mock_create_temp,
    sample_task,
):
    """Test successful machine task execution."""
    temp_dir = Path("/tmp/temp_dir")
    mock_create_temp.return_value = temp_dir
    mock_validate_inputs.return_value = True
    mock_validate_outputs.return_value = True

    # Mock run.sh exists
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = True

        # Mock successful subprocess
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "success output"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        with (
            patch("warifuri.core.execution.core.copy_outputs_back") as mock_copy_back,
            patch("warifuri.core.execution.core.save_execution_log") as mock_save_log,
            patch("warifuri.core.execution.core.create_done_file") as mock_create_done,
        ):
            result = execute_machine_task(sample_task, dry_run=False)

            assert result is True
            mock_copy_back.assert_called_once()
            mock_save_log.assert_called_once()
            mock_create_done.assert_called_once()

    mock_rmtree.assert_called_once_with(temp_dir)


def test_find_execution_script_run_sh():
    """Test _find_execution_script finding run.sh."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        run_sh = temp_path / "run.sh"
        run_sh.write_text("#!/bin/bash\necho 'test'")

        task = Mock()
        task.full_name = "test/task"
        execution_log = []

        script = _find_execution_script(temp_path, task, execution_log)

        assert script == run_sh
        assert "Found executable script: run.sh" in execution_log


def test_find_execution_script_run_py():
    """Test _find_execution_script finding run.py."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        run_py = temp_path / "run.py"
        run_py.write_text("print('test')")

        task = Mock()
        task.full_name = "test/task"
        execution_log = []

        script = _find_execution_script(temp_path, task, execution_log)

        assert script == run_py
        assert "Found executable script: run.py" in execution_log


def test_find_execution_script_not_found():
    """Test _find_execution_script when no script is found."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        task = Mock()
        task.full_name = "test/task"
        execution_log = []

        with pytest.raises(ExecutionError, match="No executable script found"):
            _find_execution_script(temp_path, task, execution_log)

        assert "ERROR: No executable script found in test/task" in execution_log


def test_build_execution_command_unsupported():
    """Test _build_execution_command for unsupported script type."""
    run_script = Path("/tmp/run.unknown")
    execution_log = []

    with pytest.raises(ExecutionError, match="Unsupported script type"):
        _build_execution_command(run_script, execution_log)

    assert "ERROR: Unsupported script type: /tmp/run.unknown" in execution_log


@patch("warifuri.core.execution.machine.copy_input_files")
def test_copy_input_files_exception_handling(mock_copy_inputs, sample_task):
    """Test exception handling in copy_input_files wrapper."""
    from warifuri.core.execution.machine import execute_machine_task

    temp_dir = Path("/tmp/temp_dir")

    # Mock copy_input_files to raise an exception
    mock_copy_inputs.side_effect = Exception("Copy failed")

    with (
        patch("warifuri.core.execution.machine.create_temp_dir", return_value=temp_dir),
        patch("warifuri.core.execution.machine.copy_directory_contents"),
        patch("warifuri.core.execution.machine.validate_task_inputs", return_value=True),
        patch("warifuri.core.execution.machine.safe_rmtree"),
        patch("warifuri.core.execution.core.log_failure") as mock_log_failure,
    ):
        result = execute_machine_task(sample_task, dry_run=False)
        assert result is False
        mock_log_failure.assert_called_once()


@patch("warifuri.core.execution.machine.validate_task_inputs")
def test_input_validation_failure(mock_validate_inputs, sample_task):
    """Test behavior when input validation fails."""
    mock_validate_inputs.return_value = False

    with (
        patch("warifuri.core.execution.machine.create_temp_dir") as mock_create_temp,
        patch("warifuri.core.execution.machine.copy_directory_contents"),
        patch("warifuri.core.execution.machine.copy_input_files"),
        patch("warifuri.core.execution.machine.safe_rmtree") as mock_rmtree,
        patch("warifuri.core.execution.core.log_failure") as mock_log_failure,
    ):
        temp_dir = Path("/tmp/temp_dir")
        mock_create_temp.return_value = temp_dir

        result = execute_machine_task(sample_task, dry_run=False)

        assert result is False
        mock_log_failure.assert_called_once()
        mock_rmtree.assert_called_once_with(temp_dir)


@patch("warifuri.core.execution.machine.validate_task_outputs")
def test_output_validation_failure(mock_validate_outputs, sample_task):
    """Test behavior when output validation fails."""
    temp_dir = Path("/tmp/temp_dir")

    with (
        patch("warifuri.core.execution.machine.create_temp_dir", return_value=temp_dir),
        patch("warifuri.core.execution.machine.copy_directory_contents"),
        patch("warifuri.core.execution.machine.copy_input_files"),
        patch("warifuri.core.execution.machine.validate_task_inputs", return_value=True),
        patch("warifuri.core.execution.machine.setup_task_environment"),
        patch("warifuri.core.execution.machine.subprocess.run") as mock_subprocess,
        patch("warifuri.core.execution.machine.safe_rmtree"),
        patch("warifuri.core.execution.core.copy_outputs_back"),
        patch("warifuri.core.execution.core.log_failure") as mock_log_failure,
    ):
        # Mock successful script execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "success"
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        # Mock output validation failure
        mock_validate_outputs.return_value = False

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.side_effect = lambda path: str(path).endswith("run.sh")

            result = execute_machine_task(sample_task, dry_run=False)

            assert result is False
            mock_log_failure.assert_called_once()
