"""GitHub integration module for warifuri."""

import html
import json
import logging
import os
import re
import subprocess
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from .types import Project, Task

logger = logging.getLogger(__name__)


def sanitize_github_url(url: str) -> Optional[str]:
    """Safely parse and validate GitHub URL."""
    if not url or not isinstance(url, str):
        return None

    url = url.strip()

    # Parse URL to validate it
    try:
        parsed = urlparse(url)

        # Only allow GitHub URLs
        if parsed.hostname not in ("github.com", "www.github.com"):
            return None

        # Validate the path format
        if parsed.scheme not in ("https", "http", "git", "ssh"):
            return None

        # Remove fragment and query parameters for security
        clean_path = parsed.path.rstrip("/")

        # Validate GitHub repo path format (owner/repo)
        if parsed.scheme in ("https", "http"):
            path_match = re.match(r"^/([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)(?:\.git)?/?$", clean_path)
        else:  # git/ssh
            path_match = re.match(r"^([a-zA-Z0-9._-]+)/([a-zA-Z0-9._-]+)(?:\.git)?/?$", clean_path)

        if not path_match:
            return None

        owner, repo = path_match.groups()
        return f"{owner}/{repo}"

    except Exception:
        return None


def get_github_repo() -> Optional[str]:
    """Get current GitHub repository from git remote."""
    try:
        # Try to get from git remote
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True
        )

        remote_url = result.stdout.strip()

        # Safely parse GitHub URL
        repo_path = sanitize_github_url(remote_url)
        if repo_path:
            return repo_path

    except subprocess.CalledProcessError:
        pass

    # Try environment variable
    env_repo = os.environ.get("GITHUB_REPOSITORY")
    if env_repo:
        # Validate environment variable format
        if re.match(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$", env_repo):
            return env_repo

    return None


def check_github_cli() -> bool:
    """Check if GitHub CLI is installed and authenticated."""
    try:
        # Check if gh is installed
        subprocess.run(["gh", "--version"], capture_output=True, check=True)

        # Check if authenticated
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        return result.returncode == 0

    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def create_branch(branch_name: str) -> bool:
    """Create and checkout a new git branch."""
    try:
        # Check if branch already exists
        result = subprocess.run(
            ["git", "branch", "--list", branch_name], capture_output=True, text=True
        )

        if result.stdout.strip():
            logger.info(f"Branch {branch_name} already exists, switching to it")
            subprocess.run(["git", "checkout", branch_name], check=True)
        else:
            logger.info(f"Creating new branch: {branch_name}")
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)

        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create/checkout branch {branch_name}: {e}")
        return False


def commit_changes(message: str, files: Optional[List[str]] = None) -> bool:
    """Commit changes to the current branch."""
    try:
        # Add files
        if files:
            for file_path in files:
                subprocess.run(["git", "add", file_path], check=True)
        else:
            subprocess.run(["git", "add", "."], check=True)

        # Check if there are changes to commit
        result = subprocess.run(["git", "diff", "--cached", "--exit-code"], capture_output=True)

        if result.returncode == 0:
            logger.info("No changes to commit")
            return True

        # Commit changes
        commit_result = subprocess.run(
            ["git", "commit", "-m", message], capture_output=True, text=True
        )

        if commit_result.returncode != 0:
            # Pre-commit hooks may have modified files, try adding and committing again
            logger.info("Pre-commit hooks modified files, adding changes and retrying commit")
            subprocess.run(["git", "add", "."], check=True)

            # Check again if there are changes after hook modifications
            result = subprocess.run(["git", "diff", "--cached", "--exit-code"], capture_output=True)

            if result.returncode == 0:
                logger.info("No changes to commit after pre-commit hook modifications")
                return True

            # Try commit again
            subprocess.run(["git", "commit", "-m", message], check=True)

        logger.info(f"Committed changes: {message}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to commit changes: {e}")
        return False


def push_branch(branch_name: str) -> bool:
    """Push branch to remote repository."""
    try:
        subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
        logger.info(f"Pushed branch: {branch_name}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to push branch {branch_name}: {e}")
        return False


