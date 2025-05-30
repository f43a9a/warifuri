"""Unit tests for file operations module."""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import List

from warifuri.core.execution.file_ops import copy_input_files, _copy_file_or_directory
from warifuri.core.types import TaskInstruction, Task, TaskType, TaskStatus


class TestCopyInputFiles:
    """Test copy_input_files function."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.execution_log: List[str] = []

        # Create mock task
        self.task_instruction = TaskInstruction(
            name="test_task",
            description="Test task description",
            dependencies=[],
            inputs=["test_file.txt"],
            outputs=[]
        )
        self.task = Task(
            project="test_project",
            name="test_task",
            path=Path("/workspace/project/task.yaml"),
            instruction=self.task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY
        )

    def test_no_input_files(self) -> None:
        """Test when task has no input files."""
        task_instruction = TaskInstruction(
            name="test_task",
            description="Test task description",
            dependencies=[],
            inputs=[],
            outputs=[]
        )
        task = Task(
            project="test_project",
            name="test_task",
            path=Path("/workspace/project/task.yaml"),
            instruction=task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY
        )

        copy_input_files(task, self.temp_dir, self.execution_log)

        assert "No input files to copy" in self.execution_log

    def test_workspace_path_none_derives_from_task_path(self) -> None:
        """Test that workspace_path is derived from task.path when None."""
        with patch("warifuri.core.execution.file_ops._resolve_input_path_safely") as mock_resolve:
            mock_resolve.return_value = (None, "File not found")

            copy_input_files(self.task, self.temp_dir, self.execution_log, workspace_path=None)

            # Verify that _resolve_input_path_safely was called with correct projects_base
            expected_projects_base = self.task.path.parent.parent.parent / "projects"
            mock_resolve.assert_called_once_with(
                "test_file.txt",
                self.task.path,
                expected_projects_base
            )

    def test_source_path_none_continues(self) -> None:
        """Test that function continues when source_path is None."""
        with patch("warifuri.core.execution.file_ops._resolve_input_path_safely") as mock_resolve:
            mock_resolve.return_value = (None, "File not found")

            copy_input_files(self.task, self.temp_dir, self.execution_log)

            assert "Copying input files to temporary directory..." in self.execution_log
            assert "File not found" in self.execution_log
            # Should not attempt to copy anything

    def test_source_file_not_exists(self) -> None:
        """Test error handling when source file doesn't exist."""
        non_existent_path = Path("/non/existent/file.txt")

        with patch("warifuri.core.execution.file_ops._resolve_input_path_safely") as mock_resolve:
            mock_resolve.return_value = (non_existent_path, "Resolved path")

            copy_input_files(self.task, self.temp_dir, self.execution_log)

            expected_error = f"ERROR: Input file not found during copy: {non_existent_path}"
            assert expected_error in self.execution_log

    def test_copy_cross_project_file(self) -> None:
        """Test copying cross-project files with flattened structure."""
        # Create a real file to copy
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("test content")
            source_path = Path(temp_file.name)

        try:
            task_instruction = TaskInstruction(
                name="test_task",
                description="Test task description",
                dependencies=[],
                inputs=["../other-project/file.txt"],
                outputs=[]
            )
            task = Task(
                project="test_project",
                name="test_task",
                path=Path("/workspace/project/task.yaml"),
                instruction=task_instruction,
                task_type=TaskType.MACHINE,
                status=TaskStatus.READY
            )

            with patch("warifuri.core.execution.file_ops._resolve_input_path_safely") as mock_resolve:
                mock_resolve.return_value = (source_path, "Resolved cross-project file")

                with patch("warifuri.core.execution.file_ops._copy_file_or_directory") as mock_copy:
                    copy_input_files(task, self.temp_dir, self.execution_log)

                    # Verify the destination path is flattened
                    expected_dest = self.temp_dir / "other-project_file.txt"
                    mock_copy.assert_called_once_with(
                        source_path,
                        expected_dest,
                        "../other-project/file.txt",
                        self.execution_log
                    )
        finally:
            source_path.unlink()

    def test_copy_local_file_preserves_structure(self) -> None:
        """Test copying local files preserves relative structure."""
        # Create a real file to copy
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("test content")
            source_path = Path(temp_file.name)

        try:
            task_instruction = TaskInstruction(
                name="test_task",
                description="Test task description",
                dependencies=[],
                inputs=["subdir/file.txt"],
                outputs=[]
            )
            task = Task(
                project="test_project",
                name="test_task",
                path=Path("/workspace/project/task.yaml"),
                instruction=task_instruction,
                task_type=TaskType.MACHINE,
                status=TaskStatus.READY
            )

            with patch("warifuri.core.execution.file_ops._resolve_input_path_safely") as mock_resolve:
                mock_resolve.return_value = (source_path, "Resolved local file")

                with patch("warifuri.core.execution.file_ops._copy_file_or_directory") as mock_copy:
                    copy_input_files(task, self.temp_dir, self.execution_log)

                    # Verify the destination path preserves structure
                    expected_dest = self.temp_dir / "subdir/file.txt"
                    mock_copy.assert_called_once_with(
                        source_path,
                        expected_dest,
                        "subdir/file.txt",
                        self.execution_log
                    )
        finally:
            source_path.unlink()


