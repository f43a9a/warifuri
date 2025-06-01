"""Test show command format options."""

import json

import pytest
import yaml
from click.testing import CliRunner

from warifuri.cli.main import cli
from warifuri.utils.filesystem import safe_write_file


@pytest.fixture
def show_test_workspace(temp_workspace):
    """Create a workspace with a detailed task for show testing."""
    project_dir = temp_workspace / "projects" / "test-project"
    task_dir = project_dir / "complex-task"
    task_dir.mkdir(parents=True)

    # Create a complex task with all fields
    safe_write_file(
        task_dir / "instruction.yaml",
        """name: complex-task
task_type: machine
description: This is a complex machine task with multiple features
dependencies:
  - "prerequisite-task"
  - "another-dep"
inputs:
  - "input_file.json"
  - "config.yaml"
outputs:
  - "result.json"
  - "report.html"
note: "This task requires special attention and careful monitoring"
auto_merge: true
""",
    )

    # Create run script
    safe_write_file(
        task_dir / "run.sh",
        """#!/bin/bash
echo "Running complex task"
""",
    )

    # Create auto_merge file
    safe_write_file(task_dir / "auto_merge.yaml", "enabled: true")

    # Create a completed task
    completed_task_dir = project_dir / "completed-task"
    completed_task_dir.mkdir(parents=True)
    safe_write_file(
        completed_task_dir / "instruction.yaml",
        """name: completed-task
task_type: ai
description: This task is already completed
dependencies: []
""",
    )
    safe_write_file(completed_task_dir / "prompt.yaml", "model: gpt-3.5-turbo")
    safe_write_file(completed_task_dir / "done.md", "2025-05-27 12:00:00 SHA: abc123")

    return temp_workspace