def create_pull_request(
    title: str, body: str, base_branch: str = "main", draft: bool = False, auto_merge: bool = False
) -> Optional[str]:
    """Create a pull request using GitHub CLI."""
    try:
        cmd = ["gh", "pr", "create", "--title", title, "--body", body, "--base", base_branch]

        if draft:
            cmd.append("--draft")

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        pr_url = result.stdout.strip()

        logger.info(f"Created pull request: {pr_url}")

        # Enable auto-merge if requested
        if auto_merge and not draft:
            enable_auto_merge(pr_url)

        return pr_url

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create pull request: {e}")
        if e.stderr:
            logger.error(f"Error details: {e.stderr}")
        return None


def enable_auto_merge(pr_url: str, merge_method: str = "squash") -> bool:
    """Enable auto-merge for a pull request."""
    try:
        cmd = ["gh", "pr", "merge", pr_url, "--auto", f"--{merge_method}"]

        subprocess.run(cmd, check=True)
        logger.info(f"Enabled auto-merge for PR: {pr_url}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to enable auto-merge: {e}")
        return False


def merge_pull_request(pr_url: str, merge_method: str = "squash") -> bool:
    """Merge a pull request immediately."""
    try:
        cmd = ["gh", "pr", "merge", pr_url, f"--{merge_method}", "--delete-branch"]

        subprocess.run(cmd, check=True)
        logger.info(f"Merged pull request: {pr_url}")
        return True

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to merge pull request: {e}")
        return False


def get_current_branch() -> Optional[str]:
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, text=True, check=True
        )
        return result.stdout.strip()

    except subprocess.CalledProcessError:
        return None