class TestCopyFileOrDirectory:
    """Test _copy_file_or_directory function."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.execution_log: List[str] = []

    def test_copy_file(self) -> None:
        """Test copying a single file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("test content")
            source_path = Path(temp_file.name)

        dest_path = Path(tempfile.mkdtemp()) / "dest_file.txt"

        try:
            _copy_file_or_directory(source_path, dest_path, "test_file.txt", self.execution_log)

            assert dest_path.exists()
            assert dest_path.read_text() == "test content"
            assert f"Copied input file: test_file.txt -> {dest_path}" in self.execution_log
        finally:
            source_path.unlink()
            if dest_path.exists():
                dest_path.unlink()
            dest_path.parent.rmdir()

    def test_copy_directory(self) -> None:
        """Test copying a directory."""
        # Create temporary source directory with content
        source_dir = Path(tempfile.mkdtemp())
        test_file = source_dir / "test.txt"
        test_file.write_text("test content")

        dest_dir = Path(tempfile.mkdtemp()) / "dest_dir"

        try:
            _copy_file_or_directory(source_dir, dest_dir, "test_dir", self.execution_log)

            assert dest_dir.exists()
            assert dest_dir.is_dir()
            assert (dest_dir / "test.txt").exists()
            assert (dest_dir / "test.txt").read_text() == "test content"
            assert f"Copied input directory: test_dir -> {dest_dir}" in self.execution_log
        finally:
            # Clean up
            import shutil
            shutil.rmtree(source_dir)
            shutil.rmtree(dest_dir.parent)

    def test_copy_error_handling(self) -> None:
        """Test error handling during copy operation."""
        source_path = Path("/non/existent/source")
        dest_path = Path("/tmp/dest")

        _copy_file_or_directory(source_path, dest_path, "error_file", self.execution_log)

        # Should log an error message
        error_logs = [log for log in self.execution_log if log.startswith("ERROR copying")]
        assert len(error_logs) == 1
        assert "ERROR copying input error_file:" in error_logs[0]

    def test_copy_directory_with_existing_dest(self) -> None:
        """Test copying directory when destination already exists."""
        # Create temporary source directory
        source_dir = Path(tempfile.mkdtemp())
        source_file = source_dir / "source.txt"
        source_file.write_text("source content")

        # Create temporary destination directory with existing content
        dest_parent = Path(tempfile.mkdtemp())
        dest_dir = dest_parent / "dest"
        dest_dir.mkdir()
        existing_file = dest_dir / "existing.txt"
        existing_file.write_text("existing content")

        try:
            _copy_file_or_directory(source_dir, dest_dir, "test_dir", self.execution_log)

            # Both files should exist
            assert (dest_dir / "source.txt").exists()
            assert (dest_dir / "existing.txt").exists()
            assert (dest_dir / "source.txt").read_text() == "source content"
            assert (dest_dir / "existing.txt").read_text() == "existing content"

            assert f"Copied input directory: test_dir -> {dest_dir}" in self.execution_log
        finally:
            import shutil
            shutil.rmtree(source_dir)
            shutil.rmtree(dest_parent)


class TestIntegration:
    """Integration tests for file operations."""

    def test_complete_workflow_mocked(self) -> None:
        """Test complete file copying workflow with mocked validation."""
        # Create a temporary workspace structure
        workspace = Path(tempfile.mkdtemp())
        projects_dir = workspace / "projects"
        projects_dir.mkdir()

        # Create source files
        project_dir = projects_dir / "test-project"
        project_dir.mkdir()
        source_file = project_dir / "input.txt"
        source_file.write_text("input content")

        # Create task
        task_instruction = TaskInstruction(
            name="test_task",
            description="Test task description",
            dependencies=[],
            inputs=["input.txt"],
            outputs=[]
        )
        task = Task(
            project="test-project",
            name="test_task",
            path=project_dir / "task.yaml",
            instruction=task_instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY
        )

        # Create destination
        temp_dir = Path(tempfile.mkdtemp())
        execution_log: List[str] = []

        try:
            # Mock the validation function to return the source file
            with patch("warifuri.core.execution.file_ops._resolve_input_path_safely") as mock_resolve:
                mock_resolve.return_value = (source_file, "Resolved input.txt")

                copy_input_files(task, temp_dir, execution_log, workspace_path=workspace)

                # Verify file was copied
                dest_file = temp_dir / "input.txt"
                assert dest_file.exists()
                assert dest_file.read_text() == "input content"

                # Verify logs
                assert "Copying input files to temporary directory..." in execution_log
                assert f"Copied input file: input.txt -> {dest_file}" in execution_log
        finally:
            import shutil
            shutil.rmtree(workspace)
            shutil.rmtree(temp_dir)
