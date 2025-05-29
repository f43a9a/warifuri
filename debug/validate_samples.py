#!/usr/bin/env python3
"""
Validate sample projects structure and configuration.
Checks that all sample projects are correctly configured.
"""

import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for importing warifuri modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from warifuri.core.discovery import discover_all_projects
from warifuri.core.types import TaskStatus


def validate_project_files(sample_path: Path) -> List[str]:
    """Validate that required project files exist."""
    issues = []

    # Check for project YAML files
    yaml_files = list(sample_path.glob("project-*.yaml"))
    if not yaml_files:
        issues.append("No project YAML files found")

    # Check for README
    readme_file = sample_path / "README.md"
    if not readme_file.exists():
        issues.append("README.md not found")

    # Check for scripts directory
    scripts_dir = sample_path / "scripts"
    if not scripts_dir.exists():
        issues.append("scripts/ directory not found")
    elif not any(scripts_dir.glob("*.py")):
        issues.append("No Python scripts found in scripts/")

    return issues


def validate_project_yaml(yaml_file: Path) -> List[str]:
    """Validate project YAML structure."""
    issues = []

    try:
        with open(yaml_file, 'r') as f:
            project_data = yaml.safe_load(f)

        # Check required fields
        if 'name' not in project_data:
            issues.append(f"{yaml_file.name}: Missing 'name' field")

        if 'description' not in project_data:
            issues.append(f"{yaml_file.name}: Missing 'description' field")

        if 'tasks' not in project_data:
            issues.append(f"{yaml_file.name}: Missing 'tasks' field")
        else:
            tasks = project_data['tasks']
            if not isinstance(tasks, dict):
                issues.append(f"{yaml_file.name}: 'tasks' should be a dictionary")
            else:
                for task_name, task_config in tasks.items():
                    # Check required task fields
                    if 'command' not in task_config:
                        issues.append(f"{yaml_file.name}: Task '{task_name}' missing 'command' field")

                    # Validate command references existing script
                    if 'command' in task_config:
                        command = task_config['command']
                        if 'python scripts/' in command:
                            script_name = command.split('python scripts/')[1].split()[0]
                            script_path = yaml_file.parent / "scripts" / script_name
                            if not script_path.exists():
                                issues.append(f"{yaml_file.name}: Task '{task_name}' references non-existent script: {script_name}")

    except yaml.YAMLError as e:
        issues.append(f"{yaml_file.name}: YAML parsing error: {str(e)}")
    except Exception as e:
        issues.append(f"{yaml_file.name}: Error reading file: {str(e)}")

    return issues


def validate_script_files(sample_path: Path) -> List[str]:
    """Validate Python script files."""
    issues = []

    scripts_dir = sample_path / "scripts"
    if not scripts_dir.exists():
        return ["scripts/ directory not found"]

    for script_file in scripts_dir.glob("*.py"):
        try:
            # Check if file is readable and has basic structure
            content = script_file.read_text(encoding='utf-8')

            # Check for main function
            if 'def main(' not in content:
                issues.append(f"{script_file.name}: No main() function found")

            # Check for if __name__ == "__main__" guard
            if 'if __name__ == "__main__"' not in content:
                issues.append(f"{script_file.name}: Missing __main__ guard")

            # Check for shebang
            if not content.startswith('#!/usr/bin/env python3'):
                issues.append(f"{script_file.name}: Missing or incorrect shebang")

            # Check for docstring
            lines = content.split('\n')
            has_docstring = False
            for line in lines[1:10]:  # Check first few lines after shebang
                if '"""' in line:
                    has_docstring = True
                    break

            if not has_docstring:
                issues.append(f"{script_file.name}: Missing module docstring")

        except Exception as e:
            issues.append(f"{script_file.name}: Error reading file: {str(e)}")

    return issues


