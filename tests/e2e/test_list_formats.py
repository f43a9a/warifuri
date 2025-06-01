"""Test list command format options."""

import json
import pytest
from click.testing import CliRunner

from warifuri.cli.main import cli
from warifuri.utils.filesystem import safe_write_file


@pytest.fixture
def list_test_workspace(temp_workspace):
    """Create a workspace with various tasks for list testing."""
    # Create project A with multiple tasks
    project_a = temp_workspace / "projects" / "project-a"

    # Ready task
    ready_task = project_a / "ready-task"
    ready_task.mkdir(parents=True)
    safe_write_file(
        ready_task / "instruction.yaml",
        """name: ready-task
task_type: machine
description: This is a ready machine task
dependencies: []
outputs: ["output.txt"]
"""
    )
    safe_write_file(ready_task / "run.sh", "#!/bin/bash\necho 'ready'")
    # Create the required input file to make task ready
    safe_write_file(ready_task / "input.txt", "test input")

    # Completed task
    completed_task = project_a / "completed-task"
    completed_task.mkdir(parents=True)
    safe_write_file(
        completed_task / "instruction.yaml",
        """name: completed-task
task_type: ai
description: This is a completed AI task
dependencies: []
"""
    )
    safe_write_file(completed_task / "prompt.yaml", "model: gpt-3.5-turbo")
    safe_write_file(completed_task / "done.md", "Task completed")

    # Pending task (depends on ready-task)
    pending_task = project_a / "pending-task"
    pending_task.mkdir(parents=True)
    safe_write_file(
        pending_task / "instruction.yaml",
        """name: pending-task
task_type: human
description: This is a pending human task
dependencies: ["ready-task"]
"""
    )

    # Create project B with one task
    project_b = temp_workspace / "projects" / "project-b"
    task_b = project_b / "task-b"
    task_b.mkdir(parents=True)
    safe_write_file(
        task_b / "instruction.yaml",
        """name: task-b
task_type: machine
description: Task in project B
dependencies: []
"""
    )
    safe_write_file(task_b / "run.sh", "#!/bin/bash\necho 'project-b'")

    return temp_workspace


