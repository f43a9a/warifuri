"""Mark-done command for manually completing tasks."""

import click

from ..context import Context, pass_context
from ...core.discovery import discover_all_projects, find_task_by_name
from ...core.execution import create_done_file


@click.command()
@click.argument("task_name", required=True)
@click.option("--message", help="Custom message for done.md")
@pass_context
def mark_done(
    ctx: Context,
    task_name: str,
    message: str,
) -> None:
    """Mark task as completed by creating done.md file.

    TASK_NAME should be in format 'project/task'.
    """
    workspace_path = ctx.workspace_path
    assert workspace_path is not None

    if "/" not in task_name:
        click.echo("Error: Task name must be in format 'project/task'.", err=True)
        return

    project_name, task = task_name.split("/", 1)

    # Find the task
    projects = discover_all_projects(workspace_path)
    target_task = find_task_by_name(projects, project_name, task)

    if not target_task:
        click.echo(f"Error: Task '{task_name}' not found.", err=True)
        return

    if target_task.is_completed:
        click.echo(f"Task '{task_name}' is already completed.")
        return

    # Create done.md file
    create_done_file(target_task, message)

    click.echo(f"✅ Marked task as completed: {task_name}")
    if message:
        click.echo(f"Message: {message}")
