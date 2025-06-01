#!/usr/bin/env python3
"""
Debug helper for testing sample projects.
Provides detailed debugging information about task states and dependencies.
"""

import sys
from pathlib import Path
from typing import List

# Add src to path for importing warifuri modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from warifuri.core.discovery import discover_all_projects, find_ready_tasks
from warifuri.core.types import Project, TaskStatus
from warifuri.utils.validation import validate_file_references


def debug_task_states(projects: List[Project], workspace_path: Path) -> None:
    """Debug detailed task states and dependencies."""
    print("=" * 60)
    print("TASK STATE DEBUGGING")
    print("=" * 60)

    all_tasks = {}
    for project in projects:
        for task in project.tasks:
            all_tasks[task.full_name] = task

    for project in projects:
        print(f"\nProject: {project.name}")
        print(f"Path: {project.path}")
        print("-" * 40)

        for task in project.tasks:
            print(f"  Task: {task.name}")
            print(f"    Full Name: {task.full_name}")
            print(f"    Status: {task.status.name}")
            print(f"    Type: {task.task_type}")
            print(f"    Description: {task.instruction.description}")

            # Dependencies
            if task.depends:
                print(f"    Dependencies: {task.depends}")
                for dep_name in task.depends:
                    # Check if dependency exists
                    full_dep_name = dep_name
                    if "/" not in dep_name:
                        # Try with project prefix
                        full_dep_name = f"{project.name}/{dep_name}"

                    dep_task = all_tasks.get(dep_name) or all_tasks.get(full_dep_name)
                    if dep_task:
                        print(f"      -> {dep_name}: {dep_task.status.name}")
                    else:
                        print(f"      -> {dep_name}: NOT_FOUND")
            else:
                print("    Dependencies: None")

            # Inputs
            if task.inputs:
                print(f"    Inputs: {task.inputs}")
                for input_file in task.inputs:
                    input_path = workspace_path / input_file
                    exists = input_path.exists()
                    print(f"      -> {input_file}: {'EXISTS' if exists else 'MISSING'}")
                    if exists:
                        print(f"         Size: {input_path.stat().st_size} bytes")
            else:
                print("    Inputs: None")

            # Outputs
            if task.outputs:
                print(f"    Outputs: {task.outputs}")
                for output_file in task.outputs:
                    output_path = workspace_path / output_file
                    exists = output_path.exists()
                    print(f"      -> {output_file}: {'EXISTS' if exists else 'NOT_CREATED'}")
                    if exists:
                        print(f"         Size: {output_path.stat().st_size} bytes")
            else:
                print("    Outputs: None")

            print()


def debug_ready_tasks(projects: List[Project], workspace_path: Path) -> None:
    """Debug which tasks are ready to run."""
    print("=" * 60)
    print("READY TASKS ANALYSIS")
    print("=" * 60)

    ready_tasks = find_ready_tasks(projects, workspace_path)

    print(f"Ready tasks count: {len(ready_tasks)}")

    if ready_tasks:
        print("\nReady tasks:")
        for task in ready_tasks:
            print(f"  - {task.full_name}")
            print(f"    Status: {task.status.name}")
            print(f"    Command: {task.command}")
    else:
        print("\nNo tasks are ready to run.")

    print("\nTask readiness analysis:")
    for project in projects:
        for task in project.tasks:
            is_ready = task in ready_tasks
            print(f"  {task.full_name}: {'READY' if is_ready else 'NOT_READY'}")

            if not is_ready:
                # Analyze why not ready
                reasons = []

                # Check status
                if task.status == TaskStatus.COMPLETED:
                    reasons.append("Already completed")
                elif task.status == TaskStatus.RUNNING:
                    reasons.append("Currently running")

                # Check dependencies
                if task.depends:
                    all_tasks = {}
                    for p in projects:
                        for t in p.tasks:
                            all_tasks[t.full_name] = t

                    for dep_name in task.depends:
                        full_dep_name = dep_name
                        if "/" not in dep_name:
                            full_dep_name = f"{project.name}/{dep_name}"

                        dep_task = all_tasks.get(dep_name) or all_tasks.get(full_dep_name)
                        if not dep_task:
                            reasons.append(f"Dependency not found: {dep_name}")
                        elif dep_task.status != TaskStatus.COMPLETED:
                            reasons.append(f"Dependency not completed: {dep_name} ({dep_task.status.name})")

                # Check input files
                if task.inputs:
                    try:
                        validate_file_references(task, workspace_path)
                    except FileNotFoundError as e:
                        reasons.append(f"Input file missing: {str(e)}")

                if reasons:
                    print(f"    Reasons: {'; '.join(reasons)}")


def debug_file_validation(projects: List[Project], workspace_path: Path) -> None:
    """Debug file validation for all tasks."""
    print("=" * 60)
    print("FILE VALIDATION DEBUGGING")
    print("=" * 60)

    for project in projects:
        for task in project.tasks:
            if task.inputs:
                print(f"\nValidating files for {task.full_name}:")
                try:
                    validate_file_references(task, workspace_path)
                    print("  Validation: PASSED")
                except FileNotFoundError as e:
                    print(f"  Validation: FAILED - {str(e)}")

                for input_file in task.inputs:
                    input_path = workspace_path / input_file
                    print(f"  {input_file}: {'EXISTS' if input_path.exists() else 'MISSING'}")
                    if input_path.exists():
                        print(f"    Path: {input_path}")
                        print(f"    Size: {input_path.stat().st_size} bytes")


def run_sample_test(sample_name: str) -> None:
    """Run debug analysis for a specific sample project."""
    sample_path = Path(__file__).parent.parent / "sample-projects" / sample_name

    if not sample_path.exists():
        print(f"Sample project not found: {sample_path}")
        return

    print(f"Testing sample project: {sample_name}")
    print(f"Sample path: {sample_path}")

    # Change to sample directory
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(sample_path)

        # Discover projects
        projects = discover_all_projects(sample_path)

        print(f"\nDiscovered {len(projects)} project(s)")
        for project in projects:
            print(f"  - {project.name} ({len(project.tasks)} tasks)")

        # Run debugging
        debug_task_states(projects, sample_path)
        debug_ready_tasks(projects, sample_path)
        debug_file_validation(projects, sample_path)

    finally:
        os.chdir(original_cwd)


def main() -> None:
    """Main debug function."""
    if len(sys.argv) < 2:
        print("Usage: python debug_helper.py <sample_name>")
        print("Available samples:")
        samples_dir = Path(__file__).parent.parent / "sample-projects"
        if samples_dir.exists():
            for sample in samples_dir.iterdir():
                if sample.is_dir():
                    print(f"  - {sample.name}")
        return

    sample_name = sys.argv[1]
    run_sample_test(sample_name)


if __name__ == "__main__":
    main()
