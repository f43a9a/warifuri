"""Test path security and traversal attack prevention."""

import tempfile
from pathlib import Path

import pytest

from warifuri.core.execution import _resolve_input_path_safely


class TestPathSecurity:
    """Test path traversal attack prevention."""

    def test_prevents_basic_path_traversal(self):
        """Test prevention of basic ../ attacks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create projects structure
            projects_base = tmpdir_path / "projects"
            task_path = projects_base / "test-project" / "test-task"
            task_path.mkdir(parents=True)

            # Create a sensitive file outside projects
            sensitive_file = tmpdir_path / "secret.txt"
            sensitive_file.write_text("sensitive data")

            # Try to access it via path traversal
            malicious_input = "../../../secret.txt"

            result, message = _resolve_input_path_safely(malicious_input, task_path, projects_base)

            assert result is None
            assert "SECURITY: Path traversal outside projects directory" in message

    def test_prevents_excessive_traversal(self):
        """Test prevention of excessive ../ sequences."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            projects_base = tmpdir_path / "projects"
            task_path = projects_base / "test-project" / "test-task"
            task_path.mkdir(parents=True)

            # Create input with excessive traversal
            malicious_input = "../" * 20 + "some-file.txt"

            result, message = _resolve_input_path_safely(malicious_input, task_path, projects_base)

            assert result is None
            assert "Excessive path traversal detected" in message

    def test_allows_legitimate_cross_project_access(self):
        """Test that legitimate cross-project access works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            projects_base = tmpdir_path / "projects"

            # Create legitimate file structure
            source_task = projects_base / "source-project" / "source-task"
            target_task = projects_base / "target-project" / "target-task"
            source_task.mkdir(parents=True)
            target_task.mkdir(parents=True)

            # Create a legitimate file to access
            source_file = source_task / "output.txt"
            source_file.write_text("legitimate output")

            # Access it from target task (need to go up 2 levels: task -> project -> projects)
            input_path = "../../source-project/source-task/output.txt"

            result, message = _resolve_input_path_safely(input_path, target_task, projects_base)

            assert result is not None
            assert result.exists()
            assert result.read_text() == "legitimate output"
            assert "Resolved cross-project input" in message

    def test_handles_symlink_attacks(self):
        """Test prevention of symlink-based attacks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            projects_base = tmpdir_path / "projects"
            task_path = projects_base / "test-project" / "test-task"
            task_path.mkdir(parents=True)

            # Create sensitive file outside projects
            sensitive_file = tmpdir_path / "sensitive.txt"
            sensitive_file.write_text("secret")

            # Try to create symlink attack (if symlinks are supported)
            try:
                malicious_link = task_path / "malicious_link.txt"
                malicious_link.symlink_to(sensitive_file)

                result, message = _resolve_input_path_safely(
                    "malicious_link.txt", task_path, projects_base
                )

                # Should either reject the symlink or ensure it stays within bounds
                if result is not None:
                    # If symlink is allowed, it should still be within projects bounds
                    assert result.is_relative_to(projects_base.resolve())

            except OSError:
                # Symlinks not supported on this system, skip test
                pytest.skip("Symlinks not supported")
