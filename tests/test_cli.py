"""Test CLI functionality."""

import pytest
from click.testing import CliRunner
from warifuri.cli.main import cli
from warifuri.utils import safe_write_file, ensure_directory


class TestCLI:
    """Test CLI commands."""

    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def workspace_with_demo(self, temp_workspace):
        """Workspace with demo project."""
        # Create demo project
        demo_dir = temp_workspace / "projects" / "demo"
        setup_dir = demo_dir / "setup"
        setup_dir.mkdir(parents=True)

        # Create setup task
        instruction = """name: setup
task_type: machine
description: Initial project setup
auto_merge: false
dependencies: []
inputs: []
outputs:
  - config.json
note: Setup task
"""
        safe_write_file(setup_dir / "instruction.yaml", instruction)
        safe_write_file(setup_dir / "run.sh", "#!/bin/bash\necho 'Setup complete' > config.json")
        (setup_dir / "run.sh").chmod(0o755)

        return temp_workspace

    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "warifuri - A minimal CLI for task allocation" in result.output

    def test_list_command_empty_workspace(self, runner, temp_workspace):
        """Test list command with empty workspace."""
        result = runner.invoke(cli, ["--workspace", str(temp_workspace), "list"])
        assert result.exit_code == 0
        assert "No tasks found" in result.output

    def test_list_command_with_tasks(self, runner, workspace_with_demo):
        """Test list command with tasks."""
        result = runner.invoke(cli, ["--workspace", str(workspace_with_demo), "list"])
        assert result.exit_code == 0
        assert "demo/setup" in result.output
        assert "Initial project setup" in result.output

    def test_show_command(self, runner, workspace_with_demo):
        """Test show command."""
        result = runner.invoke(cli, [
            "--workspace", str(workspace_with_demo),
            "show", "--task", "demo/setup"
        ])
        assert result.exit_code == 0
        assert "Task: demo/setup" in result.output
        assert "Type: machine" in result.output

    def test_validate_command(self, runner, workspace_with_demo):
        """Test validate command."""
        result = runner.invoke(cli, ["--workspace", str(workspace_with_demo), "validate"])
        assert result.exit_code == 0
        assert "Validation passed" in result.output or "Validating workspace" in result.output

    def test_graph_command(self, runner, workspace_with_demo):
        """Test graph command."""
        result = runner.invoke(cli, ["--workspace", str(workspace_with_demo), "graph"])
        assert result.exit_code == 0
        assert "demo/setup" in result.output
        assert "no dependencies" in result.output

    def test_init_project(self, runner, temp_workspace):
        """Test project initialization."""
        result = runner.invoke(cli, [
            "--workspace", str(temp_workspace),
            "init", "test-project"
        ])
        assert result.exit_code == 0
        assert "Created project: test-project" in result.output
        assert (temp_workspace / "projects" / "test-project").exists()

    def test_init_task(self, runner, temp_workspace):
        """Test task initialization."""
        # First create project directory
        ensure_directory(temp_workspace / "projects" / "test-project")

        result = runner.invoke(cli, [
            "--workspace", str(temp_workspace),
            "init", "test-project/new-task"
        ])
        assert result.exit_code == 0
        assert "Created task: test-project/new-task" in result.output
        assert (temp_workspace / "projects" / "test-project" / "new-task" / "instruction.yaml").exists()

    def test_template_list_empty(self, runner, temp_workspace):
        """Test template list with no templates."""
        result = runner.invoke(cli, ["--workspace", str(temp_workspace), "template", "list"])
        assert result.exit_code == 0
        assert "No templates found" in result.output

    def test_template_list_with_templates(self, runner, temp_workspace):
        """Test template list with templates."""
        # Create template
        template_dir = temp_workspace / "templates" / "basic"
        template_dir.mkdir(parents=True)
        (template_dir / "task" / "instruction.yaml").parent.mkdir(parents=True)
        safe_write_file(template_dir / "task" / "instruction.yaml", "name: task\ndescription: test")

        result = runner.invoke(cli, ["--workspace", str(temp_workspace), "template", "list"])
        assert result.exit_code == 0
        assert "basic" in result.output

    def test_run_command_with_dry_run(self, runner, workspace_with_demo):
        """Test run command with dry run."""
        result = runner.invoke(cli, [
            "--workspace", str(workspace_with_demo),
            "run", "--task", "demo/setup", "--dry-run"
        ])
        assert result.exit_code == 0
        assert "[DRY RUN]" in result.output or "Would execute" in result.output
