"""Task execution engine - main entry points."""

# Import from the modular components
from .ai import execute_ai_task
from .core import (
    check_dependencies,
    copy_outputs_back,
    create_done_file,
    execute_task,
    log_failure,
    save_execution_log,
)
from .environment import setup_task_environment
from .errors import ExecutionError
from .file_ops import copy_input_files
from .human import execute_human_task
from .machine import execute_machine_task
from .validation import _resolve_input_path_safely, validate_task_inputs, validate_task_outputs

__all__ = [
    "ExecutionError",
    "execute_task",
    "check_dependencies",
    "copy_outputs_back",
    "save_execution_log",
    "log_failure",
    "create_done_file",
    "execute_machine_task",
    "execute_ai_task",
    "execute_human_task",
    "validate_task_inputs",
    "validate_task_outputs",
    "_resolve_input_path_safely",
    "copy_input_files",
    "setup_task_environment",
]
