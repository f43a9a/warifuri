"""Unit tests for init command."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from warifuri.cli.commands.init import init
from warifuri.cli.context import Context
from warifuri.utils import ensure_directory, safe_write_file


class TestInitCommand:
    """Unit tests for init command."""

    @pytest.fixture
    def runner(self):
        """Create a click test runner."""
        return CliRunner()

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            ensure_directory(workspace / "projects")
            ensure_directory(workspace / "templates")
            yield workspace

    def test_init_no_target_no_template_error(self, runner, temp_workspace):
        """Test init with no target and no template shows error."""
        # Test line 47-50: Error case when no target and no template
        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            result = runner.invoke(init, [], obj=mock_context)

            assert result.exit_code == 0
            assert (
                "Error: TARGET is required unless using --template for workspace expansion."
                in result.output
            )

    def test_create_project_template_not_found(self, runner, temp_workspace):
        """Test creating project with non-existent template."""
        # Test lines 76-79: Template not found error
        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            result = runner.invoke(
                init, ["test-project", "--template", "nonexistent"], obj=mock_context
            )

            assert result.exit_code == 0
            assert "Error: Template 'nonexistent' not found." in result.output

    def test_create_project_with_template_success(self, runner, temp_workspace):
        """Test creating project with template successfully."""
        # Test lines 82-85: Template usage message and 115-120: Task listing
        # Create a test template
        template_dir = temp_workspace / "templates" / "test-template"
        ensure_directory(template_dir / "task1")
        ensure_directory(template_dir / "task2")
        safe_write_file(
            template_dir / "task1" / "instruction.yaml", "name: task1\ntask_type: human"
        )
        safe_write_file(
            template_dir / "task2" / "instruction.yaml", "name: task2\ntask_type: human"
        )

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            with patch(
                "warifuri.cli.commands.init.get_template_variables_from_user", return_value={}
            ):
                result = runner.invoke(
                    init,
                    ["test-project", "--template", "test-template", "--non-interactive"],
                    obj=mock_context,
                )

                assert result.exit_code == 0
                assert "Using template: test-template" in result.output
                assert (
                    "Created project 'test-project' from template 'test-template'" in result.output
                )
                assert "Created tasks:" in result.output
                assert "- task1" in result.output
                assert "- task2" in result.output

    def test_create_project_template_expansion_error(self, runner, temp_workspace):
        """Test project creation with template expansion error."""
        # Test lines 94-95: Template expansion error
        template_dir = temp_workspace / "templates" / "test-template"
        ensure_directory(template_dir)
        safe_write_file(template_dir / "some_file.txt", "content")

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            with patch(
                "warifuri.cli.commands.init.get_template_variables_from_user", return_value={}
            ):
                with patch(
                    "warifuri.cli.commands.init.expand_template_directory",
                    side_effect=Exception("Template error"),
                ):
                    result = runner.invoke(
                        init,
                        ["test-project", "--template", "test-template", "--non-interactive"],
                        obj=mock_context,
                    )

                    assert result.exit_code == 0
                    assert "Error expanding template: Template error" in result.output

    def test_validate_task_creation_exists_no_force(self, runner, temp_workspace):
        """Test task validation when task exists without force flag."""
        # Test line 139: Return False from validation
        # Create existing task
        task_path = temp_workspace / "projects" / "test-project" / "existing-task"
        ensure_directory(task_path)

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            result = runner.invoke(init, ["test-project/existing-task"], obj=mock_context)

            assert result.exit_code == 0
            assert (
                "Error: Task 'test-project/existing-task' already exists. Use --force to overwrite."
                in result.output
            )

    def test_show_dry_run_task_creation_with_template(self, runner, temp_workspace):
        """Test dry run task creation with template."""
        # Test lines 142-143: Show template usage in dry run
        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            result = runner.invoke(
                init,
                ["test-project/new-task", "--dry-run", "--template", "test-template"],
                obj=mock_context,
            )

            assert result.exit_code == 0
            assert "Would create task:" in result.output
            assert "- instruction.yaml" in result.output
            assert "Using template: test-template" in result.output

    def test_create_task_from_template_success(self, runner, temp_workspace):
        """Test task creation from template successfully."""
        # Test lines 158-162: Template task creation success path
        template_dir = temp_workspace / "templates" / "task-template" / "sample-task"
        ensure_directory(template_dir)
        safe_write_file(template_dir / "instruction.yaml", "name: {{TASK_NAME}}\ntask_type: human")

        # Create project directory first
        ensure_directory(temp_workspace / "projects" / "test-project")

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            with patch(
                "warifuri.cli.commands.init.get_template_variables_from_user", return_value={}
            ):
                result = runner.invoke(
                    init,
                    [
                        "test-project/new-task",
                        "--template",
                        "task-template/sample-task",
                        "--non-interactive",
                    ],
                    obj=mock_context,
                )

                assert result.exit_code == 0
                assert "Using template: task-template/sample-task" in result.output
                assert (
                    "Created task 'test-project/new-task' from template 'task-template/sample-task'"
                    in result.output
                )

    def test_create_task_from_template_expansion_error(self, runner, temp_workspace):
        """Test task creation from template with expansion error."""
        # Test lines 168-171: Template expansion error in task creation
        template_dir = temp_workspace / "templates" / "task-template" / "sample-task"
        ensure_directory(template_dir)
        safe_write_file(template_dir / "instruction.yaml", "name: test")

        # Create project directory first
        ensure_directory(temp_workspace / "projects" / "test-project")

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            with patch(
                "warifuri.cli.commands.init.get_template_variables_from_user", return_value={}
            ):
                with patch(
                    "warifuri.cli.commands.init.expand_template_directory",
                    side_effect=Exception("Expansion failed"),
                ):
                    result = runner.invoke(
                        init,
                        [
                            "test-project/new-task",
                            "--template",
                            "task-template/sample-task",
                            "--non-interactive",
                        ],
                        obj=mock_context,
                    )

                    assert result.exit_code == 0
                    assert "Error expanding template: Expansion failed" in result.output

    def test_resolve_template_path_simple_template_single_task(self, runner, temp_workspace):
        """Test resolving template path for simple template with single task."""
        # Test lines 186, 199-200: Template resolution success and error paths
        # Create template with single task
        template_dir = temp_workspace / "templates" / "simple-template"
        task_dir = template_dir / "only-task"
        ensure_directory(task_dir)
        safe_write_file(task_dir / "instruction.yaml", "name: test")

        # Create project directory first
        ensure_directory(temp_workspace / "projects" / "test-project")

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            with patch(
                "warifuri.cli.commands.init.get_template_variables_from_user", return_value={}
            ):
                result = runner.invoke(
                    init,
                    ["test-project/new-task", "--template", "simple-template", "--non-interactive"],
                    obj=mock_context,
                )

                assert result.exit_code == 0
                assert "Using template: simple-template" in result.output

    def test_resolve_template_path_multiple_tasks_error(self, runner, temp_workspace):
        """Test resolving template path with multiple tasks shows error."""
        # Test lines 210-224: Multiple task error
        # Create template with multiple tasks
        template_dir = temp_workspace / "templates" / "multi-template"
        ensure_directory(template_dir / "task1")
        ensure_directory(template_dir / "task2")
        safe_write_file(template_dir / "task1" / "instruction.yaml", "name: task1")
        safe_write_file(template_dir / "task2" / "instruction.yaml", "name: task2")

        # Create project directory first
        ensure_directory(temp_workspace / "projects" / "test-project")

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            result = runner.invoke(
                init, ["test-project/new-task", "--template", "multi-template"], obj=mock_context
            )

            assert result.exit_code == 0
            assert (
                "Error: Template 'multi-template' contains multiple tasks. Specify as 'template/task'."
                in result.output
            )

    def test_resolve_template_path_task_not_found(self, runner, temp_workspace):
        """Test resolving template path when task not found."""
        # Test lines 227-228: Template task not found error
        # Create template but not the specific task
        template_dir = temp_workspace / "templates" / "test-template"
        ensure_directory(template_dir / "existing-task")
        safe_write_file(template_dir / "existing-task" / "instruction.yaml", "name: existing")

        # Create project directory first
        ensure_directory(temp_workspace / "projects" / "test-project")

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            result = runner.invoke(
                init,
                ["test-project/new-task", "--template", "test-template/nonexistent-task"],
                obj=mock_context,
            )

            assert result.exit_code == 0
            assert (
                "Error: Template task 'test-template/nonexistent-task' not found." in result.output
            )

    def test_expand_template_to_workspace_expansion_error(self, runner, temp_workspace):
        """Test workspace template expansion with error."""
        # Test lines 310-311: Exception handling in workspace expansion
        template_dir = temp_workspace / "templates" / "workspace-template"
        ensure_directory(template_dir)
        safe_write_file(template_dir / "some_file.txt", "content")

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            with patch(
                "warifuri.cli.commands.init.get_template_variables_from_user", return_value={}
            ):
                with patch(
                    "warifuri.cli.commands.init.expand_template_directory",
                    side_effect=Exception("Workspace expansion failed"),
                ):
                    result = runner.invoke(
                        init,
                        ["--template", "workspace-template", "--non-interactive"],
                        obj=mock_context,
                    )

                    assert result.exit_code == 0
                    assert "Error expanding template: Workspace expansion failed" in result.output

    def test_expand_template_to_workspace_dry_run(self, runner, temp_workspace):
        """Test workspace template expansion dry run."""
        # Additional test to ensure dry run path is covered
        template_dir = temp_workspace / "templates" / "workspace-template"
        ensure_directory(template_dir)
        safe_write_file(template_dir / "file1.txt", "content1")
        safe_write_file(template_dir / "subdir" / "file2.txt", "content2")

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            result = runner.invoke(
                init, ["--template", "workspace-template", "--dry-run"], obj=mock_context
            )

            assert result.exit_code == 0
            assert "Would expand template 'workspace-template' as project:" in result.output
            assert "Would create:" in result.output

    def test_expand_template_to_workspace_already_exists(self, runner, temp_workspace):
        """Test workspace template expansion when project already exists."""
        template_dir = temp_workspace / "templates" / "workspace-template"
        ensure_directory(template_dir)

        # Create existing project with same name
        existing_project = temp_workspace / "projects" / "workspace-template"
        ensure_directory(existing_project)

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            result = runner.invoke(init, ["--template", "workspace-template"], obj=mock_context)

            assert result.exit_code == 0
            assert (
                "Error: Project 'workspace-template' already exists. Use --force to overwrite."
                in result.output
            )

    def test_expand_template_to_workspace_success(self, runner, temp_workspace):
        """Test successful expansion of template to workspace."""
        # Test lines 308-311: Successful workspace template expansion
        template_dir = temp_workspace / "templates" / "test-template"
        template_dir.mkdir(parents=True)

        # Create template files
        (template_dir / "task.yaml").write_text("name: test-task\nrun: echo 'test'")
        (template_dir / "README.md").write_text("# Test Project")

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            with patch("warifuri.cli.commands.init._expand_template_to_workspace") as mock_expand:
                mock_expand.return_value = None  # Success

                result = runner.invoke(init, ["--template", "test-template"], obj=mock_context)

                assert result.exit_code == 0
                mock_expand.assert_called_once()

    def test_create_project_already_exists_no_force(self, runner, temp_workspace):
        """Test creating project when it already exists without force flag."""
        # Test lines 76-79: Project already exists error
        project_dir = temp_workspace / "projects" / "test-project"
        project_dir.mkdir(parents=True)

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            result = runner.invoke(init, ["test-project"], obj=mock_context)

            assert result.exit_code == 0
            assert (
                "Error: Project 'test-project' already exists. Use --force to overwrite."
                in result.output
            )

    def test_create_project_dry_run_with_template(self, runner, temp_workspace):
        """Test dry run for project creation with template."""
        # Test lines 82-85: Dry run display with template
        template_dir = temp_workspace / "templates" / "test-template"
        template_dir.mkdir(parents=True)
        (template_dir / "task.yaml").write_text("name: test-task")

        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            result = runner.invoke(
                init, ["test-project", "--dry-run", "--template", "test-template"], obj=mock_context
            )

            assert result.exit_code == 0
            assert "Would create project:" in result.output
            assert "Using template: test-template" in result.output

    def test_resolve_template_path_template_not_found_final(self, runner, temp_workspace):
        """Test template resolution when template not found in final check."""
        # Test lines 223-224: Final template not found error
        with patch("warifuri.cli.commands.init.Context") as mock_context_class:
            mock_context = Mock(spec=Context)
            mock_context.ensure_workspace_path.return_value = temp_workspace
            mock_context_class.return_value = mock_context

            # Test the _resolve_template_path function directly for the final check
            from warifuri.cli.commands.init import _resolve_template_path

            result = _resolve_template_path(temp_workspace, "nonexistent-template")

            assert result is None
