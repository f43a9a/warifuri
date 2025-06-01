#!/usr/bin/env python3
"""Fix the graph command tests by adding isolated_filesystem() context."""

import re

def fix_graph_tests():
    """Fix the graph command tests to use isolated_filesystem()."""

    # Read the original file
    with open('tests/unit/test_graph_command.py', 'r') as f:
        content = f.read()

    # List of test functions that need fixing (the ones that were failing)
    test_functions = [
        'test_graph_command_no_projects',
        'test_graph_command_with_projects',
        'test_graph_command_dot_format',
        'test_graph_command_circular_dependency',
        'test_graph_command_html_format'
    ]

    for test_func in test_functions:
        # Find the test function
        pattern = rf'(def {test_func}\([^)]*\):.*?)(with patch\([^:]+?:.*?)(result = runner\.invoke\(graph[^)]*\))'

        def replace_func(match):
            func_part = match.group(1)
            patch_part = match.group(2)
            invoke_part = match.group(3)

            # Add isolated_filesystem wrapper
            new_content = func_part + '\n    with runner.isolated_filesystem():\n'
            new_content += '        # Create a workspace structure\n'
            new_content += '        Path("projects").mkdir()\n'
            new_content += '        \n'
            new_content += '        ' + patch_part.replace('\n    ', '\n        ')
            new_content += '            ' + invoke_part

            return new_content

        content = re.sub(pattern, replace_func, content, flags=re.DOTALL)

    # Write the fixed content
    with open('tests/unit/test_graph_command.py', 'w') as f:
        f.write(content)

    print(f"Fixed {len(test_functions)} test functions")

if __name__ == '__main__':
    fix_graph_tests()
