"""Main CLI entry point."""

from pathlib import Path
from typing import Optional

import click

from .context import Context, pass_context
from ..utils import find_workspace_root, setup_logging


# Import commands after defining Context to avoid circular imports
from .commands.init import init  # noqa: E402
from .commands.list import list_cmd  # noqa: E402
from .commands.run import run  # noqa: E402
from .commands.show import show  # noqa: E402
from .commands.validate import validate  # noqa: E402
from .commands.graph import graph  # noqa: E402
from .commands.mark_done import mark_done  # noqa: E402
from .commands.template import template  # noqa: E402
from .commands.issue import issue  # noqa: E402
from .commands.automation import automation  # noqa: E402


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
cli.add_command(init)
cli.add_command(list_cmd, name="list")
cli.add_command(run)
cli.add_command(show)
cli.add_command(validate)
cli.add_command(graph)
cli.add_command(mark_done, name="mark-done")
cli.add_command(template)
cli.add_command(issue)
cli.add_command(automation)


if __name__ == "__main__":
    cli()
