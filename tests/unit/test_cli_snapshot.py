"""Snapshot tests for CLI output consistency.

This module contains snapshot tests that verify CLI output format
remains consistent across changes. These tests help detect unintended
changes to user-facing output.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from snapshottest import TestCase  # type: ignore


class TestCliSnapshotOutput(TestCase):
    """CLI出力のスナップショットテスト"""

    def setUp(self) -> None:
        """各テストの前に実行される設定"""
        self.temp_dir = tempfile.mkdtemp()
        self.workspace_path = Path(self.temp_dir) / "test_workspace"
        self.workspace_path.mkdir(parents=True, exist_ok=True)

        # 基本的なworkspace構造を作成
        (self.workspace_path / "tasks").mkdir(exist_ok=True)
        (self.workspace_path / "projects").mkdir(exist_ok=True)

        # サンプルタスクを作成
        task_dir = self.workspace_path / "tasks" / "sample-task"
        task_dir.mkdir(parents=True, exist_ok=True)

        # task.yaml
        (task_dir / "task.yaml").write_text("""
title: "Sample Task"
description: "A simple sample task for testing"
type: "manual"
status: "todo"
tags: ["testing", "sample"]
inputs: []
outputs: []
""")

        # done.md (completed task)
        completed_task_dir = self.workspace_path / "tasks" / "completed-task"
        completed_task_dir.mkdir(parents=True, exist_ok=True)
        (completed_task_dir / "task.yaml").write_text("""
title: "Completed Task"
description: "A completed task for testing"
type: "manual"
status: "done"
tags: ["testing", "completed"]
inputs: []
outputs: []
""")
        (completed_task_dir / "done.md").write_text("# Task Completed\n\nThis task is done.")

    def _run_cli_command(self, args: List[str]) -> Dict[str, Any]:
        """CLIコマンドを実行し、結果を返す"""
        full_args = ["python", "-m", "warifuri", "--workspace", str(self.workspace_path)] + args

        result = subprocess.run(
            full_args, capture_output=True, text=True, cwd=self.workspace_path.parent
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "args": args,
        }

    def test_help_output_snapshot(self) -> None:
        """helpコマンドの出力スナップショット"""
        result = self._run_cli_command(["--help"])

        # Help output should be consistent
        self.assertMatchSnapshot(result["stdout"], name="help_output")
        assert result["returncode"] == 0

    def test_version_output_snapshot(self) -> None:
        """versionコマンドの出力スナップショット"""
        result = self._run_cli_command(["--version"])

        # Version output should be consistent (but we'll mask the actual version)
        version_output = result["stdout"].strip()
        # Replace actual version with placeholder for stable snapshot
        normalized_output = "warifuri, version X.X.X\n" if version_output else ""

        self.assertMatchSnapshot(normalized_output, name="version_output")
        assert result["returncode"] == 0

    def test_list_command_output_snapshot(self) -> None:
        """listコマンドの出力スナップショット"""
        result = self._run_cli_command(["list"])

        # List output should show tasks in consistent format
        self.assertMatchSnapshot(result["stdout"], name="list_default_output")
        assert result["returncode"] == 0

    def test_list_command_json_output_snapshot(self) -> None:
        """listコマンドのJSON出力スナップショット"""
        result = self._run_cli_command(["list", "--format", "json"])

        # JSON output should be consistent
        self.assertMatchSnapshot(result["stdout"], name="list_json_output")
        assert result["returncode"] == 0

    def test_list_command_ready_filter_snapshot(self) -> None:
        """listコマンドの--readyフィルタ出力スナップショット"""
        result = self._run_cli_command(["list", "--ready"])

        # Ready filter output should be consistent
        self.assertMatchSnapshot(result["stdout"], name="list_ready_output")
        assert result["returncode"] == 0

    def test_show_command_output_snapshot(self) -> None:
        """showコマンドの出力スナップショット"""
        result = self._run_cli_command(["show", "--task", "sample-task"])

        # Show output should display task details consistently
        self.assertMatchSnapshot(result["stdout"], name="show_task_output")
        assert result["returncode"] == 0

    def test_validate_command_output_snapshot(self) -> None:
        """validateコマンドの出力スナップショット"""
        result = self._run_cli_command(["validate"])

        # Validate output should show validation results consistently
        self.assertMatchSnapshot(result["stdout"], name="validate_output")
        # Validation might return different codes depending on validation results

    def test_graph_command_help_snapshot(self) -> None:
        """graphコマンドのヘルプ出力スナップショット"""
        result = self._run_cli_command(["graph", "--help"])

        # Graph help should be consistent
        self.assertMatchSnapshot(result["stdout"], name="graph_help_output")
        assert result["returncode"] == 0

    def test_automation_help_snapshot(self) -> None:
        """automationコマンドのヘルプ出力スナップショット"""
        result = self._run_cli_command(["automation", "--help"])

        # Automation help should be consistent
        self.assertMatchSnapshot(result["stdout"], name="automation_help_output")
        assert result["returncode"] == 0

    def test_template_help_snapshot(self) -> None:
        """templateコマンドのヘルプ出力スナップショット"""
        result = self._run_cli_command(["template", "--help"])

        # Template help should be consistent
        self.assertMatchSnapshot(result["stdout"], name="template_help_output")
        assert result["returncode"] == 0

    def test_init_help_snapshot(self) -> None:
        """initコマンドのヘルプ出力スナップショット"""
        result = self._run_cli_command(["init", "--help"])

        # Init help should be consistent
        self.assertMatchSnapshot(result["stdout"], name="init_help_output")
        assert result["returncode"] == 0

    def test_mark_done_help_snapshot(self) -> None:
        """mark-doneコマンドのヘルプ出力スナップショット"""
        result = self._run_cli_command(["mark-done", "--help"])

        # Mark-done help should be consistent
        self.assertMatchSnapshot(result["stdout"], name="mark_done_help_output")
        assert result["returncode"] == 0

    def test_issue_help_snapshot(self) -> None:
        """issueコマンドのヘルプ出力スナップショット"""
        result = self._run_cli_command(["issue", "--help"])

        # Issue help should be consistent
        self.assertMatchSnapshot(result["stdout"], name="issue_help_output")
        assert result["returncode"] == 0

    def test_error_output_snapshot(self) -> None:
        """エラー出力のスナップショット"""
        result = self._run_cli_command(["show", "--task", "nonexistent/task"])

        # Error output should be consistent
        # Note: CLI may return 0 even for errors, so we check stdout for error messages
        combined_output = result["stdout"] + result["stderr"]
        self.assertMatchSnapshot(combined_output, name="show_nonexistent_error")
        # Don't assert return code since CLI behavior may vary

    def test_run_dry_run_snapshot(self) -> None:
        """run --dry-run出力のスナップショット"""
        result = self._run_cli_command(["run", "sample-task", "--dry-run"])

        # Dry run output should be consistent
        self.assertMatchSnapshot(result["stdout"], name="run_dry_run_output")
        # Note: dry-run might return 0 or non-zero depending on implementation
