"""GitHub Pull Request Service for Warifuri automation.

This module provides GitHub PR creation functionality following Unix philosophy:
- Single responsibility: Handle only PR creation logic
- Composition: Use service objects for different concerns
- Testability: Each component can be tested independently
"""

from typing import Optional, Dict
import click
from ..context import Context
from ...core.github import check_github_cli, get_github_repo


class PullRequestService:
    """Service for creating GitHub pull requests."""

    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.workspace_path = ctx.workspace_path
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is required")

    def create_pr(
        self,
        task_name: str,
        branch_name: Optional[str] = None,
        commit_message: Optional[str] = None,
        pr_title: Optional[str] = None,
        pr_body: Optional[str] = None,
        base_branch: str = "main",
        draft: bool = False,
        auto_merge: bool = False,
        merge_method: str = "merge",
        dry_run: bool = False,
    ) -> bool:
        """Create a pull request for automated task execution.

        Returns:
            True if PR was created successfully, False otherwise.
        """
        # Validate GitHub environment
        if not self._validate_github_environment():
            return False

        # Get repository information
        repo = get_github_repo()
        if not repo:
            click.echo("❌ Could not determine GitHub repository", err=True)
            return False

        # Prepare PR details
        pr_details = self._prepare_pr_details(
            task_name, branch_name, commit_message, pr_title, pr_body
        )

        # Create branch and commit changes
        if not self._create_branch_and_commit(pr_details, dry_run):
            return False

        # Create the pull request
        if not self._create_github_pr(pr_details, base_branch, draft, dry_run):
            return False

        # Handle auto-merge if requested
        if auto_merge and not draft and not dry_run:
            self._setup_auto_merge(pr_details["branch_name"], merge_method)

        return True

    def _validate_github_environment(self) -> bool:
        """Validate GitHub CLI and authentication."""
        if not check_github_cli():
            click.echo("❌ GitHub CLI not found or not authenticated", err=True)
            click.echo("Please install and authenticate with: gh auth login", err=True)
            return False
        return True

    def _prepare_pr_details(
        self,
        task_name: str,
        branch_name: Optional[str],
        commit_message: Optional[str],
        pr_title: Optional[str],
        pr_body: Optional[str],
    ) -> Dict[str, str]:
        """Prepare pull request details with defaults."""
        return {
            "task_name": task_name,
            "branch_name": branch_name or f"warifuri/automation/{task_name}",
            "commit_message": commit_message or f"feat: automate task {task_name}",
            "pr_title": pr_title or f"Automate task: {task_name}",
            "pr_body": pr_body or f"Automated execution of task `{task_name}` via Warifuri.",
        }

    def _create_branch_and_commit(self, pr_details: Dict[str, str], dry_run: bool) -> bool:
        """Create branch and commit changes."""
        import subprocess

        branch_name = pr_details["branch_name"]
        commit_message = pr_details["commit_message"]

        if dry_run:
            click.echo(f"🔍 Would create branch: {branch_name}")
            click.echo(f"🔍 Would commit with message: {commit_message}")
            return True

        try:
            # Create and switch to new branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.workspace_path,
                check=True,
                capture_output=True,
            )

            # Add and commit changes
            subprocess.run(
                ["git", "add", "."],
                cwd=self.workspace_path,
                check=True,
                capture_output=True,
            )

            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=self.workspace_path,
                check=True,
                capture_output=True,
            )

            # Push to remote
            subprocess.run(
                ["git", "push", "origin", branch_name],
                cwd=self.workspace_path,
                check=True,
                capture_output=True,
            )

            click.echo(f"✅ Created and pushed branch: {branch_name}")
            return True

        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Git operation failed: {e}", err=True)
            return False

    def _create_github_pr(
        self, pr_details: Dict[str, str], base_branch: str, draft: bool, dry_run: bool
    ) -> bool:
        """Create the GitHub pull request."""
        import subprocess

        if dry_run:
            click.echo(f"🔍 Would create PR: {pr_details['pr_title']}")
            click.echo(f"🔍 From branch: {pr_details['branch_name']} to {base_branch}")
            click.echo(f"🔍 Draft: {draft}")
            return True

        try:
            cmd = [
                "gh",
                "pr",
                "create",
                "--title",
                pr_details["pr_title"],
                "--body",
                pr_details["pr_body"],
                "--base",
                base_branch,
            ]

            if draft:
                cmd.append("--draft")

            result = subprocess.run(
                cmd,
                cwd=self.workspace_path,
                check=True,
                capture_output=True,
                text=True,
            )

            pr_url = result.stdout.strip()
            click.echo(f"✅ Created pull request: {pr_url}")
            return True

        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Failed to create PR: {e}", err=True)
            return False

    def _setup_auto_merge(self, branch_name: str, merge_method: str) -> None:
        """Setup auto-merge for the pull request."""
        import subprocess

        try:
            subprocess.run(
                ["gh", "pr", "merge", branch_name, f"--{merge_method}", "--auto"],
                cwd=self.workspace_path,
                check=True,
                capture_output=True,
            )
            click.echo(f"✅ Enabled auto-merge with method: {merge_method}")

        except subprocess.CalledProcessError as e:
            click.echo(f"⚠️ Could not enable auto-merge: {e}", err=True)


class AutomationValidator:
    """Service for validating automation prerequisites."""

    def __init__(self, ctx: Context):
        self.ctx = ctx
        self.workspace_path = ctx.workspace_path
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is required")

    def validate_github_prerequisites(self) -> bool:
        """Validate GitHub prerequisites for PR creation."""
        # Check if git repository is configured
        import subprocess

        try:
            # Check if we're in a git repository
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.workspace_path,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            click.echo("❌ Not in a git repository", err=True)
            return False

        # TODO: Add more GitHub-specific checks (remote, auth, etc.)
        click.echo("✅ GitHub prerequisites validated")
        return True

    def validate_task_ready(self, task_name: str) -> bool:
        """Validate that a task is ready for automation."""
        from ...core.discovery import discover_all_projects, find_ready_tasks

        # Discover all projects and their tasks
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is required")

        projects = discover_all_projects(self.workspace_path)
        if not projects:
            click.echo("❌ No projects found in workspace", err=True)
            return False

        # Find all tasks from all projects
        all_tasks = []
        for project in projects:
            all_tasks.extend(project.tasks)

        # Find the specific task
        target_task = None
        for task in all_tasks:
            if task.name == task_name:
                target_task = task
                break

        if not target_task:
            click.echo(f"❌ Task '{task_name}' not found", err=True)
            return False

        # Check if task is ready
        ready_tasks = find_ready_tasks(projects)
        if target_task not in ready_tasks:
            click.echo(f"❌ Task '{task_name}' is not ready (missing dependencies)", err=True)
            return False

        click.echo(f"✅ Task '{task_name}' is ready for automation")
        return True

    def validate_workspace_clean(self) -> bool:
        """Validate that the workspace has no uncommitted changes."""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.workspace_path,
                check=True,
                capture_output=True,
                text=True,
            )

            if result.stdout.strip():
                click.echo("❌ Workspace has uncommitted changes", err=True)
                click.echo("Please commit or stash changes before creating PR", err=True)
                return False

            click.echo("✅ Workspace is clean")
            return True

        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Could not check git status: {e}", err=True)
            return False
