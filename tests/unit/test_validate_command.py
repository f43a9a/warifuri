"""Unit tests for validate command functionality."""
from pathlib import Path
from unittest.mock import patch, Mock
from click.testing import CliRunner
from warifuri.cli.commands.validate import validate
from warifuri.core.types import Task, TaskInstruction, TaskType, TaskStatus


def test_validate_command_no_workspace():
    """Test validate command when no workspace is found."""
    runner = CliRunner()

    with patch('warifuri.cli.context.Context.ensure_workspace_path') as mock_ensure:
        mock_ensure.side_effect = Exception("No workspace found")

        result = runner.invoke(validate)

        assert result.exit_code != 0
        assert "No workspace found" in str(result.exception)


def test_validate_command_discovery_error():
    """Test validate command when project discovery fails."""
    runner = CliRunner()

    with patch('warifuri.cli.context.Context.ensure_workspace_path', return_value=Path("/workspace")), \
         patch('warifuri.cli.commands.validate.load_schema') as mock_load_schema:

        mock_load_schema.side_effect = Exception("Schema load failed")

        result = runner.invoke(validate)

        assert result.exit_code != 0
        assert "Schema load failed" in result.output


def test_validate_command_strict_mode():
    """Test validate command in strict mode."""
    runner = CliRunner()

    task = Task(
        project="test-project",
        name="test-task",
        path=Path("/tmp/test-task"),
        instruction=TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=[],
            inputs=["input.txt"],
            outputs=["output.txt"]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    mock_project = Mock()
    mock_project.name = "test-project"
    mock_project.tasks = [task]

    with patch('warifuri.cli.context.Context.ensure_workspace_path', return_value=Path("/workspace")), \
         patch('warifuri.cli.commands.validate.discover_all_projects', return_value=[mock_project]), \
         patch('warifuri.cli.commands.validate.load_schema', return_value={}), \
         patch('warifuri.cli.commands.validate.validate_instruction_yaml'), \
         patch('warifuri.cli.commands.validate.validate_file_references', return_value=[]), \
         patch('warifuri.cli.commands.validate.detect_circular_dependencies') as mock_circular:

        mock_circular.return_value = None

        result = runner.invoke(validate, ['--strict'])

        assert result.exit_code == 0
        assert "Found 1 project(s)" in result.output
        assert "✅ Validation passed" in result.output


def test_validate_command_file_validation_failure():
    """Test validate command when file validation fails."""
    runner = CliRunner()

    task = Task(
        project="test-project",
        name="test-task",
        path=Path("/tmp/test-task"),
        instruction=TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=[],
            inputs=["input.txt"],
            outputs=["output.txt"]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    mock_project = Mock()
    mock_project.name = "test-project"
    mock_project.tasks = [task]

    with patch('warifuri.cli.context.Context.ensure_workspace_path', return_value=Path("/workspace")), \
         patch('warifuri.cli.commands.validate.discover_all_projects', return_value=[mock_project]), \
         patch('warifuri.cli.commands.validate.load_schema', return_value={}), \
         patch('warifuri.cli.commands.validate.validate_instruction_yaml'), \
         patch('warifuri.cli.commands.validate.validate_file_references', return_value=["Input file not found: input.txt"]), \
         patch('warifuri.cli.commands.validate.detect_circular_dependencies', return_value=None):

        result = runner.invoke(validate)

        assert result.exit_code == 0  # File errors are warnings by default, not errors
        assert "⚠️" in result.output


def test_validate_command_dependency_validation_failure():
    """Test validate command when dependency validation fails."""
    runner = CliRunner()

    task = Task(
        project="test-project",
        name="test-task",
        path=Path("/tmp/test-task"),
        instruction=TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=["nonexistent-task"],
            inputs=["input.txt"],
            outputs=["output.txt"]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    mock_project = Mock()
    mock_project.name = "test-project"
    mock_project.tasks = [task]

    with patch('warifuri.cli.context.Context.ensure_workspace_path', return_value=Path("/workspace")), \
         patch('warifuri.cli.commands.validate.discover_all_projects', return_value=[mock_project]), \
         patch('warifuri.cli.commands.validate.load_schema', return_value={}), \
         patch('warifuri.cli.commands.validate.validate_instruction_yaml'), \
         patch('warifuri.cli.commands.validate.validate_file_references', return_value=[]), \
         patch('warifuri.cli.commands.validate.detect_circular_dependencies', return_value=["task1", "task2", "task1"]):

        result = runner.invoke(validate)

        assert result.exit_code == 1
        assert "Circular dependency" in result.output


def test_validate_command_project_filter():
    """Test validate command with project filter."""
    runner = CliRunner()

    task1 = Task(
        project="project-1",
        name="task1",
        path=Path("/tmp/task1"),
        instruction=TaskInstruction(
            name="task1",
            description="Task 1",
            dependencies=[],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    task2 = Task(
        project="project-2",
        name="task2",
        path=Path("/tmp/task2"),
        instruction=TaskInstruction(
            name="task2",
            description="Task 2",
            dependencies=[],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    mock_project1 = Mock()
    mock_project1.name = "project-1"
    mock_project1.tasks = [task1]

    mock_project2 = Mock()
    mock_project2.name = "project-2"
    mock_project2.tasks = [task2]

    with patch('warifuri.cli.context.Context.ensure_workspace_path', return_value=Path("/workspace")), \
         patch('warifuri.cli.commands.validate.discover_all_projects', return_value=[mock_project1, mock_project2]), \
         patch('warifuri.cli.commands.validate.load_schema', return_value={}), \
         patch('warifuri.cli.commands.validate.validate_instruction_yaml'), \
         patch('warifuri.cli.commands.validate.validate_file_references', return_value=[]), \
         patch('warifuri.cli.commands.validate.detect_circular_dependencies', return_value=None):

        result = runner.invoke(validate)

        assert result.exit_code == 0
        # Should validate both projects
        assert "Tasks validated: 2" in result.output


def test_validate_command_empty_projects():
    """Test validate command with no projects found."""
    runner = CliRunner()

    with patch('warifuri.cli.context.Context.ensure_workspace_path', return_value=Path("/workspace")), \
         patch('warifuri.cli.commands.validate.discover_all_projects', return_value=[]):

        result = runner.invoke(validate)

        assert result.exit_code == 0
        assert "No projects found in workspace" in result.output
