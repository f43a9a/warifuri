"""Integration tests for complete automation workflow including error scenarios."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from warifuri.cli.main import cli
from warifuri.core.discovery import discover_all_projects, find_ready_tasks
from warifuri.core.execution import execute_task
from warifuri.core.types import TaskType, TaskStatus, Project, Task, TaskInstruction
from warifuri.utils import safe_write_file, ensure_directory


class TestAutomationWorkflowIntegration:
    """Integration tests for complete automation workflow scenarios."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def automation_workspace(self, temp_workspace):
        """Create a workspace with automation-ready tasks."""
        workspace = temp_workspace

        # Create a project with multiple automation tasks
        project_dir = workspace / "projects" / "automation-demo"  # Changed from sample-projects to projects
        ensure_directory(project_dir)

        # Machine task 1: Ready to execute
        task1_dir = project_dir / "extract-data"
        ensure_directory(task1_dir)
        safe_write_file(task1_dir / "instruction.yaml", """
name: extract-data
task_type: machine
description: Extract data from source files
dependencies: []
""")
        safe_write_file(task1_dir / "run.sh", "#!/bin/bash\necho 'Extracting data...'")
        (task1_dir / "run.sh").chmod(0o755)

        # Machine task 2: Has dependencies
        task2_dir = project_dir / "process-data"
        ensure_directory(task2_dir)
        safe_write_file(task2_dir / "instruction.yaml", """
name: process-data
task_type: machine
description: Process extracted data
dependencies:
  - automation-demo/extract-data
""")
        safe_write_file(task2_dir / "run.sh", "#!/bin/bash\necho 'Processing data...'")
        (task2_dir / "run.sh").chmod(0o755)

        # Human task
        task3_dir = project_dir / "review-results"
        ensure_directory(task3_dir)
        safe_write_file(task3_dir / "instruction.yaml", """
name: review-results
task_type: human
description: Review processed data results
dependencies:
  - automation-demo/process-data
""")

        # Create auto_merge configuration
        safe_write_file(project_dir / "auto_merge.yaml", """
auto_merge: true
merge_strategy: "rebase"
auto_delete_branch: true
""")

        return workspace

    def test_automation_discovery_workflow(self, runner, automation_workspace):
        """Test complete automation discovery workflow."""
        workspace = str(automation_workspace)

        # Test automation list command
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "automation", "list", "--format", "json"
        ])

        assert result.exit_code == 0

        # Should find automation tasks
        import json
        data = json.loads(result.output)
        assert len(data) >= 2  # At least the machine tasks

        # Check task properties
        machine_tasks = [task for task in data if task["task_type"] == "machine"]
        assert len(machine_tasks) >= 2

        # Check automation ready tasks
        automation_ready_tasks = [task for task in data if task["automation_ready"] == True]
        assert len(automation_ready_tasks) >= 2

        # Verify task structure
        extract_task = next((t for t in automation_ready_tasks if "extract-data" in t["full_name"]), None)
        assert extract_task is not None
        assert extract_task["status"] == "ready"
        assert extract_task["auto_merge_config"] is not None

    def test_automation_check_workflow(self, runner, automation_workspace):
        """Test automation check workflow for specific tasks."""
        workspace = str(automation_workspace)

        # Check a ready task
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "automation", "check", "automation-demo/extract-data"
        ])

        assert result.exit_code == 0
        assert "Can automate: ✅ Yes" in result.output

        # Check a task with dependencies
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "automation", "check", "automation-demo/process-data"
        ])

        # Should indicate dependency status
        assert result.exit_code == 0

    @patch("warifuri.cli.commands.run.execute_task")
    def test_automation_execution_workflow(self, mock_execute, runner, automation_workspace):
        """Test automation execution workflow."""
        workspace = str(automation_workspace)

        # Mock successful task execution
        mock_execute.return_value = True

        # Execute automation task
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "automation-demo/extract-data"
        ])

        assert result.exit_code == 0
        mock_execute.assert_called_once()

    def test_automation_dependency_resolution(self, runner, automation_workspace):
        """Test automation dependency resolution workflow."""
        workspace = str(automation_workspace)

        # Check task with dependencies
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "automation", "check", "automation-demo/process-data"
        ])

        assert result.exit_code == 0
        assert "Can automate:" in result.output

    def test_automation_error_handling_workflow(self, runner, automation_workspace):
        """Test automation error handling scenarios."""
        workspace = str(automation_workspace)

        # Test non-existent task
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "automation", "check", "non-existent/task"
        ])

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

        # Test invalid task format
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "automation", "check", "invalid-format"
        ])

        assert result.exit_code == 1
        assert "format" in result.output.lower()

    @patch("warifuri.cli.services.automation_service.discover_all_projects")
    def test_automation_workflow_with_mocked_discovery(self, mock_discover, runner, automation_workspace):
        """Test automation workflow with mocked discovery layer."""
        workspace = str(automation_workspace)

        # Create mock project and tasks
        mock_task = Mock(spec=Task)
        mock_task.name = "test-automation"
        mock_task.full_name = "test-project/test-automation"
        mock_task.task_type = TaskType.MACHINE
        mock_task.status = TaskStatus.READY
        mock_task.path = Path("/test/path")

        mock_instruction = Mock(spec=TaskInstruction)
        mock_instruction.description = "Test automation task"
        mock_instruction.dependencies = []
        mock_task.instruction = mock_instruction

        mock_project = Mock(spec=Project)
        mock_project.name = "test-project"
        mock_project.path = Path("/test/project")
        mock_project.tasks = [mock_task]

        mock_discover.return_value = [mock_project]

        # Test automation list with mocked data
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "automation", "list"
        ])

        assert result.exit_code == 0
        mock_discover.assert_called_once()

    def test_automation_machine_vs_human_workflow(self, runner, automation_workspace):
        """Test automation workflow distinguishes between machine and human tasks."""
        workspace = str(automation_workspace)

        # List only machine tasks
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "automation", "list", "--machine-only"
        ])

        assert result.exit_code == 0

        # Should not contain human tasks
        assert "review-results" not in result.output

        # List all tasks (should include human tasks in the output info)
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "automation", "list"
        ])

        assert result.exit_code == 0

    @patch("warifuri.cli.commands.run.execute_task")
    def test_automation_execution_error_scenarios(self, mock_execute, runner, automation_workspace):
        """Test automation execution error scenarios."""
        workspace = str(automation_workspace)

        # Mock task execution failure
        mock_execute.return_value = False

        # Execute automation task that fails
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "run", "--task", "automation-demo/extract-data"
        ])

        # Should handle failure gracefully
        assert result.exit_code == 1
        mock_execute.assert_called_once()

    def test_automation_auto_merge_config_workflow(self, runner, automation_workspace):
        """Test automation workflow with auto_merge configuration."""
        workspace = str(automation_workspace)

        # Check that auto_merge config is detected
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "automation", "list", "--format", "json"
        ])

        assert result.exit_code == 0

        import json
        data = json.loads(result.output)

        # Should have auto_merge configuration
        for task in data:
            if "automation-demo" in task["full_name"]:
                assert "auto_merge_config" in task
                assert task["auto_merge_config"] is not None

    def test_automation_ready_only_filter_workflow(self, runner, automation_workspace):
        """Test automation workflow with ready-only filter."""
        workspace = str(automation_workspace)

        # List only ready tasks
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "automation", "list", "--ready-only"
        ])

        assert result.exit_code == 0

        # Should only show ready tasks
        assert "extract-data" in result.output  # Should be ready
        # process-data might not be ready due to dependencies


