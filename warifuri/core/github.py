"""GitHub integration module for warifuri."""

import json
import logging
import os
import subprocess
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from .types import Project, Task

logger = logging.getLogger(__name__)


def get_github_repo() -> Optional[str]:
    """Get current GitHub repository from git remote."""
    try:
        # Try to get from git remote
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"], capture_output=True, text=True, check=True
        )

        remote_url = result.stdout.strip()

        # Parse GitHub URL
        if "github.com" in remote_url:
            if remote_url.startswith("https://github.com/"):
                repo_path = remote_url.replace("https://github.com/", "").replace(".git", "")
            elif remote_url.startswith("git@github.com:"):
                repo_path = remote_url.replace("git@github.com:", "").replace(".git", "")
            else:
                return None

            return repo_path

    except subprocess.CalledProcessError:
        pass

    # Try environment variable
    return os.environ.get("GITHUB_REPOSITORY")


def check_github_cli() -> bool:
    """Check if GitHub CLI is installed and authenticated."""
    try:
        # Check if gh is installed
        subprocess.run(["gh", "--version"], capture_output=True, check=True)

        # Check if authenticated
        result = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        # Check both stdout and stderr for login status
        output = result.stdout + result.stderr
        return "Logged in to github.com" in output

    except (subprocess.CalledProcessError, FileNotFoundError):
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

    body_lines = [
        f"# Task: {full_name}",
        "",
    ]

    # Add parent issue link if available
    if parent_issue_url:
        body_lines.extend([f"**Parent Project**: {parent_issue_url}", ""])
    elif repo and hasattr(task, "project"):
        # Try to find parent issue automatically
        auto_parent = find_parent_issue(task.project, repo)
        if auto_parent:
            body_lines.extend([f"**Parent Project**: {auto_parent}", ""])

    body_lines.extend(
        [
            "## Description",
            task.instruction.description
            if task.instruction.description
            else "No description provided",
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
