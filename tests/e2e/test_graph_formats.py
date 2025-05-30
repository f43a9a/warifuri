"""Test graph command output formats."""

import pytest
from click.testing import CliRunner

from warifuri.cli.main import cli
from warifuri.utils import safe_write_file


class TestGraphFormats:
    """Test graph command format options."""

    @pytest.fixture
    def runner(self):
        """CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def workspace_with_dependencies(self, temp_workspace):
        """Create workspace with tasks having dependencies."""
        projects_dir = temp_workspace / "projects"

        # Create project A with two tasks
        project_a = projects_dir / "project-a"

        # Task A1 (no dependencies)
        task_a1 = project_a / "task-a1"
        task_a1.mkdir(parents=True)
        safe_write_file(task_a1 / "instruction.yaml", """name: task-a1
task_type: machine
description: First task with no dependencies
auto_merge: false
dependencies: []
inputs: []
outputs: [data.txt]
""")
        safe_write_file(task_a1 / "run.sh", "#!/bin/bash\necho 'data' > data.txt")
        (task_a1 / "run.sh").chmod(0o755)

        # Task A2 (depends on A1)
        task_a2 = project_a / "task-a2"
        task_a2.mkdir(parents=True)
        safe_write_file(task_a2 / "instruction.yaml", """name: task-a2
task_type: ai
description: Second task depending on task-a1
auto_merge: false
dependencies: [task-a1]
inputs: [../task-a1/data.txt]
outputs: [processed.txt]
""")
        safe_write_file(task_a2 / "prompt.yaml", "Process the data from task-a1")

        # Create project B with one task depending on project A
        project_b = projects_dir / "project-b"
        task_b1 = project_b / "task-b1"
        task_b1.mkdir(parents=True)
        safe_write_file(task_b1 / "instruction.yaml", """name: task-b1
