"""Tests for GitHub integration."""

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from warifuri.core.github import (
    get_github_repo,
    check_github_cli,
    is_working_directory_clean,
    create_branch,
    commit_changes,
    push_branch,
    create_pull_request,
    enable_auto_merge,
    merge_pull_request,
    # Add missing imports
    get_current_branch,
    ensure_labels_exist,
    _get_existing_labels,
    _create_label,
    create_issue_safe,
    check_issue_exists,
    format_task_issue_body,
    format_project_issue_body,
    find_parent_issue,
    _add_parent_issue_section,
    _add_task_info_section,
    _add_dependencies_section,
    _add_files_sections,
    _add_notes_and_execution_section,
)
from warifuri.core.types import Task, TaskInstruction, Project, TaskType, TaskStatus


class TestGetGithubRepo:
    """Test get_github_repo function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_get_github_repo_https_url(self, mock_run: Mock) -> None:
        """Test getting GitHub repo from HTTPS URL."""
        mock_result = Mock()
        mock_result.stdout = "https://github.com/user/repo.git\n"
        mock_run.return_value = mock_result

        repo = get_github_repo()
        assert repo == "user/repo"

    @patch("warifuri.core.github.subprocess.run")
    def test_get_github_repo_ssh_url(self, mock_run: Mock) -> None:
        """Test getting GitHub repo from SSH URL."""
        mock_result = Mock()
        mock_result.stdout = "git@github.com:user/repo.git\n"
        mock_run.return_value = mock_result

        repo = get_github_repo()
        assert repo == "user/repo"

    @patch("warifuri.core.github.subprocess.run")
    def test_get_github_repo_https_without_git(self, mock_run: Mock) -> None:
        """Test getting GitHub repo from HTTPS URL without .git."""
        mock_result = Mock()
        mock_result.stdout = "https://github.com/user/repo\n"
        mock_run.return_value = mock_result

        repo = get_github_repo()
        assert repo == "user/repo"

    @patch("warifuri.core.github.os.environ.get")
    @patch("warifuri.core.github.subprocess.run")
    def test_get_github_repo_non_github_url(self, mock_run: Mock, mock_env: Mock) -> None:
        """Test with non-GitHub URL."""
        mock_result = Mock()
        mock_result.stdout = "https://gitlab.com/user/repo.git\n"
        mock_run.return_value = mock_result
        mock_env.return_value = None  # No GITHUB_REPOSITORY environment variable

        repo = get_github_repo()
        assert repo is None

    @patch("warifuri.core.github.subprocess.run")
    def test_get_github_repo_command_error(self, mock_run: Mock) -> None:
        """Test when git command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        with patch.dict(os.environ, {"GITHUB_REPOSITORY": "env/repo"}):
            repo = get_github_repo()
            assert repo == "env/repo"

    @patch("warifuri.core.github.subprocess.run")
    def test_get_github_repo_no_env_fallback(self, mock_run: Mock) -> None:
        """Test when git fails and no environment variable."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        with patch.dict(os.environ, {}, clear=True):
            repo = get_github_repo()
            assert repo is None


class TestCheckGithubCli:
    """Test check_github_cli function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_check_github_cli_success(self, mock_run: Mock) -> None:
        """Test successful GitHub CLI check."""
        # Mock gh --version success
        mock_run.return_value = Mock()

        # Mock gh auth status with returncode 0 (authenticated)
        mock_auth_result = Mock()
        mock_auth_result.returncode = 0

        mock_run.side_effect = [Mock(), mock_auth_result]

        result = check_github_cli()
        assert result is True

    @patch("warifuri.core.github.subprocess.run")
    def test_check_github_cli_not_installed(self, mock_run: Mock) -> None:
        """Test when GitHub CLI is not installed."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        result = check_github_cli()
        assert result is False

    @patch("warifuri.core.github.subprocess.run")
    def test_check_github_cli_not_authenticated(self, mock_run: Mock) -> None:
        """Test when GitHub CLI is not authenticated."""
        # Mock gh --version success
        mock_version_result = Mock()

        # Mock gh auth status with returncode 1 (not authenticated)
        mock_auth_result = Mock()
        mock_auth_result.returncode = 1

        mock_run.side_effect = [mock_version_result, mock_auth_result]

        result = check_github_cli()
        assert result is False

    @patch("warifuri.core.github.subprocess.run")
    def test_check_github_cli_file_not_found(self, mock_run: Mock) -> None:
        """Test when gh command is not found."""
        mock_run.side_effect = FileNotFoundError("gh command not found")

        result = check_github_cli()
        assert result is False


class TestIsWorkingDirectoryClean:
    """Test is_working_directory_clean function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_working_directory_clean(self, mock_run: Mock) -> None:
        """Test when working directory is clean."""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        result = is_working_directory_clean()
        assert result is True

    @patch("warifuri.core.github.subprocess.run")
    def test_working_directory_dirty(self, mock_run: Mock) -> None:
        """Test when working directory has changes."""
        mock_result = Mock()
        mock_result.stdout = " M file.txt\n"
        mock_run.return_value = mock_result

        result = is_working_directory_clean()
        assert result is False

    @patch("warifuri.core.github.subprocess.run")
    def test_working_directory_git_error(self, mock_run: Mock) -> None:
        """Test when git command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = is_working_directory_clean()
        assert result is False


class TestCreateBranch:
    """Test create_branch function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_create_branch_success(self, mock_run: Mock) -> None:
        """Test successful branch creation."""
        # Mock branch list (empty) and checkout success
        mock_run.side_effect = [
            Mock(stdout="", returncode=0),  # git branch --list (empty)
            Mock(returncode=0)  # git checkout -b
        ]

        result = create_branch("feature-branch")
        assert result is True

        # Verify git commands were called
        assert mock_run.call_count == 2
        mock_run.assert_any_call(
            ["git", "branch", "--list", "feature-branch"],
            capture_output=True,
            text=True
        )
        mock_run.assert_any_call(
            ["git", "checkout", "-b", "feature-branch"],
            check=True
        )

    @patch("warifuri.core.github.subprocess.run")
    def test_create_branch_existing(self, mock_run: Mock) -> None:
        """Test switching to existing branch."""
        # Mock branch list (has output) and checkout success
        mock_run.side_effect = [
            Mock(stdout="  feature-branch\n", returncode=0),  # git branch --list (existing)
            Mock(returncode=0)  # git checkout
        ]

        result = create_branch("feature-branch")
        assert result is True

        # Verify git commands were called correctly
        assert mock_run.call_count == 2
        mock_run.assert_any_call(
            ["git", "branch", "--list", "feature-branch"],
            capture_output=True,
            text=True
        )
        mock_run.assert_any_call(
            ["git", "checkout", "feature-branch"],
            check=True
        )

    @patch("warifuri.core.github.subprocess.run")
    def test_create_branch_error(self, mock_run: Mock) -> None:
        """Test branch creation failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = create_branch("feature-branch")
        assert result is False


class TestCommitChanges:
    """Test commit_changes function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_commit_changes_success(self, mock_run: Mock) -> None:
        """Test successful commit."""
        # Mock successful git add, diff (has changes), and commit
        mock_run.side_effect = [
            Mock(returncode=0),  # git add .
            Mock(returncode=1),  # git diff --cached --exit-code (has changes)
            Mock(returncode=0, stdout="", stderr="")  # git commit
        ]

        result = commit_changes("Test commit message")
        assert result is True

        # Verify git commands were called
        assert mock_run.call_count == 3
        calls = mock_run.call_args_list

        # First call: git add .
        assert calls[0][0][0] == ["git", "add", "."]

        # Second call: git diff --cached --exit-code
        assert calls[1][0][0] == ["git", "diff", "--cached", "--exit-code"]

        # Third call: git commit
        assert calls[2][0][0] == ["git", "commit", "-m", "Test commit message"]

    @patch("warifuri.core.github.subprocess.run")
    def test_commit_changes_specific_files(self, mock_run: Mock) -> None:
        """Test commit with specific files."""
        # Mock successful git add, diff (has changes), and commit
        mock_run.side_effect = [
            Mock(returncode=0),  # git add file1.txt
            Mock(returncode=0),  # git add file2.txt
            Mock(returncode=1),  # git diff --cached --exit-code (has changes)
            Mock(returncode=0, stdout="", stderr="")  # git commit
        ]

        result = commit_changes("Test commit", ["file1.txt", "file2.txt"])
        assert result is True

        # Verify specific files were added
        calls = mock_run.call_args_list
        assert calls[0][0][0] == ["git", "add", "file1.txt"]
        assert calls[1][0][0] == ["git", "add", "file2.txt"]

    @patch("warifuri.core.github.subprocess.run")
    def test_commit_changes_no_changes(self, mock_run: Mock) -> None:
        """Test when there are no changes to commit."""
        # Mock git add and diff (no changes)
        mock_run.side_effect = [
            Mock(returncode=0),  # git add .
            Mock(returncode=0)   # git diff --cached --exit-code (no changes)
        ]

        result = commit_changes("Test commit message")
        assert result is True
        assert mock_run.call_count == 2  # Should not call commit

    @patch("warifuri.core.github.subprocess.run")
    def test_commit_changes_pre_commit_hook_modified_files(self, mock_run: Mock) -> None:
        """Test when pre-commit hooks modify files."""
        # Mock git operations including pre-commit hook scenario
        mock_run.side_effect = [
            Mock(returncode=0),  # git add .
            Mock(returncode=1),  # git diff --cached --exit-code (has changes)
            Mock(returncode=1, stdout="", stderr=""),  # git commit (fails, pre-commit modified)
            Mock(returncode=0),  # git add . (second time)
            Mock(returncode=1),  # git diff --cached --exit-code (still has changes)
            Mock(returncode=0)   # git commit (success)
        ]

        result = commit_changes("Test commit message")
        assert result is True
        assert mock_run.call_count == 6

    @patch("warifuri.core.github.subprocess.run")
    def test_commit_changes_pre_commit_hook_no_changes_after(self, mock_run: Mock) -> None:
        """Test when pre-commit hooks leave no changes."""
        # Mock git operations where pre-commit leaves no changes
        mock_run.side_effect = [
            Mock(returncode=0),  # git add .
            Mock(returncode=1),  # git diff --cached --exit-code (has changes)
            Mock(returncode=1, stdout="", stderr=""),  # git commit (fails, pre-commit modified)
            Mock(returncode=0),  # git add . (second time)
            Mock(returncode=0)   # git diff --cached --exit-code (no changes after hook)
        ]

        result = commit_changes("Test commit message")
        assert result is True
        assert mock_run.call_count == 5  # Should not call final commit

    @patch("warifuri.core.github.subprocess.run")
    def test_commit_changes_add_error(self, mock_run: Mock) -> None:
        """Test commit failure during git add."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = commit_changes("Test commit message")
        assert result is False

    @patch("warifuri.core.github.subprocess.run")
    def test_commit_changes_commit_error(self, mock_run: Mock) -> None:
        """Test commit failure during git commit."""
        # First call (git add) succeeds, second call (git diff) has changes, third call (git commit) fails
        mock_run.side_effect = [
            Mock(returncode=0),  # git add .
            Mock(returncode=1),  # git diff --cached --exit-code (has changes)
            subprocess.CalledProcessError(1, "git")  # git commit fails
        ]

        result = commit_changes("Test commit message")
        assert result is False


class TestPushBranch:
    """Test push_branch function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_push_branch_success(self, mock_run: Mock) -> None:
        """Test successful branch push."""
        mock_run.return_value = Mock()

        result = push_branch("feature-branch")
        assert result is True

        mock_run.assert_called_once_with(
            ["git", "push", "-u", "origin", "feature-branch"],
            check=True
        )

    @patch("warifuri.core.github.subprocess.run")
    def test_push_branch_error(self, mock_run: Mock) -> None:
        """Test branch push failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = push_branch("feature-branch")
        assert result is False


class TestCreatePullRequest:
    """Test create_pull_request function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_create_pull_request_success(self, mock_run: Mock) -> None:
        """Test successful pull request creation."""
        mock_result = Mock()
        mock_result.stdout = "https://github.com/user/repo/pull/123\n"
        mock_run.return_value = mock_result

        url = create_pull_request(
            title="Test PR",
            body="Test body",
            base_branch="main",
            draft=False,
            auto_merge=False
        )

        assert url == "https://github.com/user/repo/pull/123"

    @patch("warifuri.core.github.subprocess.run")
    def test_create_pull_request_draft(self, mock_run: Mock) -> None:
        """Test creating draft pull request."""
        mock_result = Mock()
        mock_result.stdout = "https://github.com/user/repo/pull/123\n"
        mock_run.return_value = mock_result

        create_pull_request(
            title="Test PR",
            body="Test body",
            draft=True
        )

        # Verify --draft flag was included
        args = mock_run.call_args[0][0]
        assert "--draft" in args

    @patch("warifuri.core.github.enable_auto_merge")
    @patch("warifuri.core.github.subprocess.run")
    def test_create_pull_request_with_auto_merge(self, mock_run: Mock, mock_auto_merge: Mock) -> None:
        """Test creating pull request with auto-merge enabled."""
        mock_result = Mock()
        mock_result.stdout = "https://github.com/user/repo/pull/123\n"
        mock_run.return_value = mock_result
        mock_auto_merge.return_value = True

        url = create_pull_request(
            title="Test PR",
            body="Test body",
            auto_merge=True,
            draft=False
        )

        assert url == "https://github.com/user/repo/pull/123"
        mock_auto_merge.assert_called_once_with("https://github.com/user/repo/pull/123")

    @patch("warifuri.core.github.subprocess.run")
    def test_create_pull_request_error(self, mock_run: Mock) -> None:
        """Test pull request creation failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        url = create_pull_request(title="Test PR", body="Test body")
        assert url is None


class TestEnableAutoMerge:
    """Test enable_auto_merge function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_enable_auto_merge_success(self, mock_run: Mock) -> None:
        """Test successful auto-merge enabling."""
        mock_run.return_value = Mock()

        result = enable_auto_merge("https://github.com/user/repo/pull/123", "squash")
        assert result is True

        mock_run.assert_called_once_with(
            ["gh", "pr", "merge", "https://github.com/user/repo/pull/123", "--auto", "--squash"],
            check=True
        )

    @patch("warifuri.core.github.subprocess.run")
    def test_enable_auto_merge_error(self, mock_run: Mock) -> None:
        """Test auto-merge enabling failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        result = enable_auto_merge("https://github.com/user/repo/pull/123", "squash")
        assert result is False


class TestMergePullRequest:
    """Test merge_pull_request function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_merge_pull_request_success(self, mock_run: Mock) -> None:
        """Test successful pull request merge."""
        mock_run.return_value = Mock()

        result = merge_pull_request("https://github.com/user/repo/pull/123", "squash")
        assert result is True

        mock_run.assert_called_once_with(
            ["gh", "pr", "merge", "https://github.com/user/repo/pull/123", "--squash", "--delete-branch"],
            check=True
        )

    @patch("warifuri.core.github.subprocess.run")
    def test_merge_pull_request_merge_method(self, mock_run: Mock) -> None:
        """Test pull request merge with different methods."""
        mock_run.return_value = Mock()

        # Test merge method
        merge_pull_request("https://github.com/user/repo/pull/123", "merge")
        args = mock_run.call_args[0][0]
        assert "--merge" in args

        # Test rebase method
        merge_pull_request("https://github.com/user/repo/pull/123", "rebase")
        args = mock_run.call_args[0][0]
        assert "--rebase" in args

    @patch("warifuri.core.github.subprocess.run")
    def test_merge_pull_request_error(self, mock_run: Mock) -> None:
        """Test pull request merge failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        result = merge_pull_request("https://github.com/user/repo/pull/123", "squash")
        assert result is False


class TestGetCurrentBranch:
    """Test get_current_branch function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_get_current_branch_success(self, mock_run: Mock) -> None:
        """Test successful current branch retrieval."""
        mock_result = Mock()
        mock_result.stdout = "feature-branch\n"
        mock_run.return_value = mock_result

        branch = get_current_branch()
        assert branch == "feature-branch"

        mock_run.assert_called_once_with(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True
        )

    @patch("warifuri.core.github.subprocess.run")
    def test_get_current_branch_error(self, mock_run: Mock) -> None:
        """Test current branch retrieval failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        branch = get_current_branch()
        assert branch is None


class TestEnsureLabelsExist:
    """Test ensure_labels_exist function."""

    @patch("warifuri.core.github._get_existing_labels")
    def test_ensure_labels_exist_empty_list(self, mock_get_labels: Mock) -> None:
        """Test with empty labels list."""
        result = ensure_labels_exist("user/repo", [])
        assert result == {}
        mock_get_labels.assert_not_called()

    @patch("warifuri.core.github._create_label")
    @patch("warifuri.core.github._get_existing_labels")
    def test_ensure_labels_exist_all_existing(self, mock_get_labels: Mock, mock_create: Mock) -> None:
        """Test when all labels already exist."""
        mock_get_labels.return_value = {"bug", "feature", "enhancement"}

        result = ensure_labels_exist("user/repo", ["bug", "feature"])

        assert result == {"bug": True, "feature": True}
        mock_get_labels.assert_called_once_with("user/repo")
        mock_create.assert_not_called()

    @patch("warifuri.core.github._create_label")
    @patch("warifuri.core.github._get_existing_labels")
    def test_ensure_labels_exist_some_missing(self, mock_get_labels: Mock, mock_create: Mock) -> None:
        """Test when some labels need to be created."""
        mock_get_labels.return_value = {"bug"}
        mock_create.side_effect = [True, False]  # First creation succeeds, second fails

        result = ensure_labels_exist("user/repo", ["bug", "feature", "new-label"])

        assert result == {"bug": True, "feature": True, "new-label": False}
        mock_get_labels.assert_called_once_with("user/repo")
        assert mock_create.call_count == 2
        mock_create.assert_any_call("user/repo", "feature")
        mock_create.assert_any_call("user/repo", "new-label")


class TestGetExistingLabels:
    """Test _get_existing_labels function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_get_existing_labels_success(self, mock_run: Mock) -> None:
        """Test successful label retrieval."""
        mock_result = Mock()
        mock_result.stdout = json.dumps([
            {"name": "bug"},
            {"name": "feature"},
            {"name": "enhancement"}
        ])
        mock_run.return_value = mock_result

        labels = _get_existing_labels("user/repo")
        assert labels == {"bug", "feature", "enhancement"}

        mock_run.assert_called_once_with(
            ["gh", "label", "list", "--repo", "user/repo", "--json", "name"],
            capture_output=True,
            text=True,
            check=True
        )

    @patch("warifuri.core.github.subprocess.run")
    def test_get_existing_labels_error(self, mock_run: Mock) -> None:
        """Test label retrieval failure."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        labels = _get_existing_labels("user/repo")
        assert labels == set()

    @patch("warifuri.core.github.subprocess.run")
    def test_get_existing_labels_json_error(self, mock_run: Mock) -> None:
        """Test invalid JSON response."""
        mock_result = Mock()
        mock_result.stdout = "invalid json"
        mock_run.return_value = mock_result

        labels = _get_existing_labels("user/repo")
        assert labels == set()


class TestCreateLabel:
    """Test _create_label function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_create_label_success(self, mock_run: Mock) -> None:
        """Test successful label creation."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = _create_label("user/repo", "new-label")
        assert result is True

        mock_run.assert_called_once_with(
            [
                "gh", "label", "create", "new-label",
                "--color", "0969da",
                "--description", "Auto-created by warifuri for new-label",
                "--repo", "user/repo"
            ],
            capture_output=True,
            text=True,
            check=False
        )

    @patch("warifuri.core.github.subprocess.run")
    def test_create_label_failure(self, mock_run: Mock) -> None:
        """Test label creation failure."""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr.strip.return_value = "Label already exists"
        mock_run.return_value = mock_result

        result = _create_label("user/repo", "existing-label")
        assert result is False

    @patch("warifuri.core.github.subprocess.run")
    def test_create_label_exception(self, mock_run: Mock) -> None:
        """Test label creation with exception."""
        mock_run.side_effect = Exception("Network error")

        result = _create_label("user/repo", "new-label")
        assert result is False


class TestCreateIssueSafe:
    """Test create_issue_safe function."""

    @patch("warifuri.core.github.ensure_labels_exist")
    @patch("warifuri.core.github.check_issue_exists")
    @patch("warifuri.core.github.subprocess.run")
    def test_create_issue_safe_success(self, mock_run: Mock, mock_check: Mock, mock_labels: Mock) -> None:
        """Test successful issue creation."""
        mock_check.return_value = False
        mock_labels.return_value = {"bug": True, "feature": True}
        mock_result = Mock()
        mock_result.stdout = "https://github.com/user/repo/issues/123\n"
        mock_run.return_value = mock_result

        success, url = create_issue_safe(
            title="Test Issue",
            body="Test body",
            labels=["bug", "feature"],
            assignee="testuser",
            repo="user/repo",
            dry_run=False
        )

        assert success is True
        assert url == "https://github.com/user/repo/issues/123"
        mock_check.assert_called_once_with("Test Issue", "user/repo")
        mock_labels.assert_called_once_with("user/repo", ["bug", "feature"])

    def test_create_issue_safe_dry_run(self) -> None:
        """Test dry run mode."""
        success, url = create_issue_safe(
            title="Test Issue",
            body="Test body",
            labels=["bug", "feature"],
            assignee="testuser",
            repo="user/repo",
            dry_run=True
        )

        assert success is True
        assert url is None

    @patch("warifuri.core.github.check_issue_exists")
    def test_create_issue_safe_duplicate(self, mock_check: Mock) -> None:
        """Test when issue already exists."""
        mock_check.return_value = True

        success, url = create_issue_safe(
            title="Existing Issue",
            body="Test body",
            repo="user/repo"
        )

        assert success is False
        assert url is None

    @patch("warifuri.core.github.ensure_labels_exist")
    @patch("warifuri.core.github.check_issue_exists")
    @patch("warifuri.core.github.subprocess.run")
    def test_create_issue_safe_partial_label_failure(self, mock_run: Mock, mock_check: Mock, mock_labels: Mock) -> None:
        """Test when some labels cannot be created."""
        mock_check.return_value = False
        mock_labels.return_value = {"bug": True, "missing": False}
        mock_result = Mock()
        mock_result.stdout = "https://github.com/user/repo/issues/123\n"
        mock_run.return_value = mock_result

        success, url = create_issue_safe(
            title="Test Issue",
            body="Test body",
            labels=["bug", "missing"],
            repo="user/repo"
        )

        assert success is True
        assert url == "https://github.com/user/repo/issues/123"
        # Should only use labels that exist
        args = mock_run.call_args[0][0]
        assert "--label" in args
        label_index = args.index("--label")
        assert args[label_index + 1] == "bug"

    @patch("warifuri.core.github.ensure_labels_exist")
    @patch("warifuri.core.github.check_issue_exists")
    @patch("warifuri.core.github.subprocess.run")
    def test_create_issue_safe_command_error(self, mock_run: Mock, mock_check: Mock, mock_labels: Mock) -> None:
        """Test when gh command fails."""
        mock_check.return_value = False
        mock_labels.return_value = {}
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        success, url = create_issue_safe(
            title="Test Issue",
            body="Test body",
            repo="user/repo"
        )

        assert success is False
        assert url is None


class TestCheckIssueExists:
    """Test check_issue_exists function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_check_issue_exists_found(self, mock_run: Mock) -> None:
        """Test when issue with exact title exists."""
        mock_result = Mock()
        mock_result.stdout = json.dumps([
            {"title": "Test Issue"},
            {"title": "Another Issue"}
        ])
        mock_run.return_value = mock_result

        exists = check_issue_exists("Test Issue", "user/repo")
        assert exists is True

    @patch("warifuri.core.github.subprocess.run")
    def test_check_issue_exists_not_found(self, mock_run: Mock) -> None:
        """Test when issue with title doesn't exist."""
        mock_result = Mock()
        mock_result.stdout = json.dumps([
            {"title": "Different Issue"},
            {"title": "Another Issue"}
        ])
        mock_run.return_value = mock_result

        exists = check_issue_exists("Test Issue", "user/repo")
        assert exists is False

    @patch("warifuri.core.github.subprocess.run")
    def test_check_issue_exists_empty_result(self, mock_run: Mock) -> None:
        """Test when no issues found."""
        mock_result = Mock()
        mock_result.stdout = json.dumps([])
        mock_run.return_value = mock_result

        exists = check_issue_exists("Test Issue", "user/repo")
        assert exists is False

    @patch("warifuri.core.github.subprocess.run")
    def test_check_issue_exists_command_error(self, mock_run: Mock) -> None:
        """Test when gh command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        exists = check_issue_exists("Test Issue", "user/repo")
        assert exists is False

    @patch("warifuri.core.github.subprocess.run")
    def test_check_issue_exists_json_error(self, mock_run: Mock) -> None:
        """Test when JSON parsing fails."""
        mock_result = Mock()
        mock_result.stdout = "invalid json"
        mock_run.return_value = mock_result

        exists = check_issue_exists("Test Issue", "user/repo")
        assert exists is False


class TestFormatTaskIssueBody:
    """Test format_task_issue_body function."""

    def create_mock_task(self,
                        name: str = "test-task",
                        project: str = "test-project",
                        description: str = "Test description",
                        task_type: TaskType = TaskType.MACHINE,
                        dependencies: list = None,
                        inputs: list = None,
                        outputs: list = None,
                        note: str = "") -> Task:
        """Create a mock task for testing."""
        instruction = TaskInstruction(
            name=name,
            description=description,
            dependencies=dependencies or [],
            inputs=inputs or [],
            outputs=outputs or [],
            note=note
        )

        task = Task(
            project=project,
            name=name,
            path=Path(f"/test/path/{project}/{name}"),
            instruction=instruction,
            task_type=task_type,
            status=TaskStatus.READY
        )

        return task

    def test_format_task_issue_body_basic(self) -> None:
        """Test basic task issue body formatting."""
        task = self.create_mock_task(
            name="test-task",
            project="test-project",
            description="A test task description"
        )

        body = format_task_issue_body(task)

        assert "# Task: test-project/test-task" in body
        assert "## Description" in body
        assert "A test task description" in body
        assert "**Type**: machine" in body
        assert "**Status**: ready" in body
        assert "**Completed**: No" in body
        assert "warifuri run --task test-project/test-task" in body

    @patch("warifuri.core.github.find_parent_issue")
    def test_format_task_issue_body_with_parent_url(self, mock_find_parent: Mock) -> None:
        """Test task issue body with explicit parent URL."""
        task = self.create_mock_task()
        parent_url = "https://github.com/user/repo/issues/123"

        body = format_task_issue_body(task, repo="user/repo", parent_issue_url=parent_url)

        assert f"**Parent Project**: {parent_url}" in body
        mock_find_parent.assert_not_called()

    @patch("warifuri.core.github.find_parent_issue")
    def test_format_task_issue_body_with_auto_parent(self, mock_find_parent: Mock) -> None:
        """Test task issue body with auto-discovered parent."""
        task = self.create_mock_task(project="test-project")
        mock_find_parent.return_value = "https://github.com/user/repo/issues/456"

        body = format_task_issue_body(task, repo="user/repo")

        assert "**Parent Project**: https://github.com/user/repo/issues/456" in body
        mock_find_parent.assert_called_once_with("test-project", "user/repo")

    def test_format_task_issue_body_with_dependencies(self) -> None:
        """Test task issue body with dependencies."""
        task = self.create_mock_task(
            dependencies=["dep1", "dep2", "dep3"]
        )

        body = format_task_issue_body(task)

        assert "## Dependencies" in body
        assert "- [ ] dep1" in body
        assert "- [ ] dep2" in body
        assert "- [ ] dep3" in body

    def test_format_task_issue_body_with_files(self) -> None:
        """Test task issue body with input and output files."""
        task = self.create_mock_task(
            inputs=["input1.txt", "input2.json"],
            outputs=["output1.txt", "result.json"]
        )

        body = format_task_issue_body(task)

        assert "## Input Files" in body
        assert "- `input1.txt`" in body
        assert "- `input2.json`" in body
        assert "## Expected Outputs" in body
        assert "- `output1.txt`" in body
        assert "- `result.json`" in body

    def test_format_task_issue_body_with_note(self) -> None:
        """Test task issue body with note."""
        task = self.create_mock_task(
            note="This is an important note about the task."
        )

        body = format_task_issue_body(task)

        assert "## Notes" in body
        assert "This is an important note about the task." in body

    def test_format_task_issue_body_no_project_attribute(self) -> None:
        """Test task issue body when task has no project attribute."""
        task = self.create_mock_task(name="standalone-task")
        # Remove the project attribute to simulate a task without it
        delattr(task, 'project')

        body = format_task_issue_body(task)

        assert "# Task: standalone-task" in body
        assert "warifuri run --task standalone-task" in body


class TestFormatProjectIssueBody:
    """Test format_project_issue_body function."""

    def create_mock_project(self, name: str = "test-project", tasks: list = None) -> Project:
        """Create a mock project for testing."""
        if tasks is None:
            tasks = []

        # Create a simple mock project
        project = MagicMock()
        project.name = name
        project.tasks = tasks
        return project

    def create_mock_task(self, name: str, status: TaskStatus, description: str = "") -> Task:
        """Create a mock task with specified status."""
        task = MagicMock()
        task.name = name
        task.status = status
        task.instruction.description = description or "No description"
        return task

    def test_format_project_issue_body_basic(self) -> None:
        """Test basic project issue body formatting."""
        tasks = [
            self.create_mock_task("task1", TaskStatus.COMPLETED, "First task"),
            self.create_mock_task("task2", TaskStatus.READY, "Second task"),
            self.create_mock_task("task3", TaskStatus.PENDING, "Third task")
        ]

        project = self.create_mock_project("test-project", tasks)

        body = format_project_issue_body(project)

        assert "# Project: test-project" in body
        assert "## Overview" in body
        assert "overall progress of the 'test-project' project" in body
        assert "## Tasks" in body
        assert "✅ task1: First task" in body
        assert "🔄 task2: Second task" in body
        assert "⏸️ task3: Third task" in body
        assert "warifuri run --task test-project" in body

    def test_format_project_issue_body_no_tasks(self) -> None:
        """Test project issue body with no tasks."""
        project = self.create_mock_project("empty-project", [])

        body = format_project_issue_body(project)

        assert "# Project: empty-project" in body
        assert "## Tasks" in body
        assert "warifuri run --task empty-project" in body

    def test_format_project_issue_body_task_no_description(self) -> None:
        """Test project issue body with task that has no description."""
        task = self.create_mock_task("no-desc-task", TaskStatus.READY)
        task.instruction.description = None

        project = self.create_mock_project("test-project", [task])

        body = format_project_issue_body(project)

        assert "🔄 no-desc-task: No description" in body


class TestFindParentIssue:
    """Test find_parent_issue function."""

    @patch("warifuri.core.github.subprocess.run")
    def test_find_parent_issue_found(self, mock_run: Mock) -> None:
        """Test when parent issue is found."""
        mock_result = Mock()
        mock_result.stdout = json.dumps([
            {
                "title": "[PROJECT] test-project",
                "url": "https://github.com/user/repo/issues/123"
            }
        ])
        mock_run.return_value = mock_result

        url = find_parent_issue("test-project", "user/repo")
        assert url == "https://github.com/user/repo/issues/123"

        mock_run.assert_called_once_with(
            [
                "gh", "issue", "list", "--repo", "user/repo",
                "--search", '"[PROJECT] test-project" in:title',
                "--json", "title,url"
            ],
            capture_output=True,
            text=True,
            check=True
        )

    @patch("warifuri.core.github.subprocess.run")
    def test_find_parent_issue_not_found(self, mock_run: Mock) -> None:
        """Test when parent issue is not found."""
        mock_result = Mock()
        mock_result.stdout = json.dumps([
            {
                "title": "[PROJECT] different-project",
                "url": "https://github.com/user/repo/issues/456"
            }
        ])
        mock_run.return_value = mock_result

        url = find_parent_issue("test-project", "user/repo")
        assert url is None

    @patch("warifuri.core.github.subprocess.run")
    def test_find_parent_issue_empty_result(self, mock_run: Mock) -> None:
        """Test when no issues found."""
        mock_result = Mock()
        mock_result.stdout = json.dumps([])
        mock_run.return_value = mock_result

        url = find_parent_issue("test-project", "user/repo")
        assert url is None

    @patch("warifuri.core.github.subprocess.run")
    def test_find_parent_issue_command_error(self, mock_run: Mock) -> None:
        """Test when gh command fails."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "gh")

        url = find_parent_issue("test-project", "user/repo")
        assert url is None

    @patch("warifuri.core.github.subprocess.run")
    def test_find_parent_issue_json_error(self, mock_run: Mock) -> None:
        """Test when JSON parsing fails."""
        mock_result = Mock()
        mock_result.stdout = "invalid json"
        mock_run.return_value = mock_result

        url = find_parent_issue("test-project", "user/repo")
        assert url is None


