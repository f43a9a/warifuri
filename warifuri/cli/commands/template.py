"""Template command for managing templates."""

import click

from ..main import Context, pass_context


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
    workspace_path = ctx.workspace_path
    assert workspace_path is not None

    templates_dir = workspace_path / "templates"

    if not templates_dir.exists():
        click.echo("No templates directory found.")
        return

    try:
        templates = [
            d.name for d in templates_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
        ]
    except Exception:
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
