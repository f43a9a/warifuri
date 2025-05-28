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
        """Ensure workspace path is available, raising ClickException if not."""
        if self.workspace_path is None:
            raise click.ClickException("Workspace path is not set. Please run from a valid workspace.")
        return self.workspace_path


pass_context = click.make_pass_decorator(Context, ensure=True)
