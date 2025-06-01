"""CLI context for passing shared data."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import click


class Context:
    """CLI context for passing shared data."""

    def __init__(
        self, workspace_path: Optional[Path] = None, logger: Optional[logging.Logger] = None
    ) -> None:
        self.workspace_path = workspace_path
        self.logger = logger or logging.getLogger(__name__)
        self.timestamp = datetime.now().isoformat()

    def ensure_workspace_path(self) -> Path:
        """Ensure workspace path is set and return it.

        Returns:
            Path: The workspace path

        Raises:
            click.ClickException: If workspace path is not set or invalid
        """
        if self.workspace_path is None:
            # Try to discover workspace from current directory
            current_dir = Path.cwd()

            # Look for workspace indicators: projects/ or workspace/ directory
            for path in [current_dir] + list(current_dir.parents):
                if (path / "projects").exists() or (path / "workspace").exists():
                    self.workspace_path = path
                    break

            if self.workspace_path is None:
                raise click.ClickException(
                    "Could not find workspace directory\n"
                    "Please run from a directory containing 'workspace/' or 'projects/'"
                )

        if not self.workspace_path.exists():
            raise click.ClickException(f"Workspace path does not exist: {self.workspace_path}")

        return self.workspace_path


pass_context = click.make_pass_decorator(Context, ensure=True)
