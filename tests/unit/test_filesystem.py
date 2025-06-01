"""Tests for filesystem utilities."""

import stat
from pathlib import Path
from unittest.mock import patch

import pytest

from warifuri.utils.filesystem import (
    find_workspace_root,
    list_projects,
    list_tasks,
    find_instruction_files,
    create_temp_dir,
    copy_directory_contents,
    ensure_directory,
    safe_write_file,
    get_git_commit_sha,
)


class TestFindWorkspaceRoot:
    """Test find_workspace_root function."""

    def test_find_workspace_root_with_workspace_dir(self, tmp_path: Path) -> None:
        """Test finding workspace root with workspace/ directory."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()

        # Create a subdirectory and search from there
        sub_dir = tmp_path / "some" / "nested" / "path"
        sub_dir.mkdir(parents=True)

        result = find_workspace_root(sub_dir)
        assert result == workspace_dir

    def test_find_workspace_root_with_projects_dir(self, tmp_path: Path) -> None:
        """Test finding workspace root with projects/ directory."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        sub_dir = tmp_path / "nested"
        sub_dir.mkdir()

        result = find_workspace_root(sub_dir)
        assert result == tmp_path

    def test_find_workspace_root_not_found(self, tmp_path: Path) -> None:
        """Test when workspace root is not found."""
        sub_dir = tmp_path / "no" / "valid" / "structure" / "here"
        sub_dir.mkdir(parents=True)

        result = find_workspace_root(sub_dir)
        assert result is None

    def test_find_workspace_root_current_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test finding workspace root from current directory."""
        workspace_dir = tmp_path / "workspace"
        workspace_dir.mkdir()

        monkeypatch.chdir(tmp_path)
        result = find_workspace_root()
        assert result == workspace_dir


class TestListProjects:
    """Test list_projects function."""

    def test_list_projects_success(self, tmp_path: Path) -> None:
        """Test listing projects successfully."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create some project directories
        (projects_dir / "project1").mkdir()
        (projects_dir / "project2").mkdir()
        (projects_dir / "project3").mkdir()

        # Create hidden directory (should be ignored)
        (projects_dir / ".hidden").mkdir()

        # Create a file (should be ignored)
        (projects_dir / "file.txt").touch()

        projects = list_projects(tmp_path)
        assert set(projects) == {"project1", "project2", "project3"}

    def test_list_projects_no_projects_dir(self, tmp_path: Path) -> None:
        """Test listing projects when projects/ doesn't exist."""
        projects = list_projects(tmp_path)
        assert projects == []


class TestListTasks:
    """Test list_tasks function."""

    def test_list_tasks_success(self, tmp_path: Path) -> None:
        """Test listing tasks successfully."""
        project_dir = tmp_path / "projects" / "myproject"
        project_dir.mkdir(parents=True)

        # Create some task directories
        (project_dir / "task1").mkdir()
        (project_dir / "task2").mkdir()
        (project_dir / "task3").mkdir()

        # Create hidden directory (should be ignored)
        (project_dir / ".hidden").mkdir()

        tasks = list_tasks(tmp_path, "myproject")
        assert set(tasks) == {"task1", "task2", "task3"}

    def test_list_tasks_no_project(self, tmp_path: Path) -> None:
        """Test listing tasks for non-existent project."""
        tasks = list_tasks(tmp_path, "nonexistent")
        assert tasks == []


class TestFindInstructionFiles:
    """Test find_instruction_files function."""

    def test_find_instruction_files_success(self, tmp_path: Path) -> None:
        """Test finding instruction files successfully."""
        projects_dir = tmp_path / "projects"
        projects_dir.mkdir()

        # Create instruction files in different projects
        proj1_dir = projects_dir / "project1"
        proj1_dir.mkdir()
        inst1 = proj1_dir / "instruction.yaml"
        inst1.touch()

        proj2_task_dir = projects_dir / "project2" / "task1"
        proj2_task_dir.mkdir(parents=True)
        inst2 = proj2_task_dir / "instruction.yaml"
        inst2.touch()

        # Non-instruction file (should be ignored)
        (proj1_dir / "other.yaml").touch()

        files = list(find_instruction_files(tmp_path))
        assert len(files) == 2
        assert inst1 in files
        assert inst2 in files

    def test_find_instruction_files_no_projects_dir(self, tmp_path: Path) -> None:
        """Test finding instruction files when projects/ doesn't exist."""
        files = list(find_instruction_files(tmp_path))
        assert files == []


class TestCreateTempDir:
    """Test create_temp_dir function."""

    def test_create_temp_dir(self) -> None:
        """Test creating temporary directory with correct permissions."""
        temp_dir = create_temp_dir()

        try:
            assert temp_dir.exists()
            assert temp_dir.is_dir()
            assert temp_dir.name.startswith("warifuri_")

            # Check permissions (owner read/write/execute only)
            mode = temp_dir.stat().st_mode
            assert mode & stat.S_IRWXU == stat.S_IRWXU  # Owner has rwx
            assert mode & stat.S_IRWXG == 0  # Group has no permissions
            assert mode & stat.S_IRWXO == 0  # Others have no permissions

        finally:
            # Clean up
            import shutil
            shutil.rmtree(temp_dir)


class TestCopyDirectoryContents:
    """Test copy_directory_contents function."""

    def test_copy_directory_contents_success(self, tmp_path: Path) -> None:
        """Test copying directory contents successfully."""
        src = tmp_path / "src"
        dst = tmp_path / "dst"

        src.mkdir()

        # Create source files and directories
        (src / "file1.txt").write_text("content1")
        (src / "file2.txt").write_text("content2")

        subdir = src / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("nested content")

        copy_directory_contents(src, dst)

        assert dst.exists()
        assert (dst / "file1.txt").read_text() == "content1"
        assert (dst / "file2.txt").read_text() == "content2"
        assert (dst / "subdir" / "nested.txt").read_text() == "nested content"

    def test_copy_directory_contents_source_not_found(self, tmp_path: Path) -> None:
        """Test copying from non-existent source directory."""
        src = tmp_path / "nonexistent"
        dst = tmp_path / "dst"

        with pytest.raises(FileNotFoundError, match="Source directory not found"):
            copy_directory_contents(src, dst)


class TestEnsureDirectory:
    """Test ensure_directory function."""

    def test_ensure_directory_creates_new(self, tmp_path: Path) -> None:
        """Test creating new directory."""
        new_dir = tmp_path / "new" / "nested" / "dir"

        ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ensure_directory_exists(self, tmp_path: Path) -> None:
        """Test with existing directory."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()

        ensure_directory(existing_dir)

        assert existing_dir.exists()
        assert existing_dir.is_dir()


class TestSafeWriteFile:
    """Test safe_write_file function."""

    def test_safe_write_file_new_file(self, tmp_path: Path) -> None:
        """Test writing to new file."""
        file_path = tmp_path / "new" / "file.txt"
        content = "test content"

        safe_write_file(file_path, content)

        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == content

    def test_safe_write_file_existing_file(self, tmp_path: Path) -> None:
        """Test overwriting existing file."""
        file_path = tmp_path / "existing.txt"
        file_path.write_text("old content")

        new_content = "new content"
        safe_write_file(file_path, new_content)

        assert file_path.read_text(encoding="utf-8") == new_content


class TestGetGitCommitSha:
    """Test get_git_commit_sha function."""

    def test_get_git_commit_sha_no_git_module(self) -> None:
        """Test when git module is not available."""
        with patch.dict("sys.modules", {"git": None}):
            sha = get_git_commit_sha()
            assert sha is None
