"""Automation command for GitHub Actions integration."""

import json
from typing import Optional

import click

from ..context import Context, pass_context
from ...core.discovery import discover_all_projects
from ...core.types import TaskStatus, TaskType
from ...core.github import (
    check_github_cli,
    get_github_repo,
    is_working_directory_clean,
    create_branch,
    commit_changes,
    push_branch,
    create_pull_request,
    enable_auto_merge,
    merge_pull_request,
)


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
    workspace_path = ctx.workspace_path
    assert workspace_path is not None

    # Discover projects
    projects = discover_all_projects(workspace_path)

    if project:
        projects = [p for p in projects if p.name == project]

    automation_tasks = []

    for proj in projects:
        for task in proj.tasks:
            # Apply filters
            if ready_only and task.status != TaskStatus.READY:
                continue

            if machine_only and task.task_type != TaskType.MACHINE:
                continue

            # Check for auto_merge configuration
            auto_merge_config = None
            for config_file in ["auto_merge.yaml", "auto_merge.yml"]:
                task_config = task.path / config_file
                project_config = proj.path / config_file

                if task_config.exists():
                    auto_merge_config = str(task_config)
                    break
                elif project_config.exists():
                    auto_merge_config = str(project_config)
                    break

            task_info = {
                "project": proj.name,
                "name": task.name,
                "full_name": task.full_name,
                "task_type": task.task_type.value,
                "status": task.status.value,
                "auto_merge_config": auto_merge_config,
                "automation_ready": (
                    task.status == TaskStatus.READY
                    and task.task_type == TaskType.MACHINE
                    and auto_merge_config is not None
                ),
            }

            automation_tasks.append(task_info)

    if format == "json":
        click.echo(json.dumps(automation_tasks, indent=2))
    else:
        if not automation_tasks:
            click.echo("No tasks found matching criteria.")
            return

        click.echo("Automation-Ready Tasks:")
        click.echo("=" * 50)

        for task_info in automation_tasks:
            status_icon = "🤖" if task_info["automation_ready"] else "⏸️"
            auto_merge_icon = "✅" if task_info["auto_merge_config"] else "❌"

            click.echo(f"{status_icon} {task_info['full_name']}")
            click.echo(f"   Type: {task_info['task_type']}")
            click.echo(f"   Status: {task_info['status']}")
            click.echo(f"   Auto-merge: {auto_merge_icon}")
            if task_info["auto_merge_config"]:
                click.echo(f"   Config: {task_info['auto_merge_config']}")
            click.echo()


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
    workspace_path = ctx.workspace_path
    assert workspace_path is not None

    # Parse task name
    if "/" not in task_name:
        click.echo("Error: Task name must be in format 'project/task'", err=True)
        raise click.Abort()

    project_name, task_name_only = task_name.split("/", 1)

    # Find the task
    projects = discover_all_projects(workspace_path)
    target_project = None
    target_task = None

    for project in projects:
        if project.name == project_name:
            target_project = project
            for task in project.tasks:
                if task.name == task_name_only:
                    target_task = task
                    break
            break

    if not target_project or not target_task:
        click.echo(f"Error: Task '{task_name}' not found", err=True)
        raise click.Abort()

    # Check automation conditions
    can_automate = True
    issues = []

    # Check task type
    if target_task.task_type != TaskType.MACHINE:
        can_automate = False
        issues.append(f"Task type is '{target_task.task_type.value}', expected 'machine'")

    # Check task status
    if target_task.status != TaskStatus.READY:
        can_automate = False
        issues.append(f"Task status is '{target_task.status.value}', expected 'ready'")

    # Check for auto_merge configuration
    auto_merge_config = None
    for config_file in ["auto_merge.yaml", "auto_merge.yml"]:
        task_config = target_task.path / config_file
        project_config = target_project.path / config_file

        if task_config.exists():
            auto_merge_config = task_config
            break
        elif project_config.exists():
            auto_merge_config = project_config
            break

    if not auto_merge_config:
        can_automate = False
        issues.append("No auto_merge.yaml configuration found")

    # Output results
    if check_only:
        result = {
            "task": task_name,
            "can_automate": can_automate,
            "issues": issues,
            "auto_merge_config": str(auto_merge_config) if auto_merge_config else None,
        }
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Task: {task_name}")
        click.echo(f"Can automate: {'✅ Yes' if can_automate else '❌ No'}")

        if auto_merge_config:
            click.echo(f"Auto-merge config: {auto_merge_config}")

        if issues:
            click.echo("\nIssues preventing automation:")
            for issue in issues:
                click.echo(f"  - {issue}")

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
    workspace_path = ctx.workspace_path
    assert workspace_path is not None

    # Check GitHub CLI
    if not check_github_cli():
        click.echo("❌ GitHub CLI not found or not authenticated", err=True)
        click.echo("Please install and authenticate with: gh auth login", err=True)
        raise click.Abort()

    # Get repository
    repo = get_github_repo()
    if not repo:
        click.echo("❌ Could not determine GitHub repository", err=True)
        raise click.Abort()

    # Parse task name
    if "/" not in task_name:
        click.echo("Error: Task name must be in format 'project/task'", err=True)
        raise click.Abort()

    project_name, task_name_only = task_name.split("/", 1)

    # Find the task
    projects = discover_all_projects(workspace_path)
    target_project = None
    target_task = None

    for project in projects:
        if project.name == project_name:
            target_project = project
            for task in project.tasks:
                if task.name == task_name_only:
                    target_task = task
                    break
            break

    if not target_project or not target_task:
        click.echo(f"❌ Task '{task_name}' not found", err=True)
        raise click.Abort()

    # Check if working directory is clean
    if not is_working_directory_clean():
        click.echo("❌ Working directory has uncommitted changes", err=True)
        click.echo("Please commit or stash your changes first", err=True)
        raise click.Abort()

    # Generate defaults
    if not branch_name:
        branch_name = f"warifuri/{task_name.replace('/', '-')}"

    if not commit_message:
        commit_message = f"feat: automate task {task_name}\n\nAI-AUTO: yes"

    if not pr_title:
        pr_title = f"🤖 Automate task: {task_name}"

    if not pr_body:
        pr_body = f"""## Automated Task Execution

**Task**: `{task_name}`
**Type**: {target_task.task_type.value}
**Status**: {target_task.status.value}

### Description
{target_task.instruction.description or "No description provided"}

### Dependencies
{chr(10).join(f"- {dep}" for dep in target_task.instruction.dependencies) if target_task.instruction.dependencies else "None"}

### Execution Command
```bash
warifuri run --task {task_name}
```

---
*This PR was created automatically by warifuri CLI*
"""

    if dry_run:
        click.echo("🔍 DRY RUN - Would perform the following actions:")
        click.echo(f"  1. Create branch: {branch_name}")
        click.echo(f"  2. Execute task: {task_name}")
        click.echo(f"  3. Commit changes: {commit_message}")
        click.echo("  4. Push branch to origin")
        click.echo(f"  5. Create PR: {pr_title}")
        if auto_merge:
            click.echo(f"  6. Enable auto-merge ({merge_method})")
        return

    # Execute the workflow
    try:
        click.echo(f"🚀 Starting automated PR creation for task: {task_name}")

        # 1. Create and checkout branch
        click.echo(f"📝 Creating branch: {branch_name}")
        if not create_branch(branch_name):
            raise click.ClickException("Failed to create branch")

        # 2. Execute the task (simulate for now)
        click.echo(f"⚙️  Executing task: {task_name}")
        # TODO: Actually run the task here
        # For now, we'll create a placeholder file to demonstrate
        output_file = workspace_path / "output" / f"{task_name.replace('/', '_')}_result.txt"
        output_file.parent.mkdir(exist_ok=True)
        output_file.write_text(
            f"Automated execution result for {task_name}\nTimestamp: {ctx.timestamp}"
        )

        # 3. Commit changes
        click.echo("📋 Committing changes")
        if not commit_changes(commit_message):
            raise click.ClickException("Failed to commit changes")

        # 4. Push branch
        click.echo("⬆️  Pushing branch to remote")
        if not push_branch(branch_name):
            raise click.ClickException("Failed to push branch")

        # 5. Create PR
        click.echo("🔄 Creating pull request")
        pr_url = create_pull_request(
            title=pr_title,
            body=pr_body,
            base_branch=base_branch,
            draft=draft,
            auto_merge=auto_merge and not draft,
        )

        if not pr_url:
            raise click.ClickException("Failed to create pull request")

        click.echo(f"✅ Successfully created PR: {pr_url}")

        # 6. Enable auto-merge if requested and not draft
        if auto_merge and not draft:
            click.echo(f"🔄 Enabling auto-merge ({merge_method})")
            if enable_auto_merge(pr_url, merge_method):
                click.echo("✅ Auto-merge enabled")
            else:
                click.echo("⚠️  Failed to enable auto-merge")

    except Exception as e:
        click.echo(f"❌ Error during PR creation: {e}", err=True)
        raise click.Abort() from e


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
    if not check_github_cli():
        click.echo("❌ GitHub CLI not found or not authenticated", err=True)
        raise click.Abort()

    if dry_run:
        click.echo(f"🔍 DRY RUN - Would merge PR: {pr_url}")
        click.echo(f"  Method: {merge_method}")
        return

    click.echo(f"🔄 Merging PR: {pr_url}")

    if merge_pull_request(pr_url, merge_method):
        click.echo("✅ PR merged successfully")
    else:
        click.echo("❌ Failed to merge PR", err=True)
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
