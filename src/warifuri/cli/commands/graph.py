"""Graph command for visualizing task dependencies."""

import os
import subprocess
import tempfile
from typing import List

import click

from ..context import Context, pass_context
from ...core.types import Task


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
    workspace_path = ctx.ensure_workspace_path()

    # Use safe discovery that doesn't raise exceptions on circular dependencies
    from ...core.discovery import discover_all_projects_safe

    projects = discover_all_projects_safe(workspace_path)

    if project:
        projects = [p for p in projects if p.name == project]

    # Collect tasks
    all_tasks = []
    for proj in projects:
        all_tasks.extend(proj.tasks)

    # Check for and warn about circular dependencies
    if all_tasks:
        from ...utils.validation import detect_circular_dependencies

        cycle = detect_circular_dependencies(all_tasks)
        if cycle:
            click.echo(f"⚠️  Warning: Circular dependency detected: {' -> '.join(cycle)}")
            click.echo("Displaying graph anyway for visualization purposes...")
            click.echo()

    if not all_tasks:
        click.echo("No tasks found.")
        return

    if format == "mermaid":
        _generate_mermaid(all_tasks)
    elif format == "html":
        _generate_html(all_tasks, web)
    else:
        _generate_ascii(all_tasks)


def _generate_ascii(tasks: List[Task]) -> None:
    """Generate ASCII dependency graph."""
    click.echo("Dependency Graph (ASCII):")
    click.echo()

    for task in tasks:
        status_symbol = (
            "✅" if task.is_completed else ("🔄" if task.status.value == "ready" else "⏸️")
        )
        click.echo(f"{status_symbol} {task.full_name}")

        for dep in task.instruction.dependencies:
            click.echo(f"  └── depends on: {dep}")

        if not task.instruction.dependencies:
            click.echo("  └── no dependencies")

        click.echo()


def _generate_mermaid(tasks: List[Task]) -> None:
    """Generate Mermaid diagram."""
    click.echo("```mermaid")
    click.echo("graph TD")

    # Define nodes
    for task in tasks:
        node_id = task.full_name.replace("/", "_").replace("-", "_")
        status = "✅" if task.is_completed else ("🔄" if task.status.value == "ready" else "⏸️")
        click.echo(f'    {node_id}["{status} {task.full_name}"]')

    # Define edges
    for task in tasks:
        node_id = task.full_name.replace("/", "_").replace("-", "_")
        for dep in task.instruction.dependencies:
            dep_id = dep.replace("/", "_").replace("-", "_")
            click.echo(f"    {dep_id} --> {node_id}")

    click.echo("```")


def _generate_html(tasks: List[Task], open_browser: bool) -> None:
    """Generate HTML visualization with interactive graph."""
    html_content = _create_html_graph(tasks)

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html_content)
        html_file = f.name

    click.echo(f"HTML graph generated: {html_file}")

    if open_browser:
        _open_in_browser(html_file)
    else:
        click.echo(f"To view the graph, open: {html_file}")


def _create_html_graph(tasks: List[Task]) -> str:
    """Create HTML content with interactive graph using vis.js."""
    nodes, edges = _build_graph_data(tasks)
    html_content = _generate_html_template(nodes, edges)
    return html_content


def _build_graph_data(tasks: List[Task]) -> tuple[list, list]:
    """Build nodes and edges data for vis.js graph."""
    nodes = []
    edges = []

    for task in tasks:
        node = _create_task_node(task)
        nodes.append(node)

        # Add edges for dependencies
        for dep in task.instruction.dependencies:
            edges.append({"from": dep, "to": task.full_name, "arrows": "to"})

    return nodes, edges


def _create_task_node(task: Task) -> dict:
    """Create a single task node with appropriate styling."""
    # Node styling based on status
    if task.is_completed:
        color = "#28a745"  # Green
        shape = "box"
    elif task.status.value == "ready":
        color = "#007bff"  # Blue
        shape = "ellipse"
    else:
        color = "#6c757d"  # Gray
        shape = "ellipse"

    return {
        "id": task.full_name,
        "label": task.full_name,
        "title": f"Type: {task.task_type.value}\\nStatus: {task.status.value}\\nDescription: {task.instruction.description}",
        "color": color,
        "shape": shape,
    }


