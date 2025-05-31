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

    def test_validate_command_strict_mode(self, runner, workspace_with_demo):
        """Test validate command with strict mode."""
        result = runner.invoke(cli, ["--workspace", str(workspace_with_demo), "validate", "--strict"])
        assert result.exit_code == 0
        assert "Validating workspace" in result.output

    def test_validate_command_empty_workspace(self, runner, temp_workspace):
        """Test validate command with empty workspace (no projects)."""
        result = runner.invoke(cli, ["--workspace", str(temp_workspace), "validate"])
        assert result.exit_code == 0
        assert "No projects found in workspace" in result.output

    def test_validate_command_dependency_validation_error(self, runner, temp_workspace):
        """Test validate command when dependency validation throws an exception."""
        from warifuri.utils import safe_write_file
        from unittest.mock import patch

        # Create a valid project first
        demo_dir = temp_workspace / "projects" / "demo"
        task_dir = demo_dir / "valid_task"
        task_dir.mkdir(parents=True)

        instruction = """name: valid_task
task_type: machine
description: Valid task
dependencies: []
inputs: []
outputs: [output.txt]
"""
        safe_write_file(task_dir / "instruction.yaml", instruction)

        # Mock detect_circular_dependencies to raise an exception
        with patch('warifuri.cli.commands.validate.detect_circular_dependencies', side_effect=Exception("Mock dependency error")):
            result = runner.invoke(cli, ["--workspace", str(temp_workspace), "validate"])
            assert result.exit_code == 1  # Should fail due to exception
            assert "Dependency validation failed" in result.output

    def test_validate_command_file_reference_warnings(self, runner, temp_workspace):
        """Test validate command with file reference warnings (non-strict mode)."""
        from warifuri.utils import safe_write_file

        # Create a project with file reference issues
        demo_dir = temp_workspace / "projects" / "demo"
        task_dir = demo_dir / "missing_files_task"
        task_dir.mkdir(parents=True)

        # Create valid instruction.yaml but with missing input files
        instruction = """name: missing_files_task
task_type: machine
description: Task with missing input files
dependencies: []
inputs: [nonexistent_input.txt]
outputs: [output.txt]
"""
        safe_write_file(task_dir / "instruction.yaml", instruction)

        # Run without --strict to get warnings instead of errors
        result = runner.invoke(cli, ["--workspace", str(temp_workspace), "validate"])
        assert result.exit_code == 0  # Should pass with warnings
        assert "Warning" in result.output or "⚠️" in result.output

    def test_validate_command_circular_dependencies(self, runner, temp_workspace):
        """Test validate command with circular dependencies."""
        from warifuri.utils import safe_write_file

        # Create a project with circular dependencies
        demo_dir = temp_workspace / "projects" / "demo"

        # Task A depends on Task B
        task_a_dir = demo_dir / "task_a"
        task_a_dir.mkdir(parents=True)
        instruction_a = """name: task_a
task_type: machine
description: Task A that depends on B
dependencies: [task_b]
inputs: []
outputs: [output_a.txt]
"""
        safe_write_file(task_a_dir / "instruction.yaml", instruction_a)

        # Task B depends on Task A (circular)
        task_b_dir = demo_dir / "task_b"
        task_b_dir.mkdir(parents=True)
        instruction_b = """name: task_b
task_type: machine
description: Task B that depends on A
dependencies: [task_a]
inputs: []
outputs: [output_b.txt]
"""
        safe_write_file(task_b_dir / "instruction.yaml", instruction_b)

        result = runner.invoke(cli, ["--workspace", str(temp_workspace), "validate"])
        assert result.exit_code == 1  # Should fail due to circular dependency
        assert "Circular dependency" in result.output or "Validation failed" in result.output

    def test_validate_command_with_validation_errors(self, runner, temp_workspace):
        """Test validate command with validation errors."""
        from warifuri.utils import safe_write_file

        # Create a project with invalid task
        demo_dir = temp_workspace / "projects" / "demo"
        task_dir = demo_dir / "invalid_task"
        task_dir.mkdir(parents=True)

        # Create invalid instruction.yaml (missing required fields)
        invalid_instruction = """name: invalid_task
# Missing description and other required fields
"""
        safe_write_file(task_dir / "instruction.yaml", invalid_instruction)

        result = runner.invoke(cli, ["--workspace", str(temp_workspace), "validate"])
        # This should fail due to validation errors
        assert result.exit_code == 1  # click.Abort() causes exit code 1
        assert "Validation error" in result.output or "Error" in result.output

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

    def test_template_list_empty_directory(self, runner, temp_workspace):
        """Test template list with empty templates directory."""
        # Templates directory exists but is empty (default from conftest.py)
        result = runner.invoke(cli, ["--workspace", str(temp_workspace), "template", "list"])
        assert result.exit_code == 0
        assert "No templates found." in result.output

    def test_template_list_no_directory(self, runner, temp_workspace):
        """Test template list with no templates directory."""
        # Remove templates directory to test missing directory case
        templates_dir = temp_workspace / "templates"
        if templates_dir.exists():
            import shutil
            shutil.rmtree(templates_dir)

        result = runner.invoke(cli, ["--workspace", str(temp_workspace), "template", "list"])
        assert result.exit_code == 0
        assert "No templates directory found" in result.output

    def test_template_list_json_format(self, runner, temp_workspace):
        """Test template list with JSON format."""
        # Create template
        template_dir = temp_workspace / "templates" / "basic"
        template_dir.mkdir(parents=True)
        (template_dir / "task" / "instruction.yaml").parent.mkdir(parents=True)
        safe_write_file(template_dir / "task" / "instruction.yaml", "name: task\ndescription: test")

        result = runner.invoke(cli, ["--workspace", str(temp_workspace), "template", "list", "--format", "json"])
        assert result.exit_code == 0
        import json
        templates = json.loads(result.output.strip())
        assert "basic" in templates

    def test_template_list_permission_error(self, runner, temp_workspace):
        """Test template list with permission error when reading directory."""
        import os
        from unittest.mock import patch

        # Create templates directory
        templates_dir = temp_workspace / "templates"
        templates_dir.mkdir(exist_ok=True)

        # Mock Path.iterdir at the class level to raise OSError
        with patch('pathlib.Path.iterdir', side_effect=OSError("Permission denied")):
            result = runner.invoke(cli, ["--workspace", str(temp_workspace), "template", "list"])
            assert result.exit_code == 0
            assert "No templates found." in result.output

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

    def test_cli_version(self, runner):
        """Test CLI version command."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "warifuri, version" in result.output
        assert "0.2.0" in result.output
