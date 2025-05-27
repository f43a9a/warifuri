"""Test run command auto-execution functionality."""

import pytest
from click.testing import CliRunner
from pathlib import Path

from warifuri.cli.main import cli
from warifuri.utils import safe_write_file, ensure_directory


class TestRunAutoExecution:
    """Test run command auto-execution features."""

    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def workspace_with_ready_tasks(self, temp_workspace):
        """Create workspace with ready and blocked tasks."""
        projects_dir = temp_workspace / "projects"

        # Project A: Ready task (no dependencies)
        project_a = projects_dir / "project-a"
        task_a1 = project_a / "ready-task"
        task_a1.mkdir(parents=True)
        safe_write_file(task_a1 / "instruction.yaml", """name: ready-task
task_type: machine
description: Ready task with no dependencies
auto_merge: false
dependencies: []
inputs: []
outputs: [result.txt]
""")
        safe_write_file(task_a1 / "run.sh", "#!/bin/bash\necho 'done' > result.txt")
        (task_a1 / "run.sh").chmod(0o755)

        # Project A: Blocked task (has dependency)
        task_a2 = project_a / "blocked-task"
        task_a2.mkdir(parents=True)
        safe_write_file(task_a2 / "instruction.yaml", """name: blocked-task
task_type: machine
description: Blocked task with dependency
auto_merge: false
dependencies: [ready-task]
inputs: [../ready-task/result.txt]
outputs: [final.txt]
""")
        safe_write_file(task_a2 / "run.sh", "#!/bin/bash\ncp ../ready-task/result.txt final.txt")
        (task_a2 / "run.sh").chmod(0o755)

        # Project B: Another ready task
        project_b = projects_dir / "project-b"
        task_b1 = project_b / "another-ready"
        task_b1.mkdir(parents=True)
        safe_write_file(task_b1 / "instruction.yaml", """name: another-ready
task_type: human
description: Another ready task
auto_merge: false
dependencies: []
inputs: []
outputs: []
""")

        return temp_workspace

    @pytest.fixture
    def workspace_with_completed_task(self, temp_workspace):
        """Create workspace with completed task."""
        projects_dir = temp_workspace / "projects"

        # Project with completed task
        project = projects_dir / "completed-project"
        task = project / "completed-task"
        task.mkdir(parents=True)
        safe_write_file(task / "instruction.yaml", """name: completed-task
task_type: machine
description: Already completed task
auto_merge: false
dependencies: []
inputs: []
outputs: [output.txt]
""")
        safe_write_file(task / "run.sh", "#!/bin/bash\necho 'output' > output.txt")
        (task / "run.sh").chmod(0o755)

        # Mark as completed
        safe_write_file(task / "done.md", "Task completed")

        return temp_workspace

    def test_run_auto_select_ready_task(self, runner, workspace_with_ready_tasks):
        """Test auto-selection of ready task without arguments."""
        workspace = str(workspace_with_ready_tasks)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--dry-run"
        ])

        assert result.exit_code == 0
        assert "Executing task:" in result.output
        # Should pick one of the ready tasks
        assert "project-a/ready-task" in result.output or "project-b/another-ready" in result.output
        assert "[DRY RUN]" in result.output

    def test_run_project_ready_task(self, runner, workspace_with_ready_tasks):
        """Test running ready task from specific project."""
        workspace = str(workspace_with_ready_tasks)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "project-a", "--dry-run"
        ])

        assert result.exit_code == 0
        assert "Executing task: project-a/ready-task" in result.output
        assert "[DRY RUN]" in result.output

    def test_run_specific_task(self, runner, workspace_with_ready_tasks):
        """Test running specific task."""
        workspace = str(workspace_with_ready_tasks)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "project-a/ready-task", "--dry-run"
        ])

        assert result.exit_code == 0
        assert "Executing task: project-a/ready-task" in result.output
        assert "Type: machine" in result.output
        assert "[DRY RUN]" in result.output

    def test_run_no_ready_tasks(self, runner, workspace_with_completed_task):
        """Test behavior when no ready tasks are available."""
        workspace = str(workspace_with_completed_task)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run"
        ])

        assert result.exit_code == 0
        assert "No ready tasks found." in result.output

    def test_run_nonexistent_task(self, runner, workspace_with_ready_tasks):
        """Test running non-existent task."""
        workspace = str(workspace_with_ready_tasks)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "nonexistent/task"
        ])

        assert result.exit_code == 0
        assert "Error: Task 'nonexistent/task' not found." in result.output

    def test_run_project_no_ready_tasks(self, runner, workspace_with_ready_tasks):
        """Test running ready task from project with no ready tasks."""
        workspace = str(workspace_with_ready_tasks)

        # Create project with only blocked tasks
        project_c = workspace_with_ready_tasks / "projects" / "project-c"
        task_c1 = project_c / "blocked-only"
        task_c1.mkdir(parents=True)
        safe_write_file(task_c1 / "instruction.yaml", """name: blocked-only
task_type: machine
description: Task blocked by dependency
auto_merge: false
dependencies: [nonexistent-task]
inputs: []
outputs: []
""")

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "project-c"
        ])

        assert result.exit_code == 0
        assert "No ready tasks found in project 'project-c'." in result.output

    def test_run_actual_execution(self, runner, workspace_with_ready_tasks):
        """Test actual task execution (not dry run)."""
        workspace = str(workspace_with_ready_tasks)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "project-a/ready-task"
        ])

        assert result.exit_code == 0
        assert "Executing task: project-a/ready-task" in result.output
        assert "✅ Task completed" in result.output

        # Verify done.md was created
        done_file = workspace_with_ready_tasks / "projects" / "project-a" / "ready-task" / "done.md"
        assert done_file.exists()

        # Verify output was created
        output_file = workspace_with_ready_tasks / "projects" / "project-a" / "ready-task" / "result.txt"
        assert output_file.exists()
        assert output_file.read_text().strip() == "done"

    def test_run_force_execution(self, runner, workspace_with_ready_tasks):
        """Test force execution of blocked task."""
        workspace = str(workspace_with_ready_tasks)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "project-a/blocked-task", "--force", "--dry-run"
        ])

        assert result.exit_code == 0
        assert "Executing task: project-a/blocked-task" in result.output
        assert "[DRY RUN]" in result.output

    def test_run_empty_workspace(self, runner, temp_workspace):
        """Test run command with empty workspace."""
        workspace = str(temp_workspace)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run"
        ])

        assert result.exit_code == 0
        assert "No projects found in workspace." in result.output

    def test_run_with_environment_variables(self, runner, workspace_with_ready_tasks):
        """Test that environment variables are set during execution."""
        workspace = str(workspace_with_ready_tasks)

        # Create a task that checks environment variables
        project = workspace_with_ready_tasks / "projects" / "env-test"
        task = project / "env-check"
        task.mkdir(parents=True)
        safe_write_file(task / "instruction.yaml", """name: env-check
task_type: machine
description: Check environment variables
auto_merge: false
dependencies: []
inputs: []
outputs: [env.txt]
""")
        safe_write_file(task / "run.sh", """#!/bin/bash
echo "PROJECT_NAME: $WARIFURI_PROJECT_NAME" > env.txt
echo "TASK_NAME: $WARIFURI_TASK_NAME" >> env.txt
echo "WORKSPACE_DIR: $WARIFURI_WORKSPACE_DIR" >> env.txt
""")
        (task / "run.sh").chmod(0o755)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "env-test/env-check"
        ])

        assert result.exit_code == 0
        assert "✅ Task completed" in result.output

        # Check environment variables were set
        env_file = task / "env.txt"
        assert env_file.exists()
        env_content = env_file.read_text()
        assert "PROJECT_NAME: env-test" in env_content
        assert "TASK_NAME: env-check" in env_content
        assert "WORKSPACE_DIR:" in env_content

    def test_run_ai_task_dry_run(self, runner, workspace_with_ready_tasks):
        """Test AI task execution in dry run mode."""
        workspace = str(workspace_with_ready_tasks)

        # Create AI task
        project = workspace_with_ready_tasks / "projects" / "ai-project"
        task = project / "ai-task"
        task.mkdir(parents=True)
        safe_write_file(task / "instruction.yaml", """name: ai-task
task_type: ai
description: AI task for testing
auto_merge: false
dependencies: []
inputs: []
outputs: [response.md]
""")
        safe_write_file(task / "prompt.yaml", """model: gpt-3.5-turbo
temperature: 0.7
system_prompt: "You are a helpful assistant."
""")

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "ai-project/ai-task", "--dry-run"
        ])

        assert result.exit_code == 0
        assert "Executing task: ai-project/ai-task" in result.output
        assert "Type: ai" in result.output
        assert "[DRY RUN]" in result.output

    def test_run_human_task(self, runner, workspace_with_ready_tasks):
        """Test human task execution."""
        workspace = str(workspace_with_ready_tasks)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "project-b/another-ready"
        ])

        assert result.exit_code == 0
        assert "Executing task: project-b/another-ready" in result.output
        assert "Type: human" in result.output
        assert "Human task" in result.output and "requires manual intervention" in result.output
