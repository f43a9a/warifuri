"""Human task execution module."""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.types import Task

logger = logging.getLogger(__name__)


def execute_human_task(task: "Task", dry_run: bool = False) -> bool:
    """Handle human task execution.

    Args:
        task: The human task to execute
        dry_run: If True, only log what would be done

    Returns:
        True (human tasks are always considered successful as they require manual completion)
    """
    logger.info(f"Human task: {task.full_name}")

    if dry_run:
        logger.info(f"[DRY RUN] Human task requires manual intervention: {task.full_name}")
    else:
        logger.info(f"Human task '{task.full_name}' requires manual intervention.")
        logger.info(f"Description: {task.instruction.description}")
        logger.info("Please complete the task manually and run 'warifuri mark-done' when finished.")

    return True