class TestListFormatOptions:
    """Test list command format and filtering options."""

    def test_list_plain_format_default(self, list_test_workspace):
        """Test default plain format output."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--workspace", str(list_test_workspace),
            "list"
        ])

        assert result.exit_code == 0
        assert "[READY] project-a/ready-task" in result.output
        assert "[COMPLETED] project-a/completed-task" in result.output
        assert "[PENDING] project-a/pending-task" in result.output
        assert "[READY] project-b/task-b" in result.output
        assert "This is a ready machine task" in result.output

    def test_list_json_format(self, list_test_workspace):
        """Test JSON format output."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--workspace", str(list_test_workspace),
            "list", "--format", "json"
        ])

        assert result.exit_code == 0

        # Parse JSON output
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 4  # 4 tasks total

        # Check structure
        first_task = data[0]
        assert "name" in first_task
        assert "description" in first_task
        assert "status" in first_task

        # Find specific task
        ready_task = next(t for t in data if t["name"] == "project-a/ready-task")
        assert ready_task["status"] == "ready"
        assert ready_task["description"] == "This is a ready machine task"

    def test_list_tsv_format(self, list_test_workspace):
        """Test TSV format output."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--workspace", str(list_test_workspace),
            "list", "--format", "tsv"
        ])

        assert result.exit_code == 0

        lines = result.output.strip().split('\n')
        assert len(lines) == 5  # Header + 4 tasks

        # Check header
        headers = lines[0].split('\t')
        assert "name" in headers
        assert "description" in headers
        assert "status" in headers

        # Check data
        task_line = lines[1].split('\t')
        assert len(task_line) == len(headers)

    def test_list_ready_filter(self, list_test_workspace):
        """Test --ready filter."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--workspace", str(list_test_workspace),
            "list", "--ready"
        ])

        assert result.exit_code == 0
        assert "[READY] project-a/ready-task" in result.output
        assert "[READY] project-b/task-b" in result.output
        assert "[COMPLETED]" not in result.output
        assert "[PENDING]" not in result.output

    def test_list_completed_filter(self, list_test_workspace):
        """Test --completed filter."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--workspace", str(list_test_workspace),
            "list", "--completed"
        ])

        assert result.exit_code == 0
        assert "[COMPLETED] project-a/completed-task" in result.output
        assert "[READY]" not in result.output
        assert "[PENDING]" not in result.output

    def test_list_project_filter(self, list_test_workspace):
        """Test --project filter."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--workspace", str(list_test_workspace),
            "list", "--project", "project-a"
        ])

        assert result.exit_code == 0
        assert "project-a/ready-task" in result.output
        assert "project-a/completed-task" in result.output
        assert "project-a/pending-task" in result.output
        assert "project-b" not in result.output

    def test_list_fields_selection(self, list_test_workspace):
        """Test --fields option for custom field selection."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--workspace", str(list_test_workspace),
            "list", "--fields", "name,type,project", "--format", "json"
        ])

        assert result.exit_code == 0

        data = json.loads(result.output)
        first_task = data[0]

        # Should only have requested fields
        assert "name" in first_task
        assert "type" in first_task
        assert "project" in first_task
        # Should not have other fields
        assert "description" not in first_task
        assert "status" not in first_task

    def test_list_fields_with_plain_format(self, list_test_workspace):
        """Test --fields option with plain format."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--workspace", str(list_test_workspace),
            "list", "--fields", "name,type,dependencies"
        ])

        assert result.exit_code == 0
        assert "type:" in result.output
        assert "dependencies:" in result.output

    def test_list_combined_filters(self, list_test_workspace):
        """Test combining multiple filters."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--workspace", str(list_test_workspace),
            "list", "--ready", "--project", "project-a", "--format", "json"
        ])

        assert result.exit_code == 0

        data = json.loads(result.output)
        assert len(data) == 1  # Only one ready task in project-a
        assert data[0]["name"] == "project-a/ready-task"
        assert data[0]["status"] == "ready"

    def test_list_empty_result(self, list_test_workspace):
        """Test list with filters that return no results."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--workspace", str(list_test_workspace),
            "list", "--ready", "--project", "non-existent"
        ])

        assert result.exit_code == 0
        assert "No tasks found." in result.output

    def test_list_all_fields_json(self, list_test_workspace):
        """Test listing all available fields in JSON format."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--workspace", str(list_test_workspace),
            "list", "--fields", "name,description,status,type,dependencies,project,task",
            "--format", "json"
        ])

        assert result.exit_code == 0

        data = json.loads(result.output)
        first_task = data[0]

        # Should have all requested fields
        expected_fields = ["name", "description", "status", "type", "dependencies", "project", "task"]
        for field in expected_fields:
            assert field in first_task

    def test_list_tsv_with_custom_fields(self, list_test_workspace):
        """Test TSV format with custom fields."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--workspace", str(list_test_workspace),
            "list", "--fields", "name,status,type", "--format", "tsv"
        ])

        assert result.exit_code == 0

        lines = result.output.strip().split('\n')
        headers = lines[0].split('\t')

        assert headers == ["name", "status", "type"]

        # Check data consistency
        for line in lines[1:]:
            values = line.split('\t')
            assert len(values) == 3

    def test_list_invalid_field(self, list_test_workspace):
        """Test behavior with invalid field names."""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "--workspace", str(list_test_workspace),
            "list", "--fields", "name,invalid_field", "--format", "json"
        ])

        assert result.exit_code == 0

        data = json.loads(result.output)
        first_task = data[0]

        # Should have valid fields, invalid ones should be absent
        assert "name" in first_task
        assert "invalid_field" not in first_task
