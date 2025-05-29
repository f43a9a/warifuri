#!/usr/bin/env python3
"""Direct test of find_ready_tasks function."""

import sys
sys.path.insert(0, 'src')

from pathlib import Path
from warifuri.core.discovery import discover_all_projects, find_ready_tasks
from warifuri.utils.filesystem import safe_write_file
import tempfile
import inspect

def test_function_signature():
    """Test the function signature."""
    sig = inspect.signature(find_ready_tasks)
    print(f"Function signature: {sig}")
    print(f"Parameters: {list(sig.parameters.keys())}")

def test_basic_functionality():
    """Test basic functionality."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        projects_dir = workspace / "projects"
        project_dir = projects_dir / "test"
        task_dir = project_dir / "task1"
        task_dir.mkdir(parents=True)

        safe_write_file(task_dir / "instruction.yaml", """
name: task1
task_type: human
description: "Test task"
dependencies: []
inputs: []
outputs: []
""")

        projects = discover_all_projects(workspace)
        print(f"Found projects: {len(projects)}")

        # Test with workspace_path parameter
        try:
            ready_tasks = find_ready_tasks(projects, workspace)
            print(f"Ready tasks with workspace_path: {len(ready_tasks)}")
        except Exception as e:
            print(f"Error with workspace_path: {e}")

        # Test without workspace_path parameter
        try:
            ready_tasks = find_ready_tasks(projects)
            print(f"Ready tasks without workspace_path: {len(ready_tasks)}")
        except Exception as e:
            print(f"Error without workspace_path: {e}")

if __name__ == "__main__":
    test_function_signature()
    test_basic_functionality()
