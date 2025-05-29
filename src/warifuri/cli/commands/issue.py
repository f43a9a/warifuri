"""Issue command for GitHub integration."""


import click

from ..context import Context, pass_context
from typing import List, Optional
from ...core.discovery import discover_all_projects, find_task_by_name
from ...core.types import Project
from ...core.github import (
    check_github_cli,
    create_issue_safe,
    ensure_labels_exist,
    get_github_repo,
    format_task_issue_body,
)


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

    # Check if GitHub CLI is available
    if not check_github_cli():
        click.echo("Error: GitHub CLI (gh) is not installed or not authenticated.", err=True)
        click.echo("Please install GitHub CLI: https://cli.github.com/", err=True)
        click.echo("And authenticate: gh auth login", err=True)
        return

    # Get GitHub repository
    repo = get_github_repo()
    if not repo:
        click.echo("Error: Could not detect GitHub repository.", err=True)
        click.echo("Make sure you're in a Git repository with a GitHub remote.", err=True)
        return

    # Validate options
    options_count = sum(bool(x) for x in [project, task, all_tasks])
    if options_count != 1:
        click.echo("Error: Specify exactly one of --project, --task, or --all-tasks.", err=True)
        return

    # Discover projects for task lookups - handle circular dependencies gracefully
    try:
        projects = discover_all_projects(workspace_path)
    except Exception as e:
        click.echo(f"Warning: Error during project discovery: {e}", err=True)
        click.echo("Attempting to continue with limited functionality...", err=True)
        projects = []

    if dry_run:
        click.echo("[DRY RUN] GitHub issue creation simulation:")

    # Parse labels if provided
    labels = label.split(",") if label else []

    if project:
        _create_project_issue(projects, project, assignee, labels, repo, dry_run)
    elif task:
        _create_task_issue(projects, task, assignee, labels, repo, dry_run)
    elif all_tasks:
        _create_all_tasks_issues(projects, all_tasks, assignee, labels, repo, dry_run)


def _create_project_issue(
    projects: List[Project],
    project: str,
    assignee: Optional[str],
    labels: List[str],
    repo: str,
    dry_run: bool,
) -> None:
    """Create parent issue for project."""
    # Find project
    target_project = None
    for proj in projects:
        if proj.name == project:
            target_project = proj
            break

    if not target_project:
        click.echo(f"Error: Project '{project}' not found.", err=True)
        return

    title = f"[PROJECT] {project}"

    # Build issue body
    body_lines = [
        f"# Project: {project}",
        "",
        "## Overview",
        f"This is a parent issue for tracking the overall progress of the '{project}' project.",
        "",
        "## Tasks",
    ]

    # List all tasks in the project
    for task in target_project.tasks:
        status_emoji = (
            "✅" if task.is_completed else ("🔄" if task.status.value == "ready" else "⏸️")
        )
        body_lines.append(f"- {status_emoji} **{task.name}**: {task.instruction.description}")

    if not target_project.tasks:
        body_lines.append("- No tasks found in this project")

    body_lines.extend(
        [
            "",
            "## Usage",
            f"Use `warifuri run --task {project}` to run ready tasks from this project.",
            "",
            "---",
            "*Created by warifuri CLI*",
        ]
    )

    body = "\n".join(body_lines)

    # Ensure labels exist before creating issue
    if labels and not dry_run:
        ensure_labels_exist(repo, labels)

    success, url = create_issue_safe(
        title=title, body=body, labels=labels, assignee=assignee or "", repo=repo, dry_run=dry_run
    )

    if not dry_run and not success:
        click.echo(f"❌ Failed to create project issue for '{project}'", err=True)


def _create_task_issue(
    projects: List[Project],
    task: str,
    assignee: Optional[str],
    labels: List[str],
    repo: str,
    dry_run: bool,
) -> None:
    """Create child issue for specific task."""
    if "/" not in task:
        click.echo("Error: Task must be in format 'project/task'.", err=True)
        return

    project_name, task_name = task.split("/", 1)

    # Find task
    target_task = find_task_by_name(projects, project_name, task_name)
    if not target_task:
        click.echo(f"Error: Task '{task}' not found.", err=True)
        return

    title = f"[TASK] {task}"

    # Use the new GitHub module for body formatting
    body = format_task_issue_body(target_task, repo)

    # Ensure labels exist before creating issue
    if labels and not dry_run:
        ensure_labels_exist(repo, labels)

    success, url = create_issue_safe(
        title=title, body=body, labels=labels, assignee=assignee or "", repo=repo, dry_run=dry_run
    )

    if not dry_run and not success:
        click.echo(f"❌ Failed to create task issue for '{task}'", err=True)


def _create_all_tasks_issues(
    projects: List[Project],
    project: str,
    assignee: Optional[str],
    labels: List[str],
    repo: str,
    dry_run: bool,
) -> None:
    """Create child issues for all tasks in project."""
    # Find project
    target_project = None
    for proj in projects:
        if proj.name == project:
            target_project = proj
            break

    if not target_project:
        click.echo(f"Error: Project '{project}' not found.", err=True)
        return

    if not target_project.tasks:
        click.echo(f"No tasks found in project '{project}'.")
        return

    click.echo(f"Creating issues for {len(target_project.tasks)} tasks in project '{project}'...")

    # Ensure labels exist before creating issues
    if labels and not dry_run:
        ensure_labels_exist(repo, labels)

    success_count = 0
    for task in target_project.tasks:
        task_full_name = f"{project}/{task.name}"

        # For all-tasks, we call create_issue_safe directly to avoid recursion
        title = f"[TASK] {task_full_name}"
        body = format_task_issue_body(task, repo)

        success, url = create_issue_safe(
            title=title,
            body=body,
            labels=labels,
            assignee=assignee or "",
            repo=repo,
            dry_run=dry_run,
        )

        if success or dry_run:
            success_count += 1

    if dry_run:
        click.echo(f"Would create {success_count} task issues for project '{project}'")
    else:
        click.echo(
            f"✅ Successfully created {success_count}/{len(target_project.tasks)} task issues for project '{project}'"
        )