class TestShowFormatOptions:
    """Test show command format options."""

    def test_show_pretty_format_default(self, show_test_workspace):
        """Test default pretty format output."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--workspace",
                str(show_test_workspace),
                "show",
                "--task",
                "test-project/complex-task",
            ],
        )

        assert result.exit_code == 0
        assert "Task: test-project/complex-task" in result.output
        assert "Type: machine" in result.output
        assert "Status: ready" in result.output
        assert "This is a complex machine task" in result.output
        assert "Dependencies:" in result.output
        assert "prerequisite-task" in result.output
        assert "Inputs:" in result.output
        assert "input_file.json" in result.output
        assert "Outputs:" in result.output
        assert "result.json" in result.output
        assert "Note:" in result.output
        assert "special attention" in result.output

    def test_show_json_format(self, show_test_workspace):
        """Test JSON format output."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--workspace",
                str(show_test_workspace),
                "show",
                "--task",
                "test-project/complex-task",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0

        # Parse JSON output
        data = json.loads(result.output)

        # Verify structure and content
        assert data["name"] == "complex-task"
        assert data["project"] == "test-project"
        assert data["full_name"] == "test-project/complex-task"
        assert data["type"] == "machine"
        assert data["status"] == "ready"
        assert "complex machine task" in data["description"]
        assert data["dependencies"] == ["prerequisite-task", "another-dep"]
        assert data["inputs"] == ["input_file.json", "config.yaml"]
        assert data["outputs"] == ["result.json", "report.html"]
        assert "special attention" in data["note"]
        assert data["auto_merge"] is True
        assert data["completed"] is False

    def test_show_yaml_format(self, show_test_workspace):
        """Test YAML format output."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--workspace",
                str(show_test_workspace),
                "show",
                "--task",
                "test-project/complex-task",
                "--format",
                "yaml",
            ],
        )

        assert result.exit_code == 0

        # Parse YAML output
        data = yaml.safe_load(result.output)

        # Verify structure
        assert data["name"] == "complex-task"
        assert data["project"] == "test-project"
        assert data["type"] == "machine"
        assert data["dependencies"] == ["prerequisite-task", "another-dep"]
        assert isinstance(data["inputs"], list)
        assert isinstance(data["outputs"], list)

    def test_show_completed_task(self, show_test_workspace):
        """Test showing a completed task."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--workspace",
                str(show_test_workspace),
                "show",
                "--task",
                "test-project/completed-task",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data["name"] == "completed-task"
        assert data["status"] == "completed"
        assert data["completed"] is True
        assert data["type"] == "ai"

    def test_show_task_not_found(self, show_test_workspace):
        """Test error handling for non-existent task."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--workspace",
                str(show_test_workspace),
                "show",
                "--task",
                "test-project/non-existent",
            ],
        )

        assert result.exit_code == 0
        assert "Error: Task 'test-project/non-existent' not found" in result.output

    def test_show_invalid_task_format(self, show_test_workspace):
        """Test error handling for invalid task format."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--workspace", str(show_test_workspace), "show", "--task", "invalid-format"]
        )

        assert result.exit_code == 0
        assert "Error: Task must be in format 'project/task'" in result.output

    def test_show_minimal_task(self, show_test_workspace):
        """Test showing a task with minimal fields."""
        # Create a minimal task
        minimal_dir = show_test_workspace / "projects" / "test-project" / "minimal"
        minimal_dir.mkdir(parents=True)
        safe_write_file(
            minimal_dir / "instruction.yaml",
            """name: minimal
task_type: human
description: A minimal human task
dependencies: []
""",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--workspace",
                str(show_test_workspace),
                "show",
                "--task",
                "test-project/minimal",
                "--format",
                "json",
            ],
        )

        assert result.exit_code == 0

        data = json.loads(result.output)
        assert data["name"] == "minimal"
        assert data["type"] == "human"
        assert data["dependencies"] == []
        # Minimal task should have empty or minimal lists
        assert data["inputs"] in [[], None]
        assert data["outputs"] in [[], None]

    def test_show_pretty_format_with_empty_lists(self, show_test_workspace):
        """Test pretty format with empty dependency/input/output lists."""
        # Create task with empty lists
        empty_dir = show_test_workspace / "projects" / "test-project" / "empty-lists"
        empty_dir.mkdir(parents=True)
        safe_write_file(
            empty_dir / "instruction.yaml",
            """name: empty-lists
task_type: human
description: Task with explicitly empty lists
dependencies: []
inputs: []
outputs: []
note: ""
""",
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--workspace", str(show_test_workspace), "show", "--task", "test-project/empty-lists"],
        )

        assert result.exit_code == 0
        assert "Task: test-project/empty-lists" in result.output
        assert "Dependencies:" not in result.output  # Should not show empty sections
        assert "Inputs:" not in result.output
        assert "Outputs:" not in result.output
        assert "Note:" not in result.output  # Empty note should not show

    def test_show_all_formats_consistency(self, show_test_workspace):
        """Test that all formats return consistent data."""
        runner = CliRunner()

        # Get data in all formats
        json_result = runner.invoke(
            cli,
            [
                "--workspace",
                str(show_test_workspace),
                "show",
                "--task",
                "test-project/complex-task",
                "--format",
                "json",
            ],
        )

        yaml_result = runner.invoke(
            cli,
            [
                "--workspace",
                str(show_test_workspace),
                "show",
                "--task",
                "test-project/complex-task",
                "--format",
                "yaml",
            ],
        )

        pretty_result = runner.invoke(
            cli,
            [
                "--workspace",
                str(show_test_workspace),
                "show",
                "--task",
                "test-project/complex-task",
                "--format",
                "pretty",
            ],
        )

        assert json_result.exit_code == 0
        assert yaml_result.exit_code == 0
        assert pretty_result.exit_code == 0

        # Parse structured formats
        json_data = json.loads(json_result.output)
        yaml_data = yaml.safe_load(yaml_result.output)

        # Key fields should be consistent
        assert json_data["name"] == yaml_data["name"]
        assert json_data["type"] == yaml_data["type"]
        assert json_data["description"] == yaml_data["description"]
        assert json_data["dependencies"] == yaml_data["dependencies"]

        # Pretty format should contain the same key information
        assert json_data["name"] in pretty_result.output
        assert json_data["type"] in pretty_result.output
        assert json_data["description"] in pretty_result.output
