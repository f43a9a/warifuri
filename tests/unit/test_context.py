"""Test CLI context functionality."""

import logging
from pathlib import Path
from unittest.mock import patch

import click
import pytest

from warifuri.cli.context import Context


class TestContext:
    """Test Context class."""

    def test_context_initialization_with_params(self):
        """Test context initialization with provided parameters."""
        workspace_path = Path("/tmp/test")
        logger = logging.getLogger("test")

        ctx = Context(workspace_path=workspace_path, logger=logger)

        assert ctx.workspace_path == workspace_path
        assert ctx.logger == logger
        assert isinstance(ctx.timestamp, str)

    def test_context_initialization_defaults(self):
        """Test context initialization with default values."""
        ctx = Context()

        assert ctx.workspace_path is None
        assert isinstance(ctx.logger, logging.Logger)
        assert isinstance(ctx.timestamp, str)

    def test_ensure_workspace_path_when_set(self, temp_workspace):
        """Test ensure_workspace_path when workspace is already set."""
        ctx = Context(workspace_path=temp_workspace)

        result = ctx.ensure_workspace_path()

        assert result == temp_workspace

    def test_ensure_workspace_path_discovery_projects_dir(self, tmp_path):
        """Test workspace discovery from projects directory."""
        # Create a workspace with projects directory
        workspace_dir = tmp_path / "workspace"
        projects_dir = workspace_dir / "projects"
        sub_dir = workspace_dir / "subdir"

        workspace_dir.mkdir()
        projects_dir.mkdir()
        sub_dir.mkdir()

        with patch("pathlib.Path.cwd", return_value=sub_dir):
            ctx = Context()
            result = ctx.ensure_workspace_path()

            assert result == workspace_dir

    def test_ensure_workspace_path_discovery_workspace_dir(self, tmp_path):
        """Test workspace discovery from workspace directory."""
        # Create a workspace with workspace directory (not projects)
        workspace_dir = tmp_path / "workspace"
        inner_workspace_dir = workspace_dir / "workspace"
        sub_dir = workspace_dir / "subdir"

        workspace_dir.mkdir()
        inner_workspace_dir.mkdir()
        sub_dir.mkdir()

        with patch("pathlib.Path.cwd", return_value=sub_dir):
            ctx = Context()
            result = ctx.ensure_workspace_path()

            assert result == workspace_dir

    def test_ensure_workspace_path_not_found(self):
        """Test workspace discovery failure."""
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/tmp/no_workspace")

            with patch.object(Path, "exists", return_value=False):
                ctx = Context()

                with pytest.raises(click.ClickException) as exc_info:
                    ctx.ensure_workspace_path()

                assert "Could not find workspace directory" in str(exc_info.value)

    def test_ensure_workspace_path_not_exists(self):
        """Test ensure_workspace_path when workspace path doesn't exist."""
        non_existent_path = Path("/tmp/non_existent")
        ctx = Context(workspace_path=non_existent_path)

        with pytest.raises(click.ClickException) as exc_info:
            ctx.ensure_workspace_path()

        assert "Workspace path does not exist" in str(exc_info.value)
        assert str(non_existent_path) in str(exc_info.value)
