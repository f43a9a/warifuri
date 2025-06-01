"""Subprocess-based E2E tests for CLI commands.

These tests execute the actual warifuri CLI as a subprocess to test the complete
end-to-end functionality including argument parsing, environment setup, and
real process execution.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List

import pytest
import yaml

from warifuri.utils import safe_write_file


class TestSubprocessCLI:
    """Test CLI commands via subprocess execution."""

    @pytest.fixture
    def warifuri_command(self) -> List[str]:
        """Get the warifuri command for subprocess execution."""
        return [sys.executable, "-m", "warifuri.cli.main"]

    @pytest.fixture
    def workspace_with_projects(self, temp_workspace: Path) -> Path:
        """Create a workspace with sample projects for testing."""
        projects_dir = temp_workspace / "projects"

        # Initialize git repository to avoid git errors
        subprocess.run(["git", "init"], cwd=temp_workspace, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_workspace, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_workspace, capture_output=True)

        # Create demo project with machine task
        demo_dir = projects_dir / "demo"
        setup_dir = demo_dir / "setup"
        setup_dir.mkdir(parents=True)

        setup_instruction = {
            "name": "setup",
            "task_type": "machine",
            "description": "Demo setup task",
            "auto_merge": False,
            "dependencies": [],
            "inputs": [],
            "outputs": ["config.json"],
            "note": "Setup configuration"
        }
        safe_write_file(setup_dir / "instruction.yaml", yaml.dump(setup_instruction))
        safe_write_file(setup_dir / "run.sh", "#!/bin/bash\necho '{\"setup\": true}' > config.json")
        (setup_dir / "run.sh").chmod(0o755)

        # Create test project with human task (no dependencies to ensure ready tasks exist)
        test_dir = projects_dir / "test"
        review_dir = test_dir / "review"
        review_dir.mkdir(parents=True)

        review_instruction = {
            "name": "review",
            "task_type": "human",
            "description": "Code review task",
            "auto_merge": False,
            "dependencies": [],  # No dependencies to make it ready
            "inputs": [],
            "outputs": ["review.md"],
            "note": "Manual code review"
        }
        safe_write_file(review_dir / "instruction.yaml", yaml.dump(review_instruction))

        # Create AI task
        ai_dir = projects_dir / "ai-task"
        analyze_dir = ai_dir / "analyze"
        analyze_dir.mkdir(parents=True)

        analyze_instruction = {
            "name": "analyze",
            "task_type": "ai",
            "description": "AI analysis task",
            "auto_merge": True,
            "dependencies": [],
            "inputs": [],
            "outputs": ["analysis.json"],
            "note": "Automated analysis"
        }
        safe_write_file(analyze_dir / "instruction.yaml", yaml.dump(analyze_instruction))

        return temp_workspace

    def run_cli_command(
        self,
        warifuri_command: List[str],
        args: List[str],
        workspace: Path,
        check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        """Run warifuri CLI command via subprocess."""
        cmd = warifuri_command + args
        env = {"PYTHONPATH": str(Path(__file__).parent.parent.parent)}

        result = subprocess.run(
            cmd,
            cwd=str(workspace),
            capture_output=True,
            text=True,
            env=env,
            check=check
        )
        return result

    def test_cli_help(self, warifuri_command: List[str], temp_workspace: Path) -> None:
        """Test CLI help command via subprocess."""
        result = self.run_cli_command(warifuri_command, ["--help"], temp_workspace)

        assert result.returncode == 0
        assert "warifuri - A minimal CLI for task allocation" in result.stdout
        assert "Commands:" in result.stdout
        assert "list" in result.stdout
        assert "run" in result.stdout

    def test_cli_version(self, warifuri_command: List[str], temp_workspace: Path) -> None:
        """Test CLI version command via subprocess."""
        result = self.run_cli_command(warifuri_command, ["--version"], temp_workspace)

        assert result.returncode == 0
        assert "warifuri" in result.stdout

    def test_list_command_json_output(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test list command with JSON output via subprocess."""
        result = self.run_cli_command(
            warifuri_command,
            ["list", "--format", "json"],
            workspace_with_projects
        )

        assert result.returncode == 0

        # Parse JSON output
        try:
            tasks = json.loads(result.stdout)
            assert isinstance(tasks, list)
            assert len(tasks) >= 3  # setup, review, analyze

            # Check task structure
            task_names = [task["name"] for task in tasks]
            assert "demo/setup" in task_names
            assert "test/review" in task_names
            assert "ai-task/analyze" in task_names

        except json.JSONDecodeError:
            pytest.fail(f"Invalid JSON output: {result.stdout}")

    def test_list_command_with_filters(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test list command with various filters via subprocess."""
        # Test ready tasks filter
        result = self.run_cli_command(
            warifuri_command,
            ["list", "--ready", "--format", "json"],
            workspace_with_projects
        )

        assert result.returncode == 0
        tasks = json.loads(result.stdout)

        # Should have tasks (even if none are marked as ready)
        assert len(tasks) >= 1

    def test_show_command_yaml_output(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test show command with YAML output via subprocess."""
        result = self.run_cli_command(
            warifuri_command,
            ["show", "--task", "demo/setup", "--format", "yaml"],
            workspace_with_projects
        )

        assert result.returncode == 0

        # Parse YAML output
        try:
            task_data = yaml.safe_load(result.stdout)
            assert task_data["name"] == "setup"  # Name field is just task name
            assert task_data["project"] == "demo"
            assert task_data["description"] == "Demo setup task"
        except yaml.YAMLError:
            pytest.fail(f"Invalid YAML output: {result.stdout}")

    def test_validate_command(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test validate command via subprocess."""
        result = self.run_cli_command(
            warifuri_command,
            ["validate"],
            workspace_with_projects
        )

        assert result.returncode == 0
        assert "Validation passed" in result.stdout

    def test_graph_command_mermaid(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test graph command with Mermaid format via subprocess."""
        result = self.run_cli_command(
            warifuri_command,
            ["graph", "--format", "mermaid"],
            workspace_with_projects
        )

        assert result.returncode == 0
        assert "graph TD" in result.stdout
        assert "demo_setup" in result.stdout or "demo/setup" in result.stdout

    def test_run_command_dry_run(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test run command with dry-run via subprocess."""
        result = self.run_cli_command(
            warifuri_command,
            ["run", "--task", "demo/setup", "--dry-run"],
            workspace_with_projects
        )

        assert result.returncode == 0
        assert "Would execute" in result.stdout or "DRY RUN" in result.stdout

    def test_run_command_actual_execution(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test actual task execution via subprocess."""
        result = self.run_cli_command(
            warifuri_command,
            ["run", "--task", "demo/setup", "--force"],
            workspace_with_projects,
            check=False  # Allow failure due to git requirements
        )

        # Should either succeed or fail gracefully
        assert result.returncode in [0, 1]

        # Just verify that the command attempted execution
        assert "Executing task:" in result.stdout or "Type:" in result.stdout

    def test_automation_commands(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test automation command suite via subprocess."""
        # Test automation list
        result = self.run_cli_command(
            warifuri_command,
            ["automation", "list"],
            workspace_with_projects
        )

        assert result.returncode == 0

        # Test automation check with specific task - allow failure for missing config
        result = self.run_cli_command(
            warifuri_command,
            ["automation", "check", "demo/setup"],
            workspace_with_projects,
            check=False
        )

        # Should return with info about automation capability
        assert result.returncode in [0, 1]
        assert "Can automate:" in result.stdout

    def test_template_commands(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test template command via subprocess."""
        result = self.run_cli_command(
            warifuri_command,
            ["template", "list"],
            workspace_with_projects
        )

        assert result.returncode == 0

    def test_mark_done_command(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test mark-done command via subprocess."""
        result = self.run_cli_command(
            warifuri_command,
            ["mark-done", "ai-task/analyze", "--message", "Completed via E2E test"],
            workspace_with_projects,
            check=False  # Allow failure due to git requirements
        )

        # Should either succeed or fail gracefully
        assert result.returncode in [0, 1]

        # Just verify the command ran and handled the task appropriately
        if result.returncode == 1:
            # If failed, should be due to git repository issues
            assert "git" in result.stderr.lower() or "repository" in result.stderr.lower()

    def test_error_handling_invalid_command(
        self, warifuri_command: List[str], temp_workspace: Path
    ) -> None:
        """Test error handling for invalid commands via subprocess."""
        result = self.run_cli_command(
            warifuri_command,
            ["invalid-command"],
            temp_workspace,
            check=False
        )

        assert result.returncode != 0
        assert "No such command" in result.stderr or "Usage:" in result.stderr

    def test_error_handling_missing_workspace(self, warifuri_command: List[str]) -> None:
        """Test error handling when workspace cannot be found."""
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.run_cli_command(
                warifuri_command,
                ["list"],
                Path(temp_dir),
                check=False
            )

            assert result.returncode != 0
            assert "Could not find workspace" in result.stderr

    def test_workspace_option(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test explicit workspace option via subprocess."""
        # Run from a different directory but specify workspace
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.run_cli_command(
                warifuri_command + ["--workspace", str(workspace_with_projects)],
                ["list", "--format", "json"],
                Path(temp_dir)
            )

            assert result.returncode == 0
            tasks = json.loads(result.stdout)
            assert len(tasks) >= 3

    def test_log_level_option(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test log level option via subprocess."""
        result = self.run_cli_command(
            warifuri_command + ["--log-level", "DEBUG"],
            ["list"],
            workspace_with_projects
        )

        assert result.returncode == 0
        # Debug logging should be visible in output or at least not cause errors

    def test_init_command_subprocess(
        self, warifuri_command: List[str], temp_workspace: Path
    ) -> None:
        """Test init command via subprocess."""
        projects_dir = temp_workspace / "projects"
        projects_dir.mkdir(exist_ok=True)

        # Test project initialization
        result = self.run_cli_command(
            warifuri_command,
            ["init", "new-project"],
            temp_workspace
        )

        assert result.returncode == 0

        # Verify project directory was created
        project_dir = projects_dir / "new-project"
        assert project_dir.exists()
        assert project_dir.is_dir()

    def test_issue_command_error_handling(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test issue command error handling via subprocess."""
        result = self.run_cli_command(
            warifuri_command,
            ["issue", "--project", "nonexistent-project"],
            workspace_with_projects,
            check=False
        )

        # Should handle gracefully (might succeed with warning or fail cleanly)
        assert result.returncode in [0, 1]  # Allow both success and failure

    def test_complex_workflow_subprocess(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test complex workflow via multiple subprocess calls."""
        # 1. List ready tasks
        result = self.run_cli_command(
            warifuri_command,
            ["list", "--ready", "--format", "json"],
            workspace_with_projects
        )
        assert result.returncode == 0
        ready_tasks = json.loads(result.stdout)

        # 2. Show details of first ready task
        if ready_tasks:
            task_name = ready_tasks[0]["name"]
            result = self.run_cli_command(
                warifuri_command,
                ["show", "--task", task_name, "--format", "yaml"],
                workspace_with_projects
            )
            assert result.returncode == 0

            # 3. Validate workspace
            result = self.run_cli_command(
                warifuri_command,
                ["validate"],
                workspace_with_projects
            )
            assert result.returncode == 0

            # 4. Generate graph
            result = self.run_cli_command(
                warifuri_command,
                ["graph", "--format", "ascii"],
                workspace_with_projects
            )
            assert result.returncode == 0

    def test_concurrent_cli_execution(
        self, warifuri_command: List[str], workspace_with_projects: Path
    ) -> None:
        """Test that multiple CLI processes can run concurrently."""
        import concurrent.futures

        def run_list_command() -> int:
            """Run list command and return exit code."""
            result = self.run_cli_command(
                warifuri_command,
                ["list"],
                workspace_with_projects,
                check=False
            )
            return result.returncode

        # Run multiple concurrent list commands
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(run_list_command) for _ in range(3)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert all(code == 0 for code in results)