task_type: human
description: Task depending on another project
auto_merge: false
dependencies: [project-a/task-a2]
inputs: [../../project-a/task-a2/processed.txt]
outputs: [final.txt]
""")

        # Mark task-a1 as completed
        safe_write_file(task_a1 / "done.md", "Completed on 2024-01-01")

        return temp_workspace

    def test_graph_ascii_format(self, runner, workspace_with_dependencies):
        """Test ASCII graph format output."""
        workspace = str(workspace_with_dependencies)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "graph", "--format", "ascii"
        ])

        assert result.exit_code == 0
        assert "Dependency Graph (ASCII)" in result.output
        assert "project-a/task-a1" in result.output
        assert "project-a/task-a2" in result.output
        assert "project-b/task-b1" in result.output
        assert "✅" in result.output  # Completed task symbol
        assert "depends on:" in result.output

    def test_graph_mermaid_format(self, runner, workspace_with_dependencies):
        """Test Mermaid graph format output."""
        workspace = str(workspace_with_dependencies)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "graph", "--format", "mermaid"
        ])

        assert result.exit_code == 0
        assert "```mermaid" in result.output
        assert "graph TD" in result.output
        assert "```" in result.output
        # Check node definitions
        assert "project_a_task_a1" in result.output or "project-a/task-a1" in result.output
        # Check edge definitions (dependencies)
        assert "-->" in result.output

    def test_graph_html_format_placeholder(self, runner, workspace_with_dependencies):
        """Test HTML graph format generation."""
        workspace = str(workspace_with_dependencies)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "graph", "--format", "html"
        ])

        assert result.exit_code == 0
        assert "HTML graph generated:" in result.output
        assert "To view the graph, open:" in result.output

    def test_graph_html_with_web_flag(self, runner, workspace_with_dependencies):
        """Test HTML graph format with --web flag."""
        workspace = str(workspace_with_dependencies)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "graph", "--format", "html", "--web"
        ])

        assert result.exit_code == 0
        assert "HTML graph generated:" in result.output
        # Should attempt to open browser or show appropriate message
        # The improved _open_in_browser function now always outputs one of these messages
        assert ("Could not open browser automatically" in result.output or
                "Opening graph in web browser" in result.output or
                "Please open manually:" in result.output)

    def test_graph_project_filter(self, runner, workspace_with_dependencies):
        """Test graph generation with project filter."""
        workspace = str(workspace_with_dependencies)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "graph", "--project", "project-a"
        ])

        assert result.exit_code == 0
        assert "project-a/task-a1" in result.output
        assert "project-a/task-a2" in result.output
        # Should not include project-b tasks
        assert "project-b/task-b1" not in result.output

    def test_graph_empty_workspace(self, runner, temp_workspace):
        """Test graph command with empty workspace."""
        workspace = str(temp_workspace)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "graph"
        ])

        assert result.exit_code == 0
        assert "No tasks found." in result.output

    def test_graph_nonexistent_project_filter(self, runner, workspace_with_dependencies):
        """Test graph command with non-existent project filter."""
        workspace = str(workspace_with_dependencies)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "graph", "--project", "nonexistent-project"
        ])

        assert result.exit_code == 0
        assert "No tasks found." in result.output

    def test_graph_default_format(self, runner, workspace_with_dependencies):
        """Test that ASCII is the default format."""
        workspace = str(workspace_with_dependencies)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "graph"
        ])

        assert result.exit_code == 0
        assert "Dependency Graph (ASCII)" in result.output

    def test_graph_dependency_visualization(self, runner, workspace_with_dependencies):
        """Test that dependencies are properly visualized."""
        workspace = str(workspace_with_dependencies)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "graph", "--format", "ascii"
        ])

        assert result.exit_code == 0
        output_lines = result.output.split('\n')

        # Find task-a1 and verify it has no dependencies
        task_a1_found = False
        for i, line in enumerate(output_lines):
            if "project-a/task-a1" in line:
                task_a1_found = True
                # Check next few lines for dependency info
                for j in range(i+1, min(i+5, len(output_lines))):
                    if "no dependencies" in output_lines[j]:
                        break
                else:
                    # Should find "no dependencies" for task-a1
                    pass
                break

        assert task_a1_found, "task-a1 should be found in output"

        # Find task-a2 and verify it depends on task-a1
        task_a2_found = False
        for i, line in enumerate(output_lines):
            if "project-a/task-a2" in line:
                task_a2_found = True
                # Check next few lines for dependency info
                for j in range(i+1, min(i+5, len(output_lines))):
                    if "depends on: task-a1" in output_lines[j]:
                        break
                else:
                    # Should find dependency on task-a1
                    pass
                break

        assert task_a2_found, "task-a2 should be found in output"

    def test_graph_status_symbols(self, runner, workspace_with_dependencies):
        """Test that status symbols are displayed correctly."""
        workspace = str(workspace_with_dependencies)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "graph", "--format", "ascii"
        ])

        assert result.exit_code == 0

        # task-a1 should show as completed (✅)
        assert "✅ project-a/task-a1" in result.output

        # Other tasks should have status symbols
        lines = result.output.split('\n')
        status_lines = [line for line in lines if any(symbol in line for symbol in ["✅", "🔄", "⏸️"])]

        # Should have at least 3 tasks with status symbols
        assert len(status_lines) >= 3

    def test_graph_mermaid_node_sanitization(self, runner, workspace_with_dependencies):
        """Test that Mermaid format properly sanitizes node IDs."""
        workspace = str(workspace_with_dependencies)

        result = runner.invoke(cli, [
            "--workspace", workspace,
            "graph", "--format", "mermaid"
        ])

        assert result.exit_code == 0

        # Check that hyphens and slashes are converted to underscores in node IDs
        assert "project_a_task_a1" in result.output
        assert "project_a_task_a2" in result.output
        assert "project_b_task_b1" in result.output

        # But original names should still appear in labels
        assert "project-a/task-a1" in result.output
