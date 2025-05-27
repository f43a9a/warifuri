"""Show command for displaying task details."""

import json

import click
import yaml

from ..main import Context, pass_context
from ...core.discovery import discover_all_projects, find_task_by_name


@click.command()
@click.option("--task", required=True, help="Task to show (project/task)")
@click.option(
    "--format",
    type=click.Choice(["yaml", "json", "pretty"]),
    default="pretty",
    help="Output format",
)
@pass_context
def show(
    ctx: Context,
    task: str,
    format: str,
) -> None:
    """Show task definition and metadata."""
    workspace_path = ctx.workspace_path
    assert workspace_path is not None

    if "/" not in task:
        click.echo("Error: Task must be in format 'project/task'.", err=True)
        return

    project_name, task_name = task.split("/", 1)

    # Discover projects and find task
    projects = discover_all_projects(workspace_path)
    target_task = find_task_by_name(projects, project_name, task_name)

    if not target_task:
        click.echo(f"Error: Task '{task}' not found.", err=True)
        return

    # Prepare data
    task_data = {
        "name": target_task.name,
        "project": target_task.project,
        "full_name": target_task.full_name,
        "description": target_task.instruction.description,
        "dependencies": target_task.instruction.dependencies,
        "inputs": target_task.instruction.inputs,
        "outputs": target_task.instruction.outputs,
        "note": target_task.instruction.note,
        "type": target_task.task_type.value,
        "status": target_task.status.value,
        "completed": target_task.is_completed,
        "auto_merge": target_task.has_auto_merge,
        "path": str(target_task.path),
    }

    # Display data
    if format == "json":
        click.echo(json.dumps(task_data, indent=2, ensure_ascii=False))
    elif format == "yaml":
        click.echo(yaml.safe_dump(task_data, default_flow_style=False, sort_keys=False))
    else:
        # Pretty format
        click.echo(f"Task: {task_data['full_name']}")
        click.echo(f"Type: {task_data['type']}")
        click.echo(f"Status: {task_data['status']}")
        click.echo(f"Completed: {'Yes' if task_data['completed'] else 'No'}")
        click.echo(f"Auto-merge: {'Yes' if task_data['auto_merge'] else 'No'}")
        click.echo(f"Path: {task_data['path']}")
        click.echo()
        click.echo("Description:")
        click.echo(f"  {task_data['description']}")

        if task_data["dependencies"] and task_data["dependencies"] is not True:
            click.echo()
            click.echo("Dependencies:")
            for dep in task_data["dependencies"]:
                click.echo(f"  - {dep}")

        if task_data["inputs"] and task_data["inputs"] is not True:
            click.echo()
            click.echo("Inputs:")
            for inp in task_data["inputs"]:
                click.echo(f"  - {inp}")

        if task_data["outputs"] and task_data["outputs"] is not True:
            click.echo()
            click.echo("Outputs:")
            for out in task_data["outputs"]:
                click.echo(f"  - {out}")

        if task_data["note"]:
            click.echo()
            click.echo("Note:")
            click.echo(f"  {task_data['note']}")
