"""Issue command for GitHub integration."""

import click

from ..main import Context, pass_context


@click.command()
@click.option("--project", help="Create parent issue for project")
@click.option("--task", help="Create child issue for specific task (project/task)")
@click.option("--all-tasks", help="Create child issues for all tasks in project")
@click.option("--assignee", help="Assign issue to user")
@click.option("--label", help="Comma-separated labels to apply")
@click.option("--dry-run", is_flag=True, help="Show what would be created without creating")
@pass_context
def issue(
    ctx: Context,
    project: str,
    task: str,
    all_tasks: str,
    assignee: str,
    label: str,
    dry_run: bool,
) -> None:
    """Create GitHub issues for projects and tasks."""
    workspace_path = ctx.workspace_path
    assert workspace_path is not None

    # Validate options
    options_count = sum(bool(x) for x in [project, task, all_tasks])
    if options_count != 1:
        click.echo("Error: Specify exactly one of --project, --task, or --all-tasks.", err=True)
        return

    if dry_run:
        click.echo("[DRY RUN] GitHub issue creation simulation:")

    if project:
        _create_project_issue(project, assignee, label, dry_run)
    elif task:
        _create_task_issue(task, assignee, label, dry_run)
    elif all_tasks:
        _create_all_tasks_issues(all_tasks, assignee, label, dry_run)


def _create_project_issue(
    project: str,
    assignee: str,
    label: str,
    dry_run: bool,
) -> None:
    """Create parent issue for project."""
    title = f"[PROJECT] {project}"

    if dry_run:
        click.echo(f"Would create project issue: {title}")
        if assignee:
            click.echo(f"  Assignee: {assignee}")
        if label:
            click.echo(f"  Labels: {label}")
    else:
        # TODO: Implement GitHub CLI integration
        click.echo("GitHub issue creation will be implemented in future version.")
        click.echo(f"Title: {title}")


def _create_task_issue(
    task: str,
    assignee: str,
    label: str,
    dry_run: bool,
) -> None:
    """Create child issue for specific task."""
    if "/" not in task:
        click.echo("Error: Task must be in format 'project/task'.", err=True)
        return

    title = f"[TASK] {task}"

    if dry_run:
        click.echo(f"Would create task issue: {title}")
        if assignee:
            click.echo(f"  Assignee: {assignee}")
        if label:
            click.echo(f"  Labels: {label}")
    else:
        # TODO: Implement GitHub CLI integration
        click.echo("GitHub issue creation will be implemented in future version.")
        click.echo(f"Title: {title}")


def _create_all_tasks_issues(
    project: str,
    assignee: str,
    label: str,
    dry_run: bool,
) -> None:
    """Create child issues for all tasks in project."""
    if dry_run:
        click.echo(f"Would create issues for all tasks in project: {project}")
        if assignee:
            click.echo(f"  Assignee: {assignee}")
        if label:
            click.echo(f"  Labels: {label}")
    else:
        # TODO: Implement GitHub CLI integration and task discovery
        click.echo("GitHub issue creation will be implemented in future version.")
        click.echo(f"Project: {project}")
