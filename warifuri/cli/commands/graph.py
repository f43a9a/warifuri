"""Graph command for visualizing task dependencies."""

import click

from ..main import Context, pass_context
from ...core.discovery import discover_all_projects


@click.command()
@click.option("--project", help="Filter by project name")
@click.option(
    "--format",
    type=click.Choice(["mermaid", "ascii", "html"]),
    default="ascii",
    help="Output format",
)
@click.option("--web", is_flag=True, help="Open in web browser (HTML format only)")
@pass_context
def graph(
    ctx: Context,
    project: str,
    format: str,
    web: bool,
) -> None:
    """Generate dependency graph visualization."""
    workspace_path = ctx.workspace_path
    assert workspace_path is not None
    
    # Discover projects
    projects = discover_all_projects(workspace_path)
    
    if project:
        projects = [p for p in projects if p.name == project]
    
    # Collect tasks
    all_tasks = []
    for proj in projects:
        all_tasks.extend(proj.tasks)
    
    if not all_tasks:
        click.echo("No tasks found.")
        return
    
    if format == "mermaid":
        _generate_mermaid(all_tasks)
    elif format == "html":
        _generate_html(all_tasks, web)
    else:
        _generate_ascii(all_tasks)


def _generate_ascii(tasks) -> None:
    """Generate ASCII dependency graph."""
    click.echo("Dependency Graph (ASCII):")
    click.echo()
    
    for task in tasks:
        status_symbol = "✅" if task.is_completed else ("🔄" if task.status.value == "ready" else "⏸️")
        click.echo(f"{status_symbol} {task.full_name}")
        
        for dep in task.instruction.dependencies:
            click.echo(f"  └── depends on: {dep}")
        
        if not task.instruction.dependencies:
            click.echo("  └── no dependencies")
        
        click.echo()


def _generate_mermaid(tasks) -> None:
    """Generate Mermaid diagram."""
    click.echo("```mermaid")
    click.echo("graph TD")
    
    # Define nodes
    for task in tasks:
        node_id = task.full_name.replace("/", "_").replace("-", "_")
        status = "✅" if task.is_completed else ("🔄" if task.status.value == "ready" else "⏸️")
        click.echo(f"    {node_id}[\"{status} {task.full_name}\"]")
    
    # Define edges
    for task in tasks:
        node_id = task.full_name.replace("/", "_").replace("-", "_")
        for dep in task.instruction.dependencies:
            dep_id = dep.replace("/", "_").replace("-", "_")
            click.echo(f"    {dep_id} --> {node_id}")
    
    click.echo("```")


def _generate_html(tasks, open_browser: bool) -> None:
    """Generate HTML visualization."""
    # TODO: Implement HTML generation with interactive graph
    click.echo("HTML graph generation will be implemented in future version.")
    if open_browser:
        click.echo("Browser opening will be implemented with HTML generation.")
