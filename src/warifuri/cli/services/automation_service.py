"""Automation services following Unix philosophy.

This module provides automation-related services that handle business logic
extracted from CLI commands.
"""

import json
from typing import Any, Dict, List, Optional, Tuple

import click

from ...core.discovery import discover_all_projects, find_ready_tasks
from ...core.execution import execute_task
from ...core.types import Task, TaskStatus, TaskType
from ..context import Context


class AutomationListService:
    """Service for listing automation status."""

    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.workspace_path = ctx.workspace_path
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is required")

    def list_tasks(self, format: str) -> None:
        """List automation status for all tasks."""
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is required")

        projects = discover_all_projects(self.workspace_path)
        if not projects:
            click.echo("No projects found in workspace")
            return

        # Collect all tasks
        all_tasks = []
        for project in projects:
            all_tasks.extend(project.tasks)

        if not all_tasks:
            click.echo("No tasks found in any project")
            return

        # Determine ready tasks
        ready_tasks = find_ready_tasks(projects)

        # Prepare task information
        task_info = []
        for project in projects:
            for task in project.tasks:
                info = {
                    "project": project.name,
                    "task": task.name,
                    "full_name": f"{project.name}/{task.name}",
                    "status": "ready" if task in ready_tasks else "blocked",
                    "dependencies": len(task.instruction.dependencies)
                    if task.instruction.dependencies
                    else 0,
                    "path": str(task.path.relative_to(self.workspace_path))
                    if self.workspace_path
                    else str(task.path),
                }
                task_info.append(info)

        # Output in requested format
        if format == "json":
            click.echo(json.dumps(task_info, indent=2))
        else:
            self._print_table(task_info)

    def _print_table(self, task_info: List[Dict[str, Any]]) -> None:
        """Print tasks in table format."""
        if not task_info:
            return

        # Calculate column widths
        max_project = max(len(task["project"]) for task in task_info)
        max_task = max(len(task["task"]) for task in task_info)
        max_status = max(len(task["status"]) for task in task_info)

        # Header
        header = f"{'Project':<{max_project}} {'Task':<{max_task}} {'Status':<{max_status}} Deps"
        click.echo(header)
        click.echo("-" * len(header))

        # Tasks
        for task in task_info:
            status_icon = "✅" if task["status"] == "ready" else "⏳"
            click.echo(
                f"{task['project']:<{max_project}} "
                f"{task['task']:<{max_task}} "
                f"{status_icon} {task['status']:<{max_status - 2}} "
                f"{task['dependencies']}"
            )

    def list_automation_tasks(
        self, ready_only: bool = False, machine_only: bool = False, project: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tasks suitable for automation with filtering options."""
        from ...core.types import TaskStatus, TaskType

        # Discover projects
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is required")
        projects = discover_all_projects(self.workspace_path)

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

        return automation_tasks

    def output_results(self, automation_tasks: List[Dict[str, Any]], format: str) -> None:
        """Output automation tasks in specified format."""
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


class AutomationCheckService:
    """Service for checking task automation readiness."""

    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.workspace_path = ctx.workspace_path
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is required")

    def check_task(self, task_name: str, verbose: bool) -> None:
        """Check if a task is ready for automation."""
        # Parse task name
        if "/" not in task_name:
            click.echo("Error: Task name must be in format 'project/task'", err=True)
            raise click.Abort()

        project_name, task_name_only = task_name.split("/", 1)

        # Find projects and task
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is required")

        projects = discover_all_projects(self.workspace_path)
        project = None
        task = None

        for p in projects:
            if p.name == project_name:
                project = p
                for t in p.tasks:
                    if t.name == task_name_only:
                        task = t
                        break
                break

        if not project:
            click.echo(f"❌ Project '{project_name}' not found", err=True)
            raise click.Abort()

        if not task:
            click.echo(
                f"❌ Task '{task_name_only}' not found in project '{project_name}'", err=True
            )
            raise click.Abort()

        # Check readiness
        all_tasks = []
        for p in projects:
            all_tasks.extend(p.tasks)

        ready_tasks = find_ready_tasks(projects)
        is_ready = task in ready_tasks

        # Basic status
        if is_ready:
            click.echo(f"✅ Task '{task_name}' is ready for automation")
        else:
            click.echo(f"⏳ Task '{task_name}' is not ready for automation")

        # Verbose information
        if verbose:
            self._show_verbose_info(task, all_tasks, is_ready)

    def _show_verbose_info(self, task: Task, all_tasks: List[Task], is_ready: bool) -> None:
        """Show detailed task information."""
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is required")

        # Get projects for dependency checking
        projects = discover_all_projects(self.workspace_path)
        click.echo("\n📋 Task Details:")
        click.echo(f"  Name: {task.name}")
        click.echo(f"  Project: {task.project}")
        click.echo(f"  Path: {task.path}")
        click.echo(f"  Status: {'Ready' if is_ready else 'Blocked'}")

        if task.instruction.dependencies:
            click.echo(f"\n🔗 Dependencies ({len(task.instruction.dependencies)}):")
            # Get projects for dependency checking
            if self.workspace_path is None:
                raise click.ClickException("Workspace path is required")
            projects = discover_all_projects(self.workspace_path)
            for dep in task.instruction.dependencies:
                # Find dependency task
                dep_task = None
                for t in all_tasks:
                    if f"{t.project}/{t.name}" == dep or t.name == dep:
                        dep_task = t
                        break
                if dep_task:
                    dep_ready = dep_task in find_ready_tasks(projects)
                    status_icon = "✅" if dep_ready else "❌"
                    click.echo(f"  {status_icon} {dep}")
                else:
                    click.echo(f"  ❓ {dep} (not found)")
        else:
            click.echo("\n🔗 Dependencies: None")

        # Check for blocking dependencies
        if not is_ready and task.instruction.dependencies:
            click.echo("\n⚠️  Task is blocked by unfinished dependencies")
            click.echo("   Run 'warifuri graph' to see the full dependency tree")

    def check_task_automation(self, task_name: str) -> Tuple[bool, List[str], Optional[str]]:
        """Check if a task can be automated and return validation results."""
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is required")
        projects = discover_all_projects(self.workspace_path)

        # Parse task name
        if "/" not in task_name:
            click.echo("Error: Task name must be in format 'project/task'", err=True)
            raise click.Abort()

        project_name, task_name_only = task_name.split("/", 1)

        # Find the task
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

        # Check task type and status
        if target_task.task_type != TaskType.MACHINE:
            can_automate = False
            issues.append(f"Task type is '{target_task.task_type.value}', expected 'machine'")

        if target_task.status != TaskStatus.READY:
            can_automate = False
            issues.append(f"Task status is '{target_task.status.value}', expected 'ready'")

        # Check for auto_merge configuration
        auto_merge_config = None
        for config_file in ["auto_merge.yaml", "auto_merge.yml"]:
            task_config = target_task.path / config_file
            project_config = target_project.path / config_file

            if task_config.exists():
                auto_merge_config = str(task_config)
                break
            elif project_config.exists():
                auto_merge_config = str(project_config)
                break

        if not auto_merge_config:
            can_automate = False
            issues.append("No auto_merge.yaml configuration found")

        return can_automate, issues, auto_merge_config

    def output_check_results(
        self,
        task_name: str,
        can_automate: bool,
        issues: List[str],
        auto_merge_config: Optional[str],
        check_only: bool,
    ) -> None:
        """Output the results of task automation check."""
        if check_only:
            result = {
                "task": task_name,
                "can_automate": can_automate,
                "issues": issues,
                "auto_merge_config": auto_merge_config,
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


class TaskExecutionService:
    """Service for executing tasks safely."""

    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.workspace_path = ctx.workspace_path
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is required")

    def execute_task_safely(self, task_name: str) -> bool:
        """Execute a task if it's ready.

        Returns:
            True if task executed successfully, False otherwise.
        """
        # Parse task name
        if "/" not in task_name:
            return False

        project_name, task_name_only = task_name.split("/", 1)

        # Find the task
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is required")

        projects = discover_all_projects(self.workspace_path)
        task = None

        for project in projects:
            if project.name == project_name:
                for t in project.tasks:
                    if t.name == task_name_only:
                        task = t
                        break
                break

        if not task:
            return False

        # Get all tasks for dependency checking
        all_tasks = []
        for p in projects:
            all_tasks.extend(p.tasks)

        # Execute task
        try:
            result = execute_task(task)
            return bool(result)
        except Exception:
            return False

    def list_automation_tasks(
        self, ready_only: bool = False, machine_only: bool = False, project: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List tasks suitable for automation with filtering options."""
        from ...core.types import TaskStatus, TaskType

        # Discover projects
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is required")
        projects = discover_all_projects(self.workspace_path)

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

        return automation_tasks

    def output_results(self, automation_tasks: List[Dict[str, Any]], format: str) -> None:
        """Output automation tasks in specified format."""
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

    def merge_pr(self, pr_url: str, merge_method: str) -> bool:
        """Merge a pull request using the specified method.

        Args:
            pr_url: URL of the pull request to merge
            merge_method: Merge method (merge, squash, rebase)

        Returns:
            True if merge successful, False otherwise
        """
        # TODO: Implement PR merging logic using GitHub API
        click.echo(f"🔄 Merging PR: {pr_url} using {merge_method}")
        click.echo("⚠️  PR merging not yet implemented")
        return False
