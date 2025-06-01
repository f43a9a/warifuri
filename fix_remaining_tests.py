#!/usr/bin/env python3
"""Script to fix the remaining graph command tests."""

import re

def fix_test_file():
    with open('tests/unit/test_graph_command.py', 'r') as f:
        content = f.read()

    # Pattern to match the specific failing tests and add ensure_workspace_path mock
    patterns_to_fix = [
        'test_graph_command_dot_format',
        'test_graph_command_circular_dependency',
        'test_graph_command_html_format'
    ]

    for pattern in patterns_to_fix:
        # Find the test function and add the mock
        test_pattern = rf'(def {pattern}\([^:]+:\s*"""[^"]+"""\s*runner = CliRunner\(\)[^{{}}]+?)(with patch\("warifuri\.core\.discovery\.discover_all_projects_safe"\) as mock_discover:)'

        def replace_func(match):
            before = match.group(1)
            # Check if it already has isolated_filesystem
            if 'isolated_filesystem' in before:
                # Add workspace mock to existing isolated_filesystem
                return before.replace(
                    'with patch("warifuri.core.discovery.discover_all_projects_safe") as mock_discover:',
                    '''with runner.isolated_filesystem():
        # Create a workspace structure
        Path("projects").mkdir()
        workspace_path = Path.cwd()

        with (
            patch("warifuri.core.discovery.discover_all_projects_safe") as mock_discover,
            patch("warifuri.cli.context.Context.ensure_workspace_path") as mock_workspace,
        ):'''
                )
            else:
                # Add both isolated_filesystem and workspace mock
                return before + '''with runner.isolated_filesystem():
        # Create a workspace structure
        Path("projects").mkdir()
        workspace_path = Path.cwd()

        with (
            patch("warifuri.core.discovery.discover_all_projects_safe") as mock_discover,
            patch("warifuri.cli.context.Context.ensure_workspace_path") as mock_workspace,
        ):'''

        content = re.sub(test_pattern, replace_func, content, flags=re.DOTALL)

    # Also need to add mock_workspace.return_value calls
    content = content.replace(
        'mock_discover.return_value = [mock_project]',
        '''mock_discover.return_value = [mock_project]
            mock_workspace.return_value = workspace_path'''
    )

    content = content.replace(
        'mock_detect.return_value = ["task1", "task2"]',
        '''mock_detect.return_value = ["task1", "task2"]
            mock_workspace.return_value = workspace_path'''
    )

    with open('tests/unit/test_graph_command.py', 'w') as f:
        f.write(content)

    print("Fixed test file")

if __name__ == "__main__":
    fix_test_file()
