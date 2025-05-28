"""Tests for GitHub integration."""

import os
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

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
)


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
    def test_commit_changes_add_error(self, mock_run: Mock) -> None:
        """Test commit failure during git add."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "git")

        result = commit_changes("Test commit message")
        assert result is False

    @patch("warifuri.core.github.subprocess.run")
    def test_commit_changes_commit_error(self, mock_run: Mock) -> None:
        """Test commit failure during git commit."""
        # First call (git add) succeeds, second call (git commit) fails
        mock_run.side_effect = [Mock(), subprocess.CalledProcessError(1, "git")]

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
