"""Issue command for GitHub integration."""

import json
import subprocess
from typing import List, Optional

import click

from ..context import Context, pass_context
from ...core.discovery import discover_all_projects, find_task_by_name


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

    # Check if GitHub CLI is available
    if not _check_gh_cli():
        click.echo("Error: GitHub CLI (gh) is not installed or not available in PATH.", err=True)
        click.echo("Please install GitHub CLI: https://cli.github.com/", err=True)
        return

    # Validate options
    options_count = sum(bool(x) for x in [project, task, all_tasks])
    if options_count != 1:
        click.echo("Error: Specify exactly one of --project, --task, or --all-tasks.", err=True)
        return

    # Discover projects for task lookups
    projects = discover_all_projects(workspace_path)

    if dry_run:
        click.echo("[DRY RUN] GitHub issue creation simulation:")

    if project:
        _create_project_issue(projects, project, assignee, label, dry_run)
    elif task:
        _create_task_issue(projects, task, assignee, label, dry_run)
    elif all_tasks:
        _create_all_tasks_issues(projects, all_tasks, assignee, label, dry_run)


def _check_gh_cli() -> bool:
    """Check if GitHub CLI is available."""
    try:
        result = subprocess.run(["gh", "--version"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def _check_existing_issue(title: str) -> bool:
    """Check if an issue with similar title already exists."""
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--search", f'"{title}" in:title', "--json", "title"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            issues = json.loads(result.stdout)
            return len(issues) > 0
        return False
    except (subprocess.SubprocessError, json.JSONDecodeError):
        return False


def _create_github_issue(
    title: str,
    body: str,
    assignee: Optional[str] = None,
    labels: Optional[str] = None,
    dry_run: bool = False,
) -> bool:
    """Create GitHub issue using gh CLI."""
    if dry_run:
        click.echo(f"Would create issue: {title}")
        if assignee:
            click.echo(f"  Assignee: {assignee}")
        if labels:
            click.echo(f"  Labels: {labels}")
        click.echo(f"  Body: {body[:100]}...")
        return True

    # Check for duplicates
    if _check_existing_issue(title):
        click.echo(f"⚠️  Issue with similar title already exists: {title}")
        return False

    cmd = ["gh", "issue", "create", "--title", title, "--body", body]

    if assignee:
        cmd.extend(["--assignee", assignee])

    if labels:
        cmd.extend(["--label", labels])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            click.echo(f"✅ Created issue: {title}")
            issue_url = result.stdout.strip()
            click.echo(f"   {issue_url}")
            return True
        else:
            click.echo(f"❌ Failed to create issue: {title}")
            click.echo(f"   Error: {result.stderr}")
            return False
    except subprocess.SubprocessError as e:
        click.echo(f"❌ GitHub CLI error: {e}")
        return False


def _create_project_issue(
    projects: List,
    project: str,
    assignee: Optional[str],
    label: Optional[str],
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

    _create_github_issue(title, body, assignee, label, dry_run)


def _create_task_issue(
    projects: List,
    task: str,
    assignee: Optional[str],
    label: Optional[str],
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

    # Build issue body
    body_lines = [
        f"# Task: {task}",
        "",
        "## Description",
        target_task.instruction.description,
        "",
        f"**Type**: {target_task.task_type.value}",
        f"**Status**: {target_task.status.value}",
        f"**Completed**: {'Yes' if target_task.is_completed else 'No'}",
        "",
    ]

    if target_task.instruction.dependencies:
        body_lines.extend(["## Dependencies", ""])
        for dep in target_task.instruction.dependencies:
            body_lines.append(f"- {dep}")
        body_lines.append("")

    if target_task.instruction.inputs:
        body_lines.extend(["## Inputs", ""])
        for inp in target_task.instruction.inputs:
            body_lines.append(f"- `{inp}`")
        body_lines.append("")

    if target_task.instruction.outputs:
        body_lines.extend(["## Outputs", ""])
        for out in target_task.instruction.outputs:
            body_lines.append(f"- `{out}`")
        body_lines.append("")

    if target_task.instruction.note:
        body_lines.extend(["## Notes", target_task.instruction.note, ""])

    body_lines.extend(
        [
            "## Usage",
            f"Use `warifuri run --task {task}` to execute this task.",
            "",
            "---",
            "*Created by warifuri CLI*",
        ]
    )

    body = "\n".join(body_lines)

    _create_github_issue(title, body, assignee, label, dry_run)


def _create_all_tasks_issues(
    projects: List,
    project: str,
    assignee: Optional[str],
    label: Optional[str],
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

    success_count = 0
    for task in target_project.tasks:
        task_full_name = f"{project}/{task.name}"
        _create_task_issue(projects, task_full_name, assignee, label, dry_run)
        if not dry_run:
            success_count += 1

    if not dry_run:
        click.echo(f"✅ Created {success_count} task issues for project '{project}'")
