"""Utilities package initialization."""

from .filesystem import (
    copy_directory_contents,
    create_temp_dir,
    ensure_directory,
    find_workspace_root,
    get_git_commit_sha,
    list_projects,
    list_tasks,
    safe_write_file,
)
from .logging import setup_logging
from .templates import (
    expand_template_directory,
    expand_template_file,
    expand_template_placeholders,
    get_template_variables_from_user,
)
from .validation import (
    CircularDependencyError,
    ValidationError,
    detect_circular_dependencies,
    load_schema,
    validate_file_references,
    validate_instruction_yaml,
)
from .yaml_utils import load_yaml, save_yaml

__all__ = [
    "copy_directory_contents",
    "create_temp_dir",
    "ensure_directory",
    "find_workspace_root",
    "get_git_commit_sha",
    "list_projects",
    "list_tasks",
    "safe_write_file",
    "setup_logging",
    "CircularDependencyError",
    "ValidationError",
    "detect_circular_dependencies",
    "load_schema",
    "validate_file_references",
    "validate_instruction_yaml",
    "load_yaml",
    "save_yaml",
]
