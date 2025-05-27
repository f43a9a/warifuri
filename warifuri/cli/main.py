"""Main CLI entry point."""

import logging
from pathlib import Path
from typing import Optional

import click

from ..utils import find_workspace_root, setup_logging
from .commands.init import init
from .commands.list import list_cmd
from .commands.run import run
from .commands.show import show
from .commands.validate import validate
from .commands.graph import graph
from .commands.mark_done import mark_done
from .commands.template import template
from .commands.issue import issue


# Global context for CLI
class Context:
    def __init__(self) -> None:
        self.workspace_path: Optional[Path] = None
        self.logger: Optional[logging.Logger] = None


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Set logging level",
)
@click.option(
    "--workspace",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Workspace directory path",
)
@pass_context
def cli(ctx: Context, log_level: Optional[str], workspace: Optional[Path]) -> None:
    """warifuri - A minimal CLI for task allocation."""
    # Setup logging
    ctx.logger = setup_logging(log_level)

    # Find workspace
    ctx.workspace_path = workspace or find_workspace_root()
    if not ctx.workspace_path:
        click.echo("Error: Could not find workspace directory", err=True)
        click.echo("Please run from a directory containing 'workspace/' or 'projects/'", err=True)
        raise click.Abort()

    ctx.logger.debug(f"Using workspace: {ctx.workspace_path}")


# Import and register commands
cli.add_command(init)  # type: ignore[has-type]
cli.add_command(list_cmd, name="list")  # type: ignore[has-type]
cli.add_command(run)  # type: ignore[has-type]
cli.add_command(show)  # type: ignore[has-type]
cli.add_command(validate)  # type: ignore[has-type]
cli.add_command(graph)  # type: ignore[has-type]
cli.add_command(mark_done, name="mark-done")  # type: ignore[has-type]
cli.add_command(template)  # type: ignore[has-type]
cli.add_command(issue)  # type: ignore[has-type]


if __name__ == "__main__":
    cli()
