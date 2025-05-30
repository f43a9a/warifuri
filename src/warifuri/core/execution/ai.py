"""AI task execution."""

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.types import Task

logger = logging.getLogger(__name__)


def execute_ai_task(task: "Task", dry_run: bool = False) -> bool:
    """Execute AI task using LLM API."""
    logger.info(f"Executing AI task: {task.full_name}")

    if dry_run:
        logger.info(f"[DRY RUN] Would execute AI task: {task.full_name}")
        return True

    try:
        from ...utils.llm import LLMClient, load_prompt_config, save_ai_response, log_ai_error

        # Load prompt configuration
        prompt_config = load_prompt_config(task.path)

        # Initialize LLM client
        llm_client = LLMClient(
            model=prompt_config.get("model", "gpt-3.5-turbo"),
            temperature=prompt_config.get("temperature", 0.7),
        )

        # Build prompts
        system_prompt = prompt_config.get("system_prompt", "You are a helpful AI assistant.")

        # Combine system prompt with task description if no explicit prompt provided
        if "prompt" in prompt_config:
            user_prompt = prompt_config["prompt"]
        else:
            user_prompt = task.instruction.description

        # Add context from task instruction
        if task.instruction.note:
            user_prompt += f"\n\nAdditional context:\n{task.instruction.note}"

        # Generate response
        logger.info(f"Generating AI response for {task.full_name}")
        response = llm_client.generate_response(system_prompt, user_prompt)

        # Save response
        save_ai_response(response, task.path)

        # Create done.md
        from .core import create_done_file
        create_done_file(task, "AI task completed successfully")

        logger.info(f"AI task completed: {task.full_name}")
        return True

    except Exception as e:
        logger.error(f"AI task failed: {task.full_name}: {e}")
        log_ai_error(e, task.path)
        return False
