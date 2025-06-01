"""File system utilities."""

import shutil
import tempfile
from pathlib import Path
from typing import Iterator, List, Optional, Union


def find_workspace_root(start_path: Optional[Union[str, Path]] = None) -> Optional[Path]:
    """Find workspace root directory by looking for workspace/ or projects/ directory."""
    current = Path(start_path) if start_path else Path.cwd()

    while current != current.parent:
        # Check for workspace/ directory
        if (current / "workspace").is_dir():
            return current / "workspace"

        # Check for projects/ directory (direct workspace)
        if (current / "projects").is_dir():
            return current

        current = current.parent

    return None


def list_projects(workspace_path: Path) -> List[str]:
    """List all project names in workspace."""
    projects_dir = workspace_path / "projects"
    if not projects_dir.exists():
        return []

    return [
        item.name
        for item in projects_dir.iterdir()
        if item.is_dir() and not item.name.startswith(".")
    ]


def list_tasks(workspace_path: Path, project_name: str) -> List[str]:
    """List all task names in a project."""
    project_dir = workspace_path / "projects" / project_name
    if not project_dir.exists():
        return []

    return [
        item.name
        for item in project_dir.iterdir()
        if item.is_dir() and not item.name.startswith(".")
    ]


def find_instruction_files(workspace_path: Path) -> Iterator[Path]:
    """Find all instruction.yaml files in workspace."""
    projects_dir = workspace_path / "projects"
    if not projects_dir.exists():
        return

    for instruction_file in projects_dir.rglob("instruction.yaml"):
        if instruction_file.is_file():
            yield instruction_file


def create_temp_dir() -> Path:
    """Create a temporary directory for safe task execution with restricted permissions."""
    import stat

    # Create temporary directory with restricted permissions (owner only)
    temp_dir = Path(tempfile.mkdtemp(prefix="warifuri_"))

    # Set restrictive permissions (rwx------) for security
    temp_dir.chmod(stat.S_IRWXU)  # 0o700

    return temp_dir


def copy_directory_contents(src: Path, dst: Path) -> None:
    """Copy directory contents to destination."""
    if not src.exists():
        raise FileNotFoundError(f"Source directory not found: {src}")

    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        if item.is_file():
            shutil.copy2(item, dst / item.name)
        elif item.is_dir():
            shutil.copytree(item, dst / item.name, dirs_exist_ok=True)


def ensure_directory(path: Path) -> None:
    """Ensure directory exists, create if not."""
    path.mkdir(parents=True, exist_ok=True)


def safe_write_file(file_path: Path, content: str) -> None:
    """Safely write content to file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def get_git_commit_sha() -> Optional[str]:
    """Get current git commit SHA."""
    try:
        import git

        repo = git.Repo(search_parent_directories=True)
        sha: str = repo.head.commit.hexsha
        return sha
    except (ImportError, OSError, FileNotFoundError, ValueError):
        # Git module not available or repository not found or other error
        return None
