"""Automation command for GitHub Actions integration."""

import json
from typing import Optional

import click

from ..context import Context, pass_context
from ..services.automation_service import (
    AutomationListService,
    AutomationCheckService,
    TaskExecutionService,
)
from ..services.pr_service import PullRequestService, AutomationValidator


@click.command()
@click.option("--ready-only", is_flag=True, help="Only show ready tasks")
@click.option("--machine-only", is_flag=True, help="Only show machine tasks")
@click.option(
    "--format", type=click.Choice(["plain", "json"]), default="plain", help="Output format"
)
@click.option("--project", help="Filter by project name")
@pass_context
def automation_list(
    ctx: Context,
    ready_only: bool,
    machine_only: bool,
    format: str,
    project: Optional[str],
) -> None:
    """List tasks suitable for automation."""
    service = AutomationListService(ctx)
    automation_tasks = service.list_automation_tasks(
        ready_only=ready_only,
        machine_only=machine_only,
        project=project,
    )

    service.output_results(automation_tasks, format)


@click.command()
@click.argument("task_name")
@click.option("--check-only", is_flag=True, help="Only check if task can be automated")
@pass_context
def check_automation(
    ctx: Context,
    task_name: str,
    check_only: bool,
) -> None:
    """Check if a task can be automated."""
    service = AutomationCheckService(ctx)
    can_automate, issues, auto_merge_config = service.check_task_automation(task_name)

    service.output_check_results(
        task_name=task_name,
        can_automate=can_automate,
        issues=issues,
        auto_merge_config=auto_merge_config,
        check_only=check_only,
    )

    if not can_automate:
        raise click.Abort()


@click.command()
@click.argument("task_name")
@click.option("--branch-name", help="Custom branch name (default: auto-generated)")
@click.option("--commit-message", help="Custom commit message")
@click.option("--pr-title", help="Custom PR title")
@click.option("--pr-body", help="Custom PR body")
@click.option("--base-branch", default="main", help="Base branch for PR")
@click.option("--draft", is_flag=True, help="Create as draft PR")
@click.option("--auto-merge", is_flag=True, help="Enable auto-merge")
@click.option(
    "--merge-method",
    type=click.Choice(["merge", "squash", "rebase"]),
    default="squash",
    help="Merge method",
)
@click.option("--dry-run", is_flag=True, help="Show what would be done without executing")
@pass_context
def create_pr(
    ctx: Context,
    task_name: str,
    branch_name: Optional[str],
    commit_message: Optional[str],
    pr_title: Optional[str],
    pr_body: Optional[str],
    base_branch: str,
    draft: bool,
    auto_merge: bool,
    merge_method: str,
    dry_run: bool,
) -> None:
    """Create a pull request for automated task execution."""
    # Validate prerequisites
    validator = AutomationValidator(ctx)
    if not validator.validate_github_prerequisites():
        raise click.Abort()
    if not validator.validate_workspace_clean():
        raise click.Abort()

    # Create PR using service
    pr_service = PullRequestService(ctx)
    success = pr_service.create_pr(
        task_name=task_name,
        branch_name=branch_name,
        commit_message=commit_message,
        pr_title=pr_title,
        pr_body=pr_body,
        base_branch=base_branch,
        draft=draft,
        auto_merge=auto_merge,
        merge_method=merge_method,
        dry_run=dry_run,
    )

    if not success:
        raise click.Abort()


@click.command()
@click.argument("pr_url")
@click.option(
    "--merge-method",
    type=click.Choice(["merge", "squash", "rebase"]),
    default="squash",
    help="Merge method",
)
@click.option("--dry-run", is_flag=True, help="Show what would be done without executing")
@pass_context
def merge_pr(
    ctx: Context,
    pr_url: str,
    merge_method: str,
    dry_run: bool,
) -> None:
    """Merge a pull request immediately."""
    validator = AutomationValidator(ctx)
    if not validator.validate_github_prerequisites():
        raise click.Abort()

    if dry_run:
        click.echo(f"🔍 DRY RUN - Would merge PR: {pr_url}")
        click.echo(f"  Method: {merge_method}")
        return

    task_service = TaskExecutionService(ctx)
    success = task_service.merge_pr(pr_url, merge_method)

    if not success:
        raise click.Abort()


# Add subcommands to a group
@click.group()
def automation() -> None:
    """Automation and GitHub Actions integration commands."""
    pass


automation.add_command(automation_list, name="list")
automation.add_command(check_automation, name="check")
automation.add_command(create_pr, name="create-pr")
automation.add_command(merge_pr, name="merge-pr")