class TestPrivateHelperFunctions:
    """Test private helper functions for issue body formatting."""

    def create_mock_task(self, **kwargs) -> Task:
        """Create a mock task for testing."""
        defaults = {
            "name": "test-task",
            "project": "test-project",
            "description": "Test description",
            "task_type": TaskType.MACHINE,
            "dependencies": [],
            "inputs": [],
            "outputs": [],
            "note": ""
        }
        defaults.update(kwargs)

        instruction = TaskInstruction(
            name=defaults["name"],
            description=defaults["description"],
            dependencies=defaults["dependencies"],
            inputs=defaults["inputs"],
            outputs=defaults["outputs"],
            note=defaults["note"]
        )

        task = Task(
            project=defaults["project"],
            name=defaults["name"],
            path=Path(f"/test/path/{defaults['project']}/{defaults['name']}"),
            instruction=instruction,
            task_type=defaults["task_type"],
            status=TaskStatus.READY
        )

        return task

    @patch("warifuri.core.github.find_parent_issue")
    def test_add_parent_issue_section_with_explicit_url(self, mock_find_parent: Mock) -> None:
        """Test _add_parent_issue_section with explicit parent URL."""
        body_lines = []
        task = self.create_mock_task()
        parent_url = "https://github.com/user/repo/issues/123"

        _add_parent_issue_section(body_lines, task, "user/repo", parent_url)

        assert f"**Parent Project**: {parent_url}" in body_lines
        assert "" in body_lines
        mock_find_parent.assert_not_called()

    @patch("warifuri.core.github.find_parent_issue")
    def test_add_parent_issue_section_with_auto_discovery(self, mock_find_parent: Mock) -> None:
        """Test _add_parent_issue_section with auto-discovery."""
        body_lines = []
        task = self.create_mock_task(project="test-project")
        mock_find_parent.return_value = "https://github.com/user/repo/issues/456"

        _add_parent_issue_section(body_lines, task, "user/repo", "")

        assert "**Parent Project**: https://github.com/user/repo/issues/456" in body_lines
        mock_find_parent.assert_called_once_with("test-project", "user/repo")

    def test_add_task_info_section(self) -> None:
        """Test _add_task_info_section."""
        body_lines = []
        task = self.create_mock_task(
            description="A detailed task description",
            task_type=TaskType.AI
        )
        # Mock the is_completed property
        with patch.object(type(task), 'is_completed', new_callable=lambda: property(lambda self: True)):
            _add_task_info_section(body_lines, task)

        assert "## Description" in body_lines
        assert "A detailed task description" in body_lines
        assert "**Type**: ai" in body_lines
        assert "**Status**: ready" in body_lines
        assert "**Completed**: Yes" in body_lines

    def test_add_dependencies_section(self) -> None:
        """Test _add_dependencies_section."""
        body_lines = []
        task = self.create_mock_task(dependencies=["dep1", "dep2"])

        _add_dependencies_section(body_lines, task)

        assert "## Dependencies" in body_lines
        assert "- [ ] dep1" in body_lines
        assert "- [ ] dep2" in body_lines

    def test_add_dependencies_section_no_dependencies(self) -> None:
        """Test _add_dependencies_section with no dependencies."""
        body_lines = []
        task = self.create_mock_task(dependencies=[])

        _add_dependencies_section(body_lines, task)

        assert "## Dependencies" not in body_lines

    def test_add_files_sections(self) -> None:
        """Test _add_files_sections."""
        body_lines = []
        task = self.create_mock_task(
            inputs=["input1.txt", "input2.json"],
            outputs=["output.txt"]
        )

        _add_files_sections(body_lines, task)

        assert "## Input Files" in body_lines
        assert "- `input1.txt`" in body_lines
        assert "- `input2.json`" in body_lines
        assert "## Expected Outputs" in body_lines
        assert "- `output.txt`" in body_lines

    def test_add_files_sections_no_files(self) -> None:
        """Test _add_files_sections with no files."""
        body_lines = []
        task = self.create_mock_task(inputs=[], outputs=[])

        _add_files_sections(body_lines, task)

        assert "## Input Files" not in body_lines
        assert "## Expected Outputs" not in body_lines

    def test_add_notes_and_execution_section(self) -> None:
        """Test _add_notes_and_execution_section."""
        body_lines = []
        task = self.create_mock_task(note="Important note about the task")
        full_name = "test-project/test-task"

        _add_notes_and_execution_section(body_lines, task, full_name)

        assert "## Notes" in body_lines
        assert "Important note about the task" in body_lines
        assert "## Execution" in body_lines
        assert "Run with: `warifuri run --task test-project/test-task`" in body_lines
        assert "Created by warifuri CLI" in body_lines

    def test_add_notes_and_execution_section_no_note(self) -> None:
        """Test _add_notes_and_execution_section with no note."""
        body_lines = []
        task = self.create_mock_task(note="")
        full_name = "test-project/test-task"

        _add_notes_and_execution_section(body_lines, task, full_name)

        assert "## Notes" not in body_lines
        assert "## Execution" in body_lines
        assert "Run with: `warifuri run --task test-project/test-task`" in body_lines
