"""List command for displaying tasks."""

import json
from typing import Any, Dict, List, Optional

import click

from ..context import Context, pass_context
from ...core.discovery import discover_all_projects, find_ready_tasks
from ...core.types import Task, TaskStatus


@click.command()
@click.option("--ready", is_flag=True, help="Show only ready tasks")
@click.option("--completed", is_flag=True, help="Show only completed tasks")
@click.option("--project", help="Filter by project name")
@click.option(
    "--format",
    type=click.Choice(["plain", "json", "tsv"]),
    default="plain",
    help="Output format",
)
@click.option("--fields", help="Comma-separated list of fields to display")
@pass_context
def list_cmd(
    ctx: Context,
    ready: bool,
    completed: bool,
    project: Optional[str],
    format: str,
    fields: Optional[str],
) -> None:
    """List tasks in workspace."""
    workspace_path = ctx.workspace_path
    assert workspace_path is not None

    # Discover all projects
    projects = discover_all_projects(workspace_path)

    # Collect tasks
    all_tasks = []
    for proj in projects:
        if project and proj.name != project:
            continue
        all_tasks.extend(proj.tasks)

    # Update task statuses
    find_ready_tasks(projects)

    # Filter tasks
    tasks = _filter_tasks(all_tasks, ready, completed)

    # Display tasks
    if format == "json":
        _display_json(tasks, fields)
    elif format == "tsv":
        _display_tsv(tasks, fields)
    else:
        _display_plain(tasks, fields)


def _filter_tasks(tasks: List[Task], ready: bool, completed: bool) -> List[Task]:
    """Filter tasks based on status flags."""
    if ready:
        return [t for t in tasks if t.status == TaskStatus.READY]
    elif completed:
        return [t for t in tasks if t.status == TaskStatus.COMPLETED]
    else:
        return tasks


def _get_task_fields(task: Task, fields: Optional[str]) -> Dict[str, Any]:
    """Get task data for specified fields."""
    all_fields = {
        "name": task.full_name,
        "description": task.instruction.description,
        "status": task.status.value,
        "type": task.task_type.value,
        "dependencies": task.instruction.dependencies,
        "project": task.project,
        "task": task.name,
    }

    if fields:
        field_list = [f.strip() for f in fields.split(",")]
        return {k: v for k, v in all_fields.items() if k in field_list}
    else:
        return {
            "name": all_fields["name"],
            "description": all_fields["description"],
            "status": all_fields["status"],
        }


def _display_plain(tasks: List[Task], fields: Optional[str]) -> None:
    """Display tasks in plain format."""
    if not tasks:
        click.echo("No tasks found.")
        return

    for task in tasks:
        task_data = _get_task_fields(task, fields)

        # Display name with status if available
        if "status" in task_data:
            click.echo(f"[{task_data['status'].upper()}] {task_data['name']}")
        else:
            click.echo(f"{task_data['name']}")

        if "description" in task_data:
            click.echo(f"  {task_data['description']}")

        # Display other fields
        displayed_fields = {"name", "description", "status"}
        for key, value in task_data.items():
            if key not in displayed_fields:
                click.echo(f"  {key}: {value}")
        click.echo()


def _display_json(tasks: List[Task], fields: Optional[str]) -> None:
    """Display tasks in JSON format."""
    data = [_get_task_fields(task, fields) for task in tasks]
    click.echo(json.dumps(data, indent=2, ensure_ascii=False))


def _display_tsv(tasks: List[Task], fields: Optional[str]) -> None:
    """Display tasks in TSV format."""
    if not tasks:
        return

    # Get field names from first task
    first_task_data = _get_task_fields(tasks[0], fields)
    headers = list(first_task_data.keys())

    # Print header
    click.echo("\t".join(headers))

    # Print data
    for task in tasks:
        task_data = _get_task_fields(task, fields)
        values = [str(task_data.get(h, "")) for h in headers]
        click.echo("\t".join(values))