def is_working_directory_clean() -> bool:
    """Check if the working directory has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
        )
        return len(result.stdout.strip()) == 0

    except subprocess.CalledProcessError:
        return False


def ensure_labels_exist(repo: str, labels: List[str]) -> Dict[str, bool]:
    """Ensure GitHub labels exist, create if missing."""
    results: Dict[str, bool] = {}

    if not labels:
        return results

    # Get list of all existing labels once
    try:
        list_result = subprocess.run(
            ["gh", "label", "list", "--repo", repo, "--json", "name"],
            capture_output=True,
            text=True,
            check=True,
        )

        import json

        existing_labels = {label_info["name"] for label_info in json.loads(list_result.stdout)}

    except Exception as e:
        logger.warning("Could not get existing labels: %s", e)
        existing_labels = set()

    for label in labels:
        if label in existing_labels:
            results[label] = True
            logger.debug("Label '%s' already exists", label)
        else:
            try:
                # Create label if missing
                logger.info("Creating missing label: %s", label)
                create_result = subprocess.run(
                    [
                        "gh",
                        "label",
                        "create",
                        label,
                        "--color",
                        "0969da",  # Blue color
                        "--description",
                        f"Auto-created by warifuri for {label}",
                        "--repo",
                        repo,
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if create_result.returncode == 0:
                    results[label] = True
                    logger.info("✅ Created label: %s", label)
                else:
                    results[label] = False
                    logger.warning(
                        "Failed to create label '%s': %s", label, create_result.stderr.strip()
                    )

            except Exception as e:
                logger.warning("Failed to process label '%s': %s", label, e)
                results[label] = False

    return results


def create_issue_safe(
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
    assignee: str = "",
    repo: str = "",
    dry_run: bool = False,
) -> Tuple[bool, Optional[str]]:
    """Create GitHub issue with safe label handling.

    Returns:
        Tuple of (success: bool, issue_url: Optional[str])
    """
    if dry_run:
        logger.info("[DRY RUN] Would create issue: %s", title)
        if labels:
            logger.info("  Labels: %s", ", ".join(labels))
        if assignee:
            logger.info("  Assignee: %s", assignee)
        return True, None

    # Check for duplicate issues
    if check_issue_exists(title, repo):
        logger.warning("⚠️  Issue with similar title already exists: %s", title)
        return False, None

    # Ensure labels exist before creating issue
    safe_labels = []
    if labels:
        label_results = ensure_labels_exist(repo, labels)
        safe_labels = [label for label, exists in label_results.items() if exists]

        if len(safe_labels) != len(labels):
            missing = [label for label, exists in label_results.items() if not exists]
            logger.warning("Could not create/verify labels: %s", missing)

    # Build command
    cmd = ["gh", "issue", "create", "--title", title, "--body", body]

    if safe_labels:
        cmd.extend(["--label", ",".join(safe_labels)])

    if assignee:
        cmd.extend(["--assignee", assignee])

    if repo:
        cmd.extend(["--repo", repo])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issue_url = result.stdout.strip()
        logger.info("✅ Created issue: %s", title)
        logger.info("   %s", issue_url)
        return True, issue_url

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.strip() if e.stderr else str(e)
        logger.error("❌ Failed to create issue: %s", title)
        logger.error("   Error: %s", error_msg)
        return False, None


def check_issue_exists(title: str, repo: str) -> bool:
    """Check if an issue with similar title already exists."""
    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                repo,
                "--search",
                f'"{title}" in:title',
                "--json",
                "title",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        issues = json.loads(result.stdout)

        # Check for exact or similar titles
        for issue in issues:
            if issue["title"] == title:
                return True

        return False

    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logger.warning("Could not check existing issues: %s", e)
        return False


def format_task_issue_body(task: "Task", repo: str = "", parent_issue_url: str = "") -> str:
    """Format task issue body in Markdown with optional parent linking."""
    # Get task full name
    full_name = f"{task.project}/{task.name}" if hasattr(task, "project") else task.name

    # Sanitize inputs to prevent HTML injection
    safe_full_name = html.escape(full_name)
    safe_description = html.escape(task.instruction.description) if task.instruction.description else "No description provided"

    body_lines = [
        f"# Task: {safe_full_name}",
        "",
    ]

    # Add parent issue link if available
    if parent_issue_url:
        # Validate parent URL format
        if re.match(r"^https://github\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+/issues/\d+$", parent_issue_url):
            body_lines.extend([f"**Parent Project**: {parent_issue_url}", ""])
    elif repo and hasattr(task, "project"):
        # Try to find parent issue automatically
        auto_parent = find_parent_issue(task.project, repo)
        if auto_parent:
            body_lines.extend([f"**Parent Project**: {auto_parent}", ""])

    body_lines.extend(
        [
            "## Description",
            safe_description,
            "",
            f"**Type**: {task.task_type.value}",
            f"**Status**: {task.status.value}",
            f"**Completed**: {'Yes' if task.is_completed else 'No'}",
            "",
        ]
    )

    if task.instruction.dependencies:
        body_lines.extend(["## Dependencies", ""])
        for dep in task.instruction.dependencies:
            body_lines.append(f"- [ ] {dep}")
        body_lines.append("")

    if task.instruction.inputs:
        body_lines.extend(["## Input Files", ""])
        for input_file in task.instruction.inputs:
            body_lines.append(f"- `{input_file}`")
        body_lines.append("")

    if task.instruction.outputs:
        body_lines.extend(["## Expected Outputs", ""])
        for output_file in task.instruction.outputs:
            body_lines.append(f"- `{output_file}`")
        body_lines.append("")

    if task.instruction.note:
        body_lines.extend(["## Notes", task.instruction.note, ""])

    body_lines.extend(
        [
            "## Execution",
            f"Run with: `warifuri run --task {full_name}`",
            "",
            "--------",
            "",
            "Created by warifuri CLI",
        ]
    )

    return "\n".join(body_lines)


def format_project_issue_body(project: "Project") -> str:
    """Format project issue body in Markdown."""
    body_lines = [
        f"# Project: {project.name}",
        "",
        "## Overview",
        "",
        f"This is a parent issue for tracking the overall progress of the '{project.name}' project.",
        "",
        "## Tasks",
        "",
    ]

    # Add task list with status
    for task in project.tasks:
        if task.status.value == "completed":
            status_icon = "✅"
        elif task.status.value == "ready":
            status_icon = "🔄"
        else:
            status_icon = "⏸️"

        body_lines.append(
            f"• {status_icon} {task.name}: {task.instruction.description or 'No description'}"
        )

    body_lines.extend(
        [
            "",
            "## Usage",
            "",
            f"Use `warifuri run --task {project.name}` to run ready tasks from this project.",
            "",
            "--------",
            "",
            "Created by warifuri CLI",
        ]
    )

    return "\n".join(body_lines)


def find_parent_issue(project_name: str, repo: str) -> Optional[str]:
    """Find parent project issue URL if it exists."""
    try:
        parent_title = f"[PROJECT] {project_name}"
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                repo,
                "--search",
                f'"{parent_title}" in:title',
                "--json",
                "title,url",
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        issues = json.loads(result.stdout)

        for issue in issues:
            if issue["title"] == parent_title:
                return str(issue["url"])

        return None

    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        logger.warning("Could not find parent issue: %s", e)
        return None
