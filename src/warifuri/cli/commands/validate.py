"""Validate command for checking workspace integrity."""

import click

from ..context import Context, pass_context
from ...core.discovery import discover_all_projects
from ...utils import (
    ValidationError,
    detect_circular_dependencies,
    load_schema,
    validate_file_references,
    validate_instruction_yaml,
)


@click.command()
@click.option("--strict", is_flag=True, help="Enable strict validation mode")
@pass_context
def validate(
    ctx: Context,
    strict: bool,
) -> None:
    """Validate workspace configuration and dependencies."""
    workspace_path = ctx.workspace_path

    click.echo("Validating workspace...")

    errors = []
    warnings = []

    try:
        # Load schema
        schema = load_schema(workspace_path)
        click.echo("✅ Schema loaded successfully")

        # Discover projects
        projects = discover_all_projects(workspace_path)

        if not projects:
            warnings.append("No projects found in workspace")
        else:
            click.echo(f"✅ Found {len(projects)} project(s)")

        # Validate each task
        all_tasks = []
        for project in projects:
            for task in project.tasks:
                all_tasks.append(task)

                # Validate instruction.yaml against schema
                try:
                    # Normalize dependencies for schema validation
                    normalized_dependencies = []
                    for dep in task.instruction.dependencies:
                        # If dependency doesn't contain '/', assume it's within same project
                        if "/" not in dep:
                            normalized_dependencies.append(f"{project.name}/{dep}")
                        else:
                            normalized_dependencies.append(dep)

                    instruction_data = {
                        "name": task.instruction.name,
                        "description": task.instruction.description,
                        "dependencies": normalized_dependencies,
                        "inputs": task.instruction.inputs,
                        "outputs": task.instruction.outputs,
                    }
                    if task.instruction.note:
                        instruction_data["note"] = task.instruction.note

                    validate_instruction_yaml(instruction_data, schema, strict)
                    click.echo(f"✅ {task.full_name}: Schema validation passed")

                except ValidationError as e:
                    errors.append(f"{task.full_name}: {e}")
                    click.echo(f"❌ {task.full_name}: {e}")

                # Validate file references
                file_errors = validate_file_references(task, workspace_path, check_inputs=True)
                for error in file_errors:
                    if strict:
                        errors.append(f"{task.full_name}: {error}")
                        click.echo(f"❌ {task.full_name}: {error}")
                    else:
                        warnings.append(f"{task.full_name}: {error}")
                        click.echo(f"⚠️  {task.full_name}: {error}")

        # Check for circular dependencies
        try:
            cycle = detect_circular_dependencies(all_tasks)
            if cycle:
                cycle_str = " -> ".join(cycle)
                errors.append(f"Circular dependency detected: {cycle_str}")
                click.echo(f"❌ Circular dependency: {cycle_str}")
            else:
                click.echo("✅ No circular dependencies found")

        except Exception as e:
            errors.append(f"Dependency validation failed: {e}")
            click.echo(f"❌ Dependency validation failed: {e}")

        # Summary
        click.echo()
        click.echo("Validation Summary:")
        click.echo(f"  Tasks validated: {len(all_tasks)}")
        click.echo(f"  Errors: {len(errors)}")
        click.echo(f"  Warnings: {len(warnings)}")

        if errors:
            click.echo()
            click.echo("Errors found:")
            for error in errors:
                click.echo(f"  - {error}")
            raise click.Abort()

        if warnings:
            click.echo()
            click.echo("Warnings:")
            for warning in warnings:
                click.echo(f"  - {warning}")

        click.echo()
        if errors:
            click.echo("❌ Validation failed")
        else:
            click.echo("✅ Validation passed")

    except Exception as e:
        click.echo(f"❌ Validation error: {e}", err=True)
        raise click.Abort() from e