def validate_sample_discovery(sample_path: Path) -> List[str]:
    """Validate that warifuri can discover the projects."""
    issues = []

    try:
        projects = discover_all_projects(sample_path)

        if not projects:
            issues.append("No projects discovered by warifuri")
        else:
            for project in projects:
                if not project.tasks:
                    issues.append(f"Project '{project.name}' has no tasks")

                for task in project.tasks:
                    # Check that task is properly initialized
                    if not task.name:
                        issues.append(f"Task in project '{project.name}' has no name")

                    if not task.command:
                        issues.append(f"Task '{task.name}' has no command")

                    # Check initial status
                    if task.status not in [TaskStatus.PENDING, TaskStatus.READY]:
                        issues.append(f"Task '{task.full_name}' has unexpected initial status: {task.status}")

    except Exception as e:
        issues.append(f"Error during project discovery: {str(e)}")

    return issues


def validate_dependencies(sample_path: Path) -> List[str]:
    """Validate task dependencies are correctly specified."""
    issues = []

    try:
        projects = discover_all_projects(sample_path)

        # Build task lookup
        all_tasks = {}
        for project in projects:
            for task in project.tasks:
                all_tasks[task.full_name] = task
                # Also add short name for same-project references
                all_tasks[task.name] = task

        for project in projects:
            for task in project.tasks:
                if task.depends:
                    for dep_name in task.depends:
                        # Check if dependency exists
                        found = False

                        # Direct match
                        if dep_name in all_tasks:
                            found = True

                        # Try with project prefix
                        elif "/" not in dep_name:
                            full_dep_name = f"{project.name}/{dep_name}"
                            if full_dep_name in all_tasks:
                                found = True

                        # Try cross-project reference
                        elif "/" in dep_name:
                            if dep_name in all_tasks:
                                found = True

                        if not found:
                            issues.append(f"Task '{task.full_name}' depends on non-existent task: '{dep_name}'")

    except Exception as e:
        issues.append(f"Error during dependency validation: {str(e)}")

    return issues


def validate_sample_project(sample_name: str, sample_path: Path) -> Dict[str, Any]:
    """Validate a complete sample project."""
    print(f"Validating {sample_name}...")

    validation_result = {
        "sample_name": sample_name,
        "valid": True,
        "issues": []
    }

    # File structure validation
    issues = validate_project_files(sample_path)
    validation_result["issues"].extend(issues)

    # YAML validation
    for yaml_file in sample_path.glob("project-*.yaml"):
        issues = validate_project_yaml(yaml_file)
        validation_result["issues"].extend(issues)

    # Script validation
    issues = validate_script_files(sample_path)
    validation_result["issues"].extend(issues)

    # Discovery validation
    issues = validate_sample_discovery(sample_path)
    validation_result["issues"].extend(issues)

    # Dependency validation
    issues = validate_dependencies(sample_path)
    validation_result["issues"].extend(issues)

    if validation_result["issues"]:
        validation_result["valid"] = False

    return validation_result


def main() -> None:
    """Main validation function."""
    print("=" * 70)
    print("SAMPLE PROJECTS VALIDATION")
    print("=" * 70)

    samples_dir = Path(__file__).parent.parent / "sample-projects"

    if not samples_dir.exists():
        print("Sample projects directory not found!")
        return

    # Get all sample projects
    sample_projects = []
    for sample_dir in samples_dir.iterdir():
        if sample_dir.is_dir():
            sample_projects.append(sample_dir)

    if not sample_projects:
        print("No sample projects found!")
        return

    print(f"Found {len(sample_projects)} sample project(s):")
    for sample in sample_projects:
        print(f"  - {sample.name}")

    # Validate each sample
    all_results = []
    for sample_dir in sample_projects:
        result = validate_sample_project(sample_dir.name, sample_dir)
        all_results.append(result)

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    total_samples = len(all_results)
    valid_samples = sum(1 for r in all_results if r["valid"])
    invalid_samples = total_samples - valid_samples

    print(f"Total samples: {total_samples}")
    print(f"Valid: {valid_samples}")
    print(f"Invalid: {invalid_samples}")

    # Detailed results
    for result in all_results:
        status = "✓ VALID" if result["valid"] else "✗ INVALID"
        print(f"\n{result['sample_name']}: {status}")

        if result["issues"]:
            for issue in result["issues"]:
                print(f"  • {issue}")

    # Save results
    results_file = Path(__file__).parent / "validation_results.json"
    import json
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nValidation results saved to: {results_file}")

    # Exit with appropriate code
    sys.exit(0 if invalid_samples == 0 else 1)


if __name__ == "__main__":
    main()