class TestAutomationIntegrationEdgeCases:
    """Integration tests for automation edge cases and error conditions."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def edge_case_workspace(self, temp_workspace):
        """Create workspace with edge case scenarios."""
        workspace = temp_workspace

        # Project with circular dependencies
        project_dir = workspace / "projects" / "circular-dep"  # Changed from sample-projects to projects
        ensure_directory(project_dir)

        task1_dir = project_dir / "task1"
        ensure_directory(task1_dir)
        safe_write_file(task1_dir / "instruction.yaml", """
name: task1
task_type: machine
description: "Task 1 with circular dependency"
dependencies:
  - circular-dep/task2
""")

        task2_dir = project_dir / "task2"
        ensure_directory(task2_dir)
        safe_write_file(task2_dir / "instruction.yaml", """
name: task2
task_type: machine
description: "Task 2 with circular dependency"
dependencies:
  - circular-dep/task1
""")

        return workspace

    def test_automation_circular_dependency_handling(self, runner, edge_case_workspace):
        """Test automation handling of circular dependencies."""
        workspace = str(edge_case_workspace)

        # Should handle circular dependencies gracefully
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "automation", "list"
        ])

        # Should handle circular dependencies gracefully or detect the error
        assert result.exit_code in [0, 1]  # Allow either success with error handling or controlled failure

    def test_automation_empty_workspace_workflow(self, runner, temp_workspace):
        """Test automation workflow with empty workspace."""
        workspace = str(temp_workspace)

        # Should handle empty workspace gracefully
        result = runner.invoke(cli, [
            "--workspace", workspace,
            "automation", "list"
        ])

        assert result.exit_code == 0
        assert "No tasks found matching criteria." in result.output or result.output.strip() == "[]"

    def test_automation_malformed_yaml_handling(self, runner, temp_workspace):
        """Test automation handling of malformed YAML files."""
        workspace = temp_workspace

        # Create project with malformed YAML
        project_dir = workspace / "projects" / "malformed"  # Changed from sample-projects to projects
        ensure_directory(project_dir)

        task_dir = project_dir / "broken-task"
        ensure_directory(task_dir)
        safe_write_file(task_dir / "instruction.yaml", """
name: broken-task
task_type: machine
dependencies: [
  - unclosed-list
description: "Malformed YAML
""")

        # Should handle malformed YAML gracefully or fail with proper error
        result = runner.invoke(cli, [
            "--workspace", str(workspace),
            "automation", "list"
        ])

        # Should either succeed with error handling or fail gracefully
        assert result.exit_code in [0, 1]  # Allow both success with error handling or controlled failure
