"""Initialize command for creating projects and tasks."""

from pathlib import Path
from typing import Optional

import click

from ..context import Context, pass_context
from ...utils import (
    ensure_directory,
    safe_write_file,
    expand_template_directory,
    get_template_variables_from_user,
)


@click.command()
@click.argument("target", required=False)
@click.option("--template", help="Template to use for initialization")
@click.option("--force", is_flag=True, help="Overwrite existing files")
@click.option("--dry-run", is_flag=True, help="Show what would be created without creating")
@click.option("--non-interactive", is_flag=True, help="Use default values without prompting")
@pass_context
def init(
    ctx: Context,
    target: Optional[str],
    template: Optional[str],
    force: bool,
    dry_run: bool,
    non_interactive: bool,
) -> None:
    """Initialize project or task.

    TARGET can be:
    - project_name: Create new project
    - project_name/task_name: Create new task
    - Empty with --template: Expand template to current workspace
    """
    workspace_path = ctx.workspace_path
    assert workspace_path is not None

    # Handle template-only expansion (no target)
    if not target and template:
        _expand_template_to_workspace(workspace_path, template, force, dry_run, non_interactive)
        return

    if not target:
        click.echo(
            "Error: TARGET is required unless using --template for workspace expansion.", err=True
        )
        return

    if "/" in target:
        # Create task
        project_name, task_name = target.split("/", 1)
        _create_task(
            workspace_path, project_name, task_name, template, force, dry_run, non_interactive
        )
    else:
        # Create project
        project_name = target
        _create_project(workspace_path, project_name, template, force, dry_run, non_interactive)


def _create_project(
    workspace_path: Path,
    project_name: str,
    template: Optional[str],
    force: bool,
    dry_run: bool,
    non_interactive: bool,
) -> None:
    """Create a new project."""
    project_path = workspace_path / "projects" / project_name

    if project_path.exists() and not force:
        click.echo(
            f"Error: Project '{project_name}' already exists. Use --force to overwrite.", err=True
        )
        return

    if dry_run:
        click.echo(f"Would create project: {project_path}")
        if template:
            click.echo(f"  Using template: {template}")
        return

    # Create project directory
    ensure_directory(project_path)

    # Handle template expansion
    if template:
        template_path = workspace_path / "templates" / template
        if not template_path.exists():
            click.echo(f"Error: Template '{template}' not found.", err=True)
            return

        click.echo(f"Using template: {template}")

        # Get template variables from user
        variables = get_template_variables_from_user(
            project_name, non_interactive=dry_run or force or non_interactive
        )
        variables["PROJECT_NAME"] = project_name  # Ensure project name is set

        # Expand template
        try:
            expand_template_directory(template_path, project_path, variables)
            click.echo(f"Created project '{project_name}' from template '{template}'")

            # List created tasks
            tasks = [
                d.name for d in project_path.iterdir() if d.is_dir() and not d.name.startswith(".")
            ]
            if tasks:
                click.echo("Created tasks:")
                for task in tasks:
                    click.echo(f"  - {task}")
        except Exception as e:
            click.echo(f"Error expanding template: {e}", err=True)
            return
    else:
        click.echo(f"Created project: {project_name}")
        click.echo("Use 'warifuri init {project_name}/{task_name}' to create tasks.")


def _create_task(
    workspace_path: Path,
    project_name: str,
    task_name: str,
    template: Optional[str],
    force: bool,
    dry_run: bool,
    non_interactive: bool,
) -> None:
    """Create a new task."""
    task_path = workspace_path / "projects" / project_name / task_name

    if task_path.exists() and not force:
        click.echo(
            f"Error: Task '{project_name}/{task_name}' already exists. Use --force to overwrite.",
            err=True,
        )
        return

    if dry_run:
        click.echo(f"Would create task: {task_path}")
        click.echo("  - instruction.yaml")
        if template:
            click.echo(f"  Using template: {template}")
        return

    # Create task directory
    ensure_directory(task_path)

    # Handle template expansion
    if template:
        # Support template/task format
        if "/" in template:
            template_name, template_task = template.split("/", 1)
            template_task_path = workspace_path / "templates" / template_name / template_task
        else:
            # Try to find a single task template
            template_path = workspace_path / "templates" / template
            if template_path.exists():
                # Look for single task directory
                task_dirs = [d for d in template_path.iterdir() if d.is_dir()]
                if len(task_dirs) == 1:
                    template_task_path = task_dirs[0]
                else:
                    click.echo(
                        f"Error: Template '{template}' contains multiple tasks. Specify as 'template/task'.",
                        err=True,
                    )
                    return
            else:
                click.echo(f"Error: Template '{template}' not found.", err=True)
                return

        if not template_task_path.exists():
            click.echo(f"Error: Template task '{template}' not found.", err=True)
            return

        click.echo(f"Using template: {template}")

        # Get template variables from user
        variables = get_template_variables_from_user(
            task_name, non_interactive=dry_run or force or non_interactive
        )
        variables["PROJECT_NAME"] = project_name
        variables["TASK_NAME"] = task_name

        # Expand template task
        try:
            expand_template_directory(template_task_path, task_path, variables)
            click.echo(f"Created task '{project_name}/{task_name}' from template '{template}'")
        except Exception as e:
            click.echo(f"Error expanding template: {e}", err=True)
            return
    else:
        # Create basic instruction.yaml
        instruction_content = f"""name: {task_name}
task_type: human
description: "Task description here"
auto_merge: false
dependencies: []
inputs: []
outputs: []
note: "Please edit this instruction.yaml to complete the task definition"
"""

        instruction_path = task_path / "instruction.yaml"
        safe_write_file(instruction_path, instruction_content)

        click.echo(f"Created task: {project_name}/{task_name}")
        click.echo(f"  - {instruction_path}")
        click.echo("Please edit instruction.yaml to complete the task definition.")


def _expand_template_to_workspace(
    workspace_path: Path,
    template: str,
    force: bool,
    dry_run: bool,
    non_interactive: bool,
) -> None:
    """Expand template as project(s) to workspace."""
    template_path = workspace_path / "templates" / template

    if not template_path.exists():
        click.echo(f"Error: Template '{template}' not found.", err=True)
        return

    # Target should be projects directory
    projects_dir = workspace_path / "projects"
    target_path = projects_dir / template

    if target_path.exists() and not force:
        click.echo(
            f"Error: Project '{template}' already exists. Use --force to overwrite.", err=True
        )
        return

    if dry_run:
        click.echo(f"Would expand template '{template}' as project: {target_path}")
        # Show what would be created
        for item in template_path.rglob("*"):
            if item.is_file():
                relative_path = item.relative_to(template_path)
                target_file_path = target_path / relative_path
                click.echo(f"  Would create: {target_file_path}")
        return

    click.echo(f"Expanding template '{template}' as project...")

    # Get template variables
    variables = get_template_variables_from_user(
        template, non_interactive=dry_run or force or non_interactive
    )
    variables["PROJECT_NAME"] = template  # Use template name as project name

    try:
        # Ensure projects directory exists
        ensure_directory(projects_dir)

        # Expand template to projects directory as a new project
        expand_template_directory(template_path, target_path, variables)
        click.echo(f"✅ Template '{template}' expanded as project '{template}'")

        # List created tasks
        tasks = [d.name for d in target_path.iterdir() if d.is_dir() and not d.name.startswith(".")]
        if tasks:
            click.echo("Created tasks:")
            for task in tasks:
                click.echo(f"  - {template}/{task}")

    except Exception as e:
        click.echo(f"Error expanding template: {e}", err=True)