def _generate_html_template(nodes: list, edges: list) -> str:
    """Generate complete HTML template with embedded graph data."""
    nodes_json = str(nodes).replace("'", '"').replace("True", "true").replace("False", "false")
    edges_json = str(edges).replace("'", '"').replace("True", "true").replace("False", "false")

    css_styles = _get_css_styles()
    js_code = _get_javascript_code(nodes_json, edges_json)

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Warifuri Task Dependencies</title>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    {css_styles}
</head>
<body>
    <div class="header">
        <h1>Warifuri Task Dependencies</h1>
        <p>Interactive dependency graph visualization</p>
    </div>

    <div id="mynetworkid"></div>

    <div class="legend">
        <h3>Legend:</h3>
        <div class="legend-item">
            <span class="legend-color" style="background-color: #28a745;"></span>
            Completed Tasks
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: #007bff;"></span>
            Ready Tasks
        </div>
        <div class="legend-item">
            <span class="legend-color" style="background-color: #6c757d;"></span>
            Blocked Tasks
        </div>
    </div>

    {js_code}
</body>
</html>"""


def _get_css_styles() -> str:
    """Return CSS styling for the graph visualization."""
    return """<style type="text/css">
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        #mynetworkid {
            width: 100%;
            height: 600px;
            border: 1px solid lightgray;
            background-color: white;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .legend {
            margin-top: 20px;
            background: white;
            padding: 15px;
            border-radius: 5px;
            border: 1px solid #ddd;
        }
        .legend-item {
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 10px;
        }
        .legend-color {
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 8px;
            vertical-align: middle;
        }
    </style>"""


def _get_javascript_code(nodes_json: str, edges_json: str) -> str:
    """Return JavaScript code for graph interactivity."""
    return f"""<script type="text/javascript">
        // Create a data object with nodes and edges
        var nodes = new vis.DataSet({nodes_json});
        var edges = new vis.DataSet({edges_json});

        // Create a network
        var container = document.getElementById("mynetworkid");
        var data = {{
            nodes: nodes,
            edges: edges
        }};

        var options = {{
            layout: {{
                hierarchical: {{
                    direction: "UD",
                    sortMethod: "directed"
                }}
            }},
            physics: {{
                enabled: false
            }},
            nodes: {{
                font: {{
                    size: 14,
                    color: "white"
                }},
                margin: 10
            }},
            edges: {{
                color: "gray",
                width: 2,
                smooth: {{
                    type: "cubicBezier",
                    forceDirection: "vertical",
                    roundness: 0.4
                }}
            }},
            interaction: {{
                dragNodes: true,
                dragView: true,
                zoomView: true
            }}
        }};

        var network = new vis.Network(container, data, options);

        // Add click event to show task details
        network.on("click", function (params) {{
            if (params.nodes.length > 0) {{
                var nodeId = params.nodes[0];
                var nodeData = nodes.get(nodeId);
                alert("Task: " + nodeId + "\\n\\n" + nodeData.title);
            }}
        }});
    </script>"""


def _open_in_browser(file_path: str) -> None:
    """Open HTML file in default browser."""
    browser_opened = False

    try:
        # Try different methods to open browser
        if os.name == "nt":  # Windows
            import platform

            if platform.system() == "Windows":
                # Use os.startfile only on Windows
                os.startfile(file_path)  # type: ignore[attr-defined]
                browser_opened = True
        elif os.name == "posix":  # macOS and Linux
            # Try macOS open command
            if subprocess.run(["which", "open"], capture_output=True, check=False).returncode == 0:
                subprocess.run(["open", file_path], check=False)
                browser_opened = True
            # Try Linux xdg-open
            elif (
                subprocess.run(["which", "xdg-open"], capture_output=True, check=False).returncode
                == 0
            ):
                subprocess.run(["xdg-open", file_path], check=False)
                browser_opened = True

        # Use environment variable if available
        browser = os.environ.get("BROWSER")
        if browser and not browser_opened:
            subprocess.run([browser, file_path], check=False)
            browser_opened = True

    except Exception as e:
        click.echo(f"⚠️  Could not open browser automatically: {e}")
        click.echo(f"Please open manually: {file_path}")
        return

    if browser_opened:
        click.echo("🌐 Opening graph in web browser...")
    else:
        click.echo("⚠️  Could not open browser automatically: No suitable browser command found")
        click.echo(f"Please open manually: {file_path}")
