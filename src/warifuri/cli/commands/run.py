"""Run command for executing tasks."""

from typing import Optional

import click

from ...core.discovery import discover_all_projects, find_ready_tasks, find_task_by_name
from ...core.execution import execute_task
from ...core.types import TaskType
from ..context import Context, pass_context


@click.command()
@click.option("--task", help="Task to run (project or project/task)")
@click.option("--dry-run", is_flag=True, help="Show what would be executed without executing")
@click.option("--force", is_flag=True, help="Force execution even if dependencies not met")
@pass_context
def run(
    ctx: Context,
    task: Optional[str],
    dry_run: bool,
    force: bool,
) -> None:
    """Run task(s).

    Without --task: Run one ready task automatically.
    With --task PROJECT: Run one ready task from the project.
    With --task PROJECT/TASK: Run the specific task.
    """
    workspace_path = ctx.ensure_workspace_path()

    # Discover all projects
    projects = discover_all_projects(workspace_path)

    if not projects:
        click.echo("No projects found in workspace.")
        return

    target_task = None

    if task:
        if "/" in task:
            # Specific task
            project_name, task_name = task.split("/", 1)
            target_task = find_task_by_name(projects, project_name, task_name)
            if not target_task:
                click.echo(f"Error: Task '{task}' not found.", err=True)
                return
        else:
            # Project - find ready task
            project_name = task
            ready_tasks = find_ready_tasks(projects, workspace_path)
            project_ready_tasks = [t for t in ready_tasks if t.project == project_name]

            if not project_ready_tasks:
                click.echo(f"No ready tasks found in project '{project_name}'.")
                return

            target_task = project_ready_tasks[0]
    else:
        # Auto-run ready task
        ready_tasks = find_ready_tasks(projects, workspace_path)

        if not ready_tasks:
            click.echo("No ready tasks found.")
            return

        target_task = ready_tasks[0]

    # Execute the task
    if target_task:
        click.echo(f"Executing task: {target_task.full_name}")
        click.echo(f"Type: {target_task.task_type.value}")
        click.echo(f"Description: {target_task.instruction.description}")

        if dry_run:
            click.echo("[DRY RUN] Task execution simulation completed.")
        else:
            # Special handling for human tasks
            if target_task.task_type == TaskType.HUMAN:
                click.echo(f"Human task '{target_task.full_name}' requires manual intervention.")
                click.echo(
                    "Please complete the task manually and run 'warifuri mark-done' when finished."
                )
                return

            # Collect all tasks for dependency checking
            all_tasks = []
            for proj in projects:
                all_tasks.extend(proj.tasks)

            success = execute_task(target_task, dry_run=dry_run, force=force, all_tasks=all_tasks)
            if success:
                click.echo(f"✅ Task completed: {target_task.full_name}")
            else:
                click.echo(f"❌ Task failed: {target_task.full_name}", err=True)

                # Show recent error log if available
                logs_dir = target_task.path / "logs"
                if logs_dir.exists():
                    recent_logs = sorted(
                        logs_dir.glob("failed_*.log"), key=lambda x: x.stat().st_mtime, reverse=True
                    )
                    if recent_logs:
                        log_content = recent_logs[0].read_text()
                        # Extract error message from log
                        lines = log_content.split("\n")
                        for line in lines:
                            if line.startswith("Error:"):
                                click.echo(f"Error: {line[6:].strip()}", err=True)
                                break

                raise click.Abort()
