"""Test machine task sandboxing and isolation features."""

import pytest
import os
import stat
from pathlib import Path
from click.testing import CliRunner

from warifuri.cli.main import cli
from warifuri.core.execution import execute_machine_task
from warifuri.core.discovery import discover_task
from warifuri.utils import safe_write_file, ensure_directory


class TestMachineSandboxing:
    """Test machine task sandboxing and isolation."""

    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def workspace_with_sandbox_tests(self, temp_workspace):
        """Create workspace with various sandboxing test scenarios."""
        projects_dir = temp_workspace / "projects" / "sandbox-test"

        # Test 1: Basic file isolation
        task1 = projects_dir / "file-isolation"
        task1.mkdir(parents=True)
        safe_write_file(task1 / "instruction.yaml", """name: file-isolation
task_type: machine
description: Test file isolation
auto_merge: false
dependencies: []
inputs: []
outputs: [result.txt]
""")
        safe_write_file(task1 / "run.sh", """#!/bin/bash
# Create file in current directory (should be temp)
echo "temp output" > result.txt
echo "Working directory: $(pwd)" > debug.txt
echo "Should not affect original task directory"
""")
        (task1 / "run.sh").chmod(0o755)

        # Test 2: Input/output handling
        task2 = projects_dir / "input-output"
        task2.mkdir(parents=True)
        safe_write_file(task2 / "instruction.yaml", """name: input-output
task_type: machine
description: Test input/output handling
auto_merge: false
dependencies: []
inputs: [input.txt]
outputs: [processed.txt, data/result.json]
""")
        safe_write_file(task2 / "input.txt", "input data")
        safe_write_file(task2 / "run.sh", """#!/bin/bash
# Process input file
if [ -f input.txt ]; then
    cat input.txt | tr '[:lower:]' '[:upper:]' > processed.txt
    mkdir -p data
    echo '{"status": "processed"}' > data/result.json
else
    echo "Input file not found" > error.txt
    exit 1
fi
""")
        (task2 / "run.sh").chmod(0o755)

        # Test 3: Environment variables
        task3 = projects_dir / "env-vars"
        task3.mkdir(parents=True)
        safe_write_file(task3 / "instruction.yaml", """name: env-vars
task_type: machine
description: Test environment variables
auto_merge: false
dependencies: []
inputs: []
outputs: [env-info.txt]
""")
        safe_write_file(task3 / "run.sh", """#!/bin/bash
echo "PROJECT_NAME: $WARIFURI_PROJECT_NAME" > env-info.txt
echo "TASK_NAME: $WARIFURI_TASK_NAME" >> env-info.txt
echo "WORKSPACE_DIR: $WARIFURI_WORKSPACE_DIR" >> env-info.txt
echo "INPUT_DIR: $WARIFURI_INPUT_DIR" >> env-info.txt
echo "OUTPUT_DIR: $WARIFURI_OUTPUT_DIR" >> env-info.txt
echo "CURRENT_DIR: $(pwd)" >> env-info.txt
""")
        (task3 / "run.sh").chmod(0o755)

        # Test 4: Error handling and logging
        task4 = projects_dir / "error-handling"
        task4.mkdir(parents=True)
        safe_write_file(task4 / "instruction.yaml", """name: error-handling
task_type: machine
description: Test error handling
auto_merge: false
dependencies: []
inputs: []
outputs: [should-not-exist.txt]
""")
        safe_write_file(task4 / "run.sh", """#!/bin/bash
echo "This script will fail"
exit 1
""")
        (task4 / "run.sh").chmod(0o755)

        # Test 5: Python script execution
        task5 = projects_dir / "python-script"
        task5.mkdir(parents=True)
        safe_write_file(task5 / "instruction.yaml", """name: python-script
task_type: machine
description: Test Python script execution
auto_merge: false
dependencies: []
inputs: []
outputs: [python-result.txt]
""")
        safe_write_file(task5 / "run.py", """#!/usr/bin/env python3
import os
import json

# Test environment variables and file operations
env_info = {
    'project': os.environ.get('WARIFURI_PROJECT_NAME'),
    'task': os.environ.get('WARIFURI_TASK_NAME'),
    'workspace': os.environ.get('WARIFURI_WORKSPACE_DIR'),
    'cwd': os.getcwd()
}

with open('python-result.txt', 'w') as f:
    f.write("Python script executed successfully\\n")
    f.write(f"Environment: {json.dumps(env_info, indent=2)}\\n")

print("Python script completed")
""")
        (task5 / "run.py").chmod(0o755)

        return temp_workspace

    def test_file_isolation(self, runner, workspace_with_sandbox_tests):
        """Test that files are created in temp directory and copied back."""
        workspace = str(workspace_with_sandbox_tests)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "sandbox-test/file-isolation"
        ])

        assert result.exit_code == 0
        assert "✅ Task completed" in result.output

        # Check that output file was copied back
        task_dir = workspace_with_sandbox_tests / "projects" / "sandbox-test" / "file-isolation"
        result_file = task_dir / "result.txt"
        assert result_file.exists()
        assert result_file.read_text().strip() == "temp output"

        # Debug file should NOT be copied back (not in outputs)
        debug_file = task_dir / "debug.txt"
        assert not debug_file.exists()

        # done.md should be created
        done_file = task_dir / "done.md"
        assert done_file.exists()

    def test_input_output_handling(self, runner, workspace_with_sandbox_tests):
        """Test input file availability and output file copying."""
        workspace = str(workspace_with_sandbox_tests)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "sandbox-test/input-output"
        ])

        assert result.exit_code == 0
        assert "✅ Task completed" in result.output

        task_dir = workspace_with_sandbox_tests / "projects" / "sandbox-test" / "input-output"

        # Check that processed output was created
        processed_file = task_dir / "processed.txt"
        assert processed_file.exists()
        assert processed_file.read_text().strip() == "INPUT DATA"

        # Check nested output directory
        nested_result = task_dir / "data" / "result.json"
        assert nested_result.exists()
        assert '"status": "processed"' in nested_result.read_text()

    def test_environment_variables(self, runner, workspace_with_sandbox_tests):
        """Test that environment variables are properly set."""
        workspace = str(workspace_with_sandbox_tests)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "sandbox-test/env-vars"
        ])

        assert result.exit_code == 0
        assert "✅ Task completed" in result.output

        task_dir = workspace_with_sandbox_tests / "projects" / "sandbox-test" / "env-vars"
        env_file = task_dir / "env-info.txt"
        assert env_file.exists()

        env_content = env_file.read_text()
        assert "PROJECT_NAME: sandbox-test" in env_content
        assert "TASK_NAME: env-vars" in env_content
        assert "WORKSPACE_DIR:" in env_content
        assert "INPUT_DIR: input" in env_content
        assert "OUTPUT_DIR: output" in env_content
        assert "CURRENT_DIR:" in env_content

    def test_error_handling_and_logging(self, runner, workspace_with_sandbox_tests):
        """Test error handling and failure logging."""
        workspace = str(workspace_with_sandbox_tests)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "sandbox-test/error-handling"
        ])

        assert result.exit_code == 1  # CLI exits with error code when task fails
        assert "❌ Task failed" in result.output

        task_dir = workspace_with_sandbox_tests / "projects" / "sandbox-test" / "error-handling"

        # done.md should NOT be created for failed tasks
        done_file = task_dir / "done.md"
        assert not done_file.exists()

        # Error log should be created
        logs_dir = task_dir / "logs"
        assert logs_dir.exists()

        log_files = list(logs_dir.glob("failed_*.log"))
        assert len(log_files) == 1

        log_content = log_files[0].read_text()
        assert "sandbox-test/error-handling" in log_content
        assert "Machine execution failed" in log_content

    def test_python_script_execution(self, runner, workspace_with_sandbox_tests):
        """Test Python script execution in sandbox."""
        workspace = str(workspace_with_sandbox_tests)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "sandbox-test/python-script"
        ])

        assert result.exit_code == 0
        assert "✅ Task completed" in result.output

        task_dir = workspace_with_sandbox_tests / "projects" / "sandbox-test" / "python-script"
        result_file = task_dir / "python-result.txt"
        assert result_file.exists()

        content = result_file.read_text()
        assert "Python script executed successfully" in content
        assert "sandbox-test" in content  # Project name in environment
        assert "python-script" in content  # Task name in environment

    def test_dry_run_no_execution(self, runner, workspace_with_sandbox_tests):
        """Test that dry run doesn't execute scripts."""
        workspace = str(workspace_with_sandbox_tests)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "sandbox-test/file-isolation", "--dry-run"
        ])

        assert result.exit_code == 0
        assert "[DRY RUN]" in result.output

        task_dir = workspace_with_sandbox_tests / "projects" / "sandbox-test" / "file-isolation"

        # No output files should be created in dry run
        result_file = task_dir / "result.txt"
        assert not result_file.exists()

        done_file = task_dir / "done.md"
        assert not done_file.exists()

    def test_bash_safety_flags(self, runner, workspace_with_sandbox_tests):
        """Test that bash is executed with safety flags."""
        projects_dir = workspace_with_sandbox_tests / "projects" / "safety-test"

        # Create task that would fail with safety flags
        task = projects_dir / "bash-safety"
        task.mkdir(parents=True)
        safe_write_file(task / "instruction.yaml", """name: bash-safety
task_type: machine
description: Test bash safety flags
auto_merge: false
dependencies: []
inputs: []
outputs: [result.txt]
""")
        safe_write_file(task / "run.sh", """#!/bin/bash
# This should fail due to undefined variable (with -u flag)
echo "Value: $UNDEFINED_VAR" > result.txt
""")
        (task / "run.sh").chmod(0o755)

        workspace = str(workspace_with_sandbox_tests)
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "safety-test/bash-safety"
        ])

        assert result.exit_code == 1  # CLI exits with error code when task fails
        assert "❌ Task failed" in result.output  # Task fails due to safety

        # Should create error log
        logs_dir = task / "logs"
        assert logs_dir.exists()
        log_files = list(logs_dir.glob("failed_*.log"))
        assert len(log_files) == 1

    def test_temp_directory_cleanup(self, temp_workspace):
        """Test that temporary directories are cleaned up."""
        # Create a simple machine task
        task_dir = temp_workspace / "projects" / "cleanup-test" / "temp-cleanup"
        task_dir.mkdir(parents=True)

        safe_write_file(task_dir / "instruction.yaml", """name: temp-cleanup
task_type: machine
description: Test temp cleanup
auto_merge: false
dependencies: []
inputs: []
outputs: [result.txt]
""")
        safe_write_file(task_dir / "run.sh", """#!/bin/bash
echo "executed" > result.txt
""")
        (task_dir / "run.sh").chmod(0o755)

        # Discover and execute task
        task = discover_task("cleanup-test", task_dir)

        # Count temp directories before execution
        import tempfile
        temp_base = Path(tempfile.gettempdir())
        before_count = len(list(temp_base.glob("warifuri_*")))

        # Execute task
        result = execute_machine_task(task, dry_run=False)
        assert result is True

        # Count temp directories after execution (should be same)
        after_count = len(list(temp_base.glob("warifuri_*")))
        assert after_count == before_count  # Temp dirs should be cleaned up

    def test_file_permissions_preservation(self, runner, workspace_with_sandbox_tests):
        """Test that file permissions are preserved in temp directory."""
        projects_dir = workspace_with_sandbox_tests / "projects" / "permission-test"

        task = projects_dir / "file-permissions"
        task.mkdir(parents=True)
        safe_write_file(task / "instruction.yaml", """name: file-permissions
task_type: machine
description: Test file permissions
auto_merge: false
dependencies: []
inputs: []
outputs: [permissions.txt]
""")
        safe_write_file(task / "run.sh", """#!/bin/bash
# Check if we can execute this script (should have +x)
if [ -x "run.sh" ]; then
    echo "Script is executable" > permissions.txt
else
    echo "Script is not executable" > permissions.txt
fi
""")
        (task / "run.sh").chmod(0o755)

        workspace = str(workspace_with_sandbox_tests)
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "permission-test/file-permissions"
        ])

        assert result.exit_code == 0
        assert "✅ Task completed" in result.output

        permissions_file = task / "permissions.txt"
        assert permissions_file.exists()
        assert "Script is executable" in permissions_file.read_text()

    def test_complex_output_structure(self, runner, workspace_with_sandbox_tests):
        """Test copying back complex directory structures."""
        projects_dir = workspace_with_sandbox_tests / "projects" / "complex-test"

        task = projects_dir / "complex-output"
        task.mkdir(parents=True)
        safe_write_file(task / "instruction.yaml", """name: complex-output
task_type: machine
description: Test complex output structure
auto_merge: false
dependencies: []
inputs: []
outputs: [data/, report.txt, logs/debug.log]
""")
        safe_write_file(task / "run.sh", """#!/bin/bash
# Create complex output structure
mkdir -p data/raw data/processed logs
echo "raw data" > data/raw/input.csv
echo "processed data" > data/processed/output.csv
echo "Summary report" > report.txt
echo "Debug information" > logs/debug.log
""")
        (task / "run.sh").chmod(0o755)

        workspace = str(workspace_with_sandbox_tests)
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "complex-test/complex-output"
        ])

        assert result.exit_code == 0
        assert "✅ Task completed" in result.output

        # Check that all outputs were copied back
        assert (task / "data" / "raw" / "input.csv").exists()
        assert (task / "data" / "processed" / "output.csv").exists()
        assert (task / "report.txt").exists()
        assert (task / "logs" / "debug.log").exists()

        # Verify content
        assert (task / "report.txt").read_text().strip() == "Summary report"

    def test_enhanced_execution_logging(self, workspace_with_sandbox_tests, runner):
        """Test enhanced execution logging functionality."""
        projects_dir = workspace_with_sandbox_tests / "projects" / "logging-test"

        # Create task with execution steps
        task = projects_dir / "logging-task"
        task.mkdir(parents=True)
        safe_write_file(task / "instruction.yaml", """name: logging-task
task_type: machine
description: Test execution logging
auto_merge: false
dependencies: []
inputs: []
outputs: [result.txt]
""")
        safe_write_file(task / "run.sh", """#!/bin/bash
echo "Starting execution"
echo "Step 1: Creating file"
echo "Hello World" > result.txt
echo "Step 2: Processing"
sleep 0.1
echo "Step 3: Finalizing"
echo "Execution completed successfully"
""")
        (task / "run.sh").chmod(0o755)

        workspace = str(workspace_with_sandbox_tests)
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "logging-test/logging-task"
        ])

        assert result.exit_code == 0
        assert "✅ Task completed" in result.output

        # Check that execution log was created
        logs_dir = task / "logs"
        assert logs_dir.exists()

        log_files = list(logs_dir.glob("execution_success_*.log"))
        assert len(log_files) > 0

        log_content = log_files[0].read_text()
        assert "Task: logging-test/logging-task" in log_content
        assert "Status: SUCCESS" in log_content
        assert "Temporary directory:" in log_content
        assert "Command: " in log_content
        assert "Exit code: 0" in log_content
        assert "STDOUT:" in log_content

    def test_input_validation_failure(self, workspace_with_sandbox_tests, runner):
        """Test input file validation failure."""
        projects_dir = workspace_with_sandbox_tests / "projects" / "validation-test"

        # Create task that requires missing input file
        task = projects_dir / "missing-input"
        task.mkdir(parents=True)
        safe_write_file(task / "instruction.yaml", """name: missing-input
task_type: machine
description: Test missing input validation
auto_merge: false
dependencies: []
inputs: [missing-file.txt]
outputs: [result.txt]
""")
        safe_write_file(task / "run.sh", """#!/bin/bash
cat missing-file.txt > result.txt
""")
        (task / "run.sh").chmod(0o755)

        workspace = str(workspace_with_sandbox_tests)
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "validation-test/missing-input"
        ])

        assert result.exit_code != 0
        assert "Input validation failed" in result.output

        # Check that failure log was created
        logs_dir = task / "logs"
        assert logs_dir.exists()

        log_files = list(logs_dir.glob("failed_*.log"))
        assert len(log_files) > 0

        log_content = log_files[0].read_text()
        assert "Missing input file: missing-file.txt" in log_content

    def test_output_validation_failure(self, workspace_with_sandbox_tests, runner):
        """Test output file validation failure."""
        projects_dir = workspace_with_sandbox_tests / "projects" / "output-validation"

        # Create task that doesn't create expected output
        task = projects_dir / "missing-output"
        task.mkdir(parents=True)
        safe_write_file(task / "instruction.yaml", """name: missing-output
task_type: machine
description: Test missing output validation
auto_merge: false
dependencies: []
inputs: []
outputs: [expected-output.txt]
""")
        safe_write_file(task / "run.sh", """#!/bin/bash
# Script doesn't create the expected output file
echo "This script runs but doesn't create the expected output"
""")
        (task / "run.sh").chmod(0o755)

        workspace = str(workspace_with_sandbox_tests)
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "output-validation/missing-output"
        ])

        assert result.exit_code != 0
        assert "Expected output files not created" in result.output or "Missing expected output" in result.output

        # Check that failure log was created
        logs_dir = task / "logs"
        assert logs_dir.exists()

        log_files = list(logs_dir.glob("failed_*.log"))
        assert len(log_files) > 0

        log_content = log_files[0].read_text()
        assert "Missing expected output: expected-output.txt" in log_content

    def test_temp_directory_security(self, workspace_with_sandbox_tests, runner):
        """Test that temporary directories have secure permissions."""
        from warifuri.utils.filesystem import create_temp_dir

        temp_dir = create_temp_dir()

        try:
            # Check permissions are owner-only (0o700)
            perms = temp_dir.stat().st_mode & 0o777
            assert perms == 0o700, f"Expected 0o700, got {oct(perms)}"
        finally:
            # Clean up
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
