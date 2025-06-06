"""Template command for managing templates."""

import click

from ..context import Context, pass_context


@click.group()
@pass_context
def template(ctx: Context) -> None:
    """Manage templates."""
    pass


@template.command("list")
@click.option(
    "--format",
    type=click.Choice(["plain", "json"]),
    default="plain",
    help="Output format",
)
@pass_context
def list_templates(
    ctx: Context,
    format: str,
) -> None:
    """List available templates."""
    workspace_path = ctx.ensure_workspace_path()

    templates_dir = workspace_path / "templates"

    if not templates_dir.exists():
        click.echo("No templates directory found.")
        return

    try:
        templates = [
            d.name for d in templates_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]
    except (OSError, FileNotFoundError) as e:
        ctx.logger.warning("Could not read templates directory: %s", e)
        templates = []

    if not templates:
        click.echo("No templates found.")
        return

    if format == "json":
        import json

        click.echo(json.dumps(templates, indent=2))
    else:
        click.echo("Available templates:")
        for template in templates:
            click.echo(f"  - {template}")
            # TODO: List tasks within template
