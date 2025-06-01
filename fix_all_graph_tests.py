#!/usr/bin/env python3
"""Script to fix all remaining graph command tests."""

import re
from pathlib import Path

def fix_all_tests():
    """Fix all the failing graph command tests by adding proper workspace setup."""

    test_file = Path("tests/unit/test_graph_command.py")
    content = test_file.read_text()

    # List of test functions that need fixing
    failing_tests = [
        "test_graph_command_dot_format",
        "test_graph_command_circular_dependency",
        "test_graph_command_html_format"
    ]

    for test_name in failing_tests:
        print(f"Fixing {test_name}...")

        # Pattern to find the test function
        pattern = rf'(def {test_name}\([^:]+:.*?)(    with patch\("warifuri\.core\.discovery\.discover_all_projects_safe"\) as mock_discover:.*?)(        result = runner\.invoke\(graph[^)]*\).*?assert result\.exit_code == 0)'

        replacement = r'''\1    with runner.isolated_filesystem():
        # Create a workspace structure
        Path("projects").mkdir()
        workspace_path = Path.cwd()

        with (
            patch("warifuri.core.discovery.discover_all_projects_safe") as mock_discover,
            patch("warifuri.cli.context.Context.ensure_workspace_path") as mock_workspace,
        ):
            mock_discover.return_value = [mock_project]
            mock_workspace.return_value = workspace_path

\3'''

        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Special handling for circular dependency test that has additional mocks
    circular_pattern = r'(def test_graph_command_circular_dependency\([^:]+:.*?)(    with \(\s*patch\("warifuri\.core\.discovery\.discover_all_projects_safe"\) as mock_discover,\s*patch\("warifuri\.utils\.validation\.detect_circular_dependencies"\) as mock_detect,\s*\):.*?)(        result = runner\.invoke\(graph\).*?assert result\.exit_code == 0)'

    circular_replacement = r'''\1    with runner.isolated_filesystem():
        # Create a workspace structure
        Path("projects").mkdir()
        workspace_path = Path.cwd()

        with (
            patch("warifuri.core.discovery.discover_all_projects_safe") as mock_discover,
            patch("warifuri.utils.validation.detect_circular_dependencies") as mock_detect,
            patch("warifuri.cli.context.Context.ensure_workspace_path") as mock_workspace,
        ):
            mock_discover.return_value = [mock_project]
            mock_detect.return_value = ["task1", "task2"]
            mock_workspace.return_value = workspace_path

\3'''

    content = re.sub(circular_pattern, circular_replacement, content, flags=re.DOTALL)

    test_file.write_text(content)
    print("All tests fixed!")

if __name__ == "__main__":
    fix_all_tests()
