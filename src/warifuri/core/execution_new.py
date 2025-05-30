"""Task execution engine - backward compatibility module.

This module provides backward compatibility by re-exporting functions
from the modular execution package.
"""

# Re-export all functions from the modular execution package for backward compatibility
from .execution import (
    ExecutionError,
    execute_task,
    check_dependencies,
    copy_outputs_back,
    save_execution_log,
    log_failure,
    create_done_file,
    execute_machine_task,
    execute_ai_task,
    execute_human_task,
    validate_task_inputs,
    validate_task_outputs,
    copy_input_files,
    setup_task_environment,
)

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
    "copy_input_files",
    "setup_task_environment",
]
