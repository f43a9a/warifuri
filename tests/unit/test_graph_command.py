from unittest.mock import Mock, patch
from pathlib import Path
from click.testing import CliRunner
from tempfile import TemporaryDirectory

from warifuri.cli.commands.graph import graph
from warifuri.core.types import Task, TaskInstruction, TaskStatus, TaskType, Project


def test_graph_command_no_projects():
    """Test graph command when no projects are found."""
    runner = CliRunner()

    with patch('warifuri.core.discovery.discover_all_projects_safe') as mock_discover:
        mock_discover.return_value = []

        result = runner.invoke(graph)

        assert result.exit_code == 0
        assert "No tasks found." in result.output


def test_graph_command_with_projects():
    """Test graph command with projects."""
    runner = CliRunner()

    task = Task(
        project="test-project",
        name="test-task",
        path=Path("test/task"),
        instruction=TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=[],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    mock_project = Mock(spec=Project)
    mock_project.tasks = [task]

    with patch('warifuri.core.discovery.discover_all_projects_safe') as mock_discover:
        mock_discover.return_value = [mock_project]

        result = runner.invoke(graph)

        assert result.exit_code == 0


def test_graph_command_dot_format():
    """Test graph command with DOT format output."""
    runner = CliRunner()

    task = Task(
        project="test-project",
        name="test-task",
        path=Path("test/task"),
        instruction=TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=[],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    mock_project = Mock(spec=Project)
    mock_project.tasks = [task]

    with patch('warifuri.core.discovery.discover_all_projects_safe') as mock_discover:
        mock_discover.return_value = [mock_project]

        result = runner.invoke(graph, ['--format', 'mermaid'])

        assert result.exit_code == 0
        assert "graph TD" in result.output


def test_create_task_node():
    """Test _create_task_node function."""
    from warifuri.cli.commands.graph import _create_task_node

    task = Task(
        project="test-project",
        name="test-task",
        path=Path("test/task"),
        instruction=TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=[],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    node = _create_task_node(task)

    assert "test-task" in node['label']
    # The label contains project/task name, not description


def test_graph_command_circular_dependency():
    """Test graph command with circular dependencies."""
    runner = CliRunner()

    task1 = Task(
        project="test-project",
        name="task1",
        path=Path("test/task1"),
        instruction=TaskInstruction(
            name="task1",
            description="Task 1",
            dependencies=["task2"],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    task2 = Task(
        project="test-project",
        name="task2",
        path=Path("test/task2"),
        instruction=TaskInstruction(
            name="task2",
            description="Task 2",
            dependencies=["task1"],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    mock_project = Mock(spec=Project)
    mock_project.tasks = [task1, task2]

    with patch('warifuri.core.discovery.discover_all_projects_safe') as mock_discover, \
         patch('warifuri.utils.validation.detect_circular_dependencies') as mock_detect:

        mock_discover.return_value = [mock_project]
        mock_detect.return_value = ["task1", "task2"]

        result = runner.invoke(graph)

        assert result.exit_code == 0
        assert "Warning: Circular dependency detected" in result.output


def test_graph_command_html_format():
    """Test graph command with HTML format output."""
    runner = CliRunner()

    task = Task(
        project="test-project",
        name="test-task",
        path=Path("test/task"),
        instruction=TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=[],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    mock_project = Mock(spec=Project)
    mock_project.tasks = [task]

    with patch('warifuri.core.discovery.discover_all_projects_safe') as mock_discover:
        mock_discover.return_value = [mock_project]

        result = runner.invoke(graph, ['--format', 'html'])

        assert result.exit_code == 0
        assert "HTML graph generated:" in result.output


def test_graph_command_html_format_with_browser():
    """Test graph command with HTML format and browser opening."""
    runner = CliRunner()

    task = Task(
        project="test-project",
        name="test-task",
        path=Path("test/task"),
        instruction=TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=[],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    mock_project = Mock(spec=Project)
    mock_project.tasks = [task]

    with patch('warifuri.core.discovery.discover_all_projects_safe') as mock_discover, \
         patch('warifuri.cli.commands.graph._open_in_browser') as mock_open:

        mock_discover.return_value = [mock_project]

        result = runner.invoke(graph, ['--format', 'html', '--web'])

        assert result.exit_code == 0
        assert mock_open.called


def test_graph_command_ready_tasks():
    """Test graph command with ready task status."""
    runner = CliRunner()

    # Create a ready task
    ready_task = Task(
        project="test-project",
        name="ready-task",
        path=Path("test/ready-task"),
        instruction=TaskInstruction(
            name="ready-task",
            description="Ready task",
            dependencies=[],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.READY
    )

    mock_project = Mock(spec=Project)
    mock_project.tasks = [ready_task]

    with patch('warifuri.core.discovery.discover_all_projects_safe') as mock_discover:
        mock_discover.return_value = [mock_project]

        result = runner.invoke(graph)

        assert result.exit_code == 0
        assert "🔄" in result.output  # Ready task icon


def test_graph_command_completed_tasks():
    """Test graph command with completed task status."""
    runner = CliRunner()

    with TemporaryDirectory() as temp_dir:
        task_path = Path(temp_dir) / "completed-task"
        task_path.mkdir(parents=True, exist_ok=True)
        # Create done.md to mark task as completed
        (task_path / "done.md").write_text("Task completed")

        # Create a completed task
        completed_task = Task(
            project="test-project",
            name="completed-task",
            path=task_path,
            instruction=TaskInstruction(
                name="completed-task",
                description="Completed task",
                dependencies=[],
                inputs=[],
                outputs=[]
            ),
            task_type=TaskType.HUMAN,
            status=TaskStatus.COMPLETED
        )

        mock_project = Mock(spec=Project)
        mock_project.tasks = [completed_task]

        with patch('warifuri.core.discovery.discover_all_projects_safe') as mock_discover:
            mock_discover.return_value = [mock_project]

            result = runner.invoke(graph)

            assert result.exit_code == 0
            assert "✅" in result.output  # Completed task icon


def test_create_task_node_ready_status():
    """Test _create_task_node function with ready status."""
    from warifuri.cli.commands.graph import _create_task_node

    task = Task(
        project="test-project",
        name="ready-task",
        path=Path("test/task"),
        instruction=TaskInstruction(
            name="ready-task",
            description="Ready task",
            dependencies=[],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.READY
    )

    node = _create_task_node(task)

    assert node['color'] == '#007bff'  # Blue for ready
    assert node['shape'] == 'ellipse'


def test_create_task_node_completed_status():
    """Test _create_task_node function with completed status."""
    from warifuri.cli.commands.graph import _create_task_node

    with TemporaryDirectory() as temp_dir:
        task_path = Path(temp_dir) / "completed-task"
        task_path.mkdir(parents=True, exist_ok=True)
        # Create done.md to mark task as completed
        (task_path / "done.md").write_text("Task completed")

        task = Task(
            project="test-project",
            name="completed-task",
            path=task_path,
            instruction=TaskInstruction(
                name="completed-task",
                description="Completed task",
                dependencies=[],
                inputs=[],
                outputs=[]
            ),
            task_type=TaskType.HUMAN,
            status=TaskStatus.COMPLETED
        )

        node = _create_task_node(task)

        assert node['color'] == '#28a745'  # Green for completed
        assert node['shape'] == 'box'


def test_graph_command_project_filter():
    """Test graph command with --project filter."""
    runner = CliRunner()

    task = Task(
        project="specific-project",
        name="specific-task",
        path=Path("specific/task"),
        instruction=TaskInstruction(
            name="specific-task",
            description="Specific task",
            dependencies=[],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    mock_project = Mock(spec=Project)
    mock_project.name = "specific-project"
    mock_project.tasks = [task]

    with patch('warifuri.core.discovery.discover_all_projects_safe') as mock_discover:
        mock_discover.return_value = [mock_project]

        result = runner.invoke(graph, ['--project', 'specific-project'])

        assert result.exit_code == 0


def test_graph_command_error_in_circular_detection():
    """Test graph command when circular dependency detection fails."""
    runner = CliRunner()

    task = Task(
        project="test-project",
        name="test-task",
        path=Path("test/task"),
        instruction=TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=[],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    mock_project = Mock(spec=Project)
    mock_project.tasks = [task]

    with patch('warifuri.core.discovery.discover_all_projects_safe') as mock_discover, \
         patch('warifuri.utils.validation.detect_circular_dependencies') as mock_detect:

        mock_discover.return_value = [mock_project]
        mock_detect.side_effect = Exception("Detection error")

        result = runner.invoke(graph)

        # Should handle error gracefully
        assert result.exit_code == 0


def test_open_in_browser_windows():
    """Test _open_in_browser on Windows."""
    from warifuri.cli.commands.graph import _open_in_browser

    with patch('os.name', 'nt'), \
         patch('platform.system', return_value='Windows'), \
         patch('os.startfile', create=True) as mock_startfile, \
         patch('click.echo') as mock_echo:

        _open_in_browser("/tmp/test.html")

        mock_startfile.assert_called_once_with("/tmp/test.html")
        mock_echo.assert_called_with("🌐 Opening graph in web browser...")


def test_open_in_browser_macos():
    """Test _open_in_browser on macOS."""
    from warifuri.cli.commands.graph import _open_in_browser

    with patch('os.name', 'posix'), \
         patch('subprocess.run') as mock_run, \
         patch('click.echo') as mock_echo:

        # Mock 'which open' returning success
        mock_run.side_effect = [
            Mock(returncode=0),  # which open
            Mock(returncode=0)   # open command
        ]

        _open_in_browser("/tmp/test.html")

        assert mock_run.call_count == 2
        mock_echo.assert_called_with("🌐 Opening graph in web browser...")


def test_open_in_browser_linux():
    """Test _open_in_browser on Linux."""
    from warifuri.cli.commands.graph import _open_in_browser

    with patch('os.name', 'posix'), \
         patch('subprocess.run') as mock_run, \
         patch('click.echo') as mock_echo:

        # Mock 'which open' failing, 'which xdg-open' succeeding
        mock_run.side_effect = [
            Mock(returncode=1),  # which open (fails)
            Mock(returncode=0),  # which xdg-open
            Mock(returncode=0)   # xdg-open command
        ]

        _open_in_browser("/tmp/test.html")

        assert mock_run.call_count == 3
        mock_echo.assert_called_with("🌐 Opening graph in web browser...")


def test_open_in_browser_environment_variable():
    """Test _open_in_browser using BROWSER environment variable."""
    from warifuri.cli.commands.graph import _open_in_browser

    with patch('os.name', 'posix'), \
         patch('subprocess.run') as mock_run, \
         patch('os.environ.get', return_value='firefox'), \
         patch('click.echo') as mock_echo:

        # Mock both open and xdg-open not available
        mock_run.side_effect = [
            Mock(returncode=1),  # which open (fails)
            Mock(returncode=1),  # which xdg-open (fails)
            Mock(returncode=0)   # firefox command
        ]

        _open_in_browser("/tmp/test.html")

        assert mock_run.call_count == 3
        mock_echo.assert_called_with("🌐 Opening graph in web browser...")


def test_open_in_browser_no_browser_available():
    """Test _open_in_browser when no browser is available."""
    from warifuri.cli.commands.graph import _open_in_browser

    with patch('os.name', 'posix'), \
         patch('subprocess.run') as mock_run, \
         patch('os.environ.get', return_value=None), \
         patch('click.echo') as mock_echo:

        # Mock all browser methods failing
        mock_run.side_effect = [
            Mock(returncode=1),  # which open (fails)
            Mock(returncode=1),  # which xdg-open (fails)
        ]

        _open_in_browser("/tmp/test.html")

        mock_echo.assert_any_call("⚠️  Could not open browser automatically: No suitable browser command found")
        mock_echo.assert_any_call("Please open manually: /tmp/test.html")


def test_open_in_browser_exception():
    """Test _open_in_browser when an exception occurs."""
    from warifuri.cli.commands.graph import _open_in_browser

    with patch('os.name', 'nt'), \
         patch('platform.system', side_effect=Exception("Platform error")), \
         patch('click.echo') as mock_echo:

        _open_in_browser("/tmp/test.html")

        mock_echo.assert_any_call("⚠️  Could not open browser automatically: Platform error")
        mock_echo.assert_any_call("Please open manually: /tmp/test.html")


def test_graph_command_circular_dependency_detection():
    """Test graph command with circular dependency detection."""
    runner = CliRunner()

    # Create tasks with circular dependencies
    task1 = Task(
        project="test-project",
        name="task1",
        path=Path("test/task1"),
        instruction=TaskInstruction(
            name="task1",
            description="Task 1",
            dependencies=["task2"],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    task2 = Task(
        project="test-project",
        name="task2",
        path=Path("test/task2"),
        instruction=TaskInstruction(
            name="task2",
            description="Task 2",
            dependencies=["task1"],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    mock_project = Mock(spec=Project)
    mock_project.tasks = [task1, task2]

    with patch('warifuri.core.discovery.discover_all_projects_safe') as mock_discover, \
         patch('warifuri.utils.validation.detect_circular_dependencies') as mock_detect, \
         patch('click.echo') as mock_echo:

        mock_discover.return_value = [mock_project]
        mock_detect.side_effect = Exception("Circular dependency detected")

        result = runner.invoke(graph)

        assert result.exit_code == 0
        mock_echo.assert_any_call("⚠️  Warning: Could not check for circular dependencies: Circular dependency detected")


def test_graph_command_status_filter_ready():
    """Test graph command shows ready tasks."""
    runner = CliRunner()

    ready_task = Task(
        project="test-project",
        name="ready-task",
        path=Path("test/ready-task"),
        instruction=TaskInstruction(
            name="ready-task",
            description="Ready task",
            dependencies=[],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.READY
    )

    mock_project = Mock(spec=Project)
    mock_project.tasks = [ready_task]

    with patch('warifuri.core.discovery.discover_all_projects_safe') as mock_discover:
        mock_discover.return_value = [mock_project]

        result = runner.invoke(graph)

        assert result.exit_code == 0
        assert "ready-task" in result.output


def test_graph_command_mermaid_format():
    """Test graph command with mermaid format."""
    runner = CliRunner()

    task = Task(
        project="test-project",
        name="test-task",
        path=Path("test/task"),
        instruction=TaskInstruction(
            name="test-task",
            description="Test task",
            dependencies=[],
            inputs=[],
            outputs=[]
        ),
        task_type=TaskType.HUMAN,
        status=TaskStatus.PENDING
    )

    mock_project = Mock(spec=Project)
    mock_project.tasks = [task]

    with patch('warifuri.core.discovery.discover_all_projects_safe') as mock_discover:
        mock_discover.return_value = [mock_project]

        result = runner.invoke(graph, ['--format', 'mermaid'])

        assert result.exit_code == 0
        assert "graph TD" in result.output  # Mermaid syntax
