"""Test template functionality in CLI commands."""

import pytest
from click.testing import CliRunner

from warifuri.cli.main import cli
from warifuri.utils.filesystem import safe_write_file


@pytest.fixture
def template_workspace(temp_workspace):
    """Create a workspace with test templates."""
    # Create data-pipeline template
    template_dir = temp_workspace / "templates" / "data-pipeline"

    # Create extract task
    extract_dir = template_dir / "extract"
    extract_dir.mkdir(parents=True)
    safe_write_file(
        extract_dir / "instruction.yaml",
        """name: extract
task_type: machine
description: Extract data from {{SOURCE}} to {{OUTPUT_FORMAT}}
dependencies: []
inputs:
  - "{{INPUT_FILE}}"
outputs:
  - "extracted_data.{{OUTPUT_FORMAT}}"
note: "Data extraction task for {{PROJECT_NAME}}"
""",
    )
    safe_write_file(
        extract_dir / "run.sh",
        """#!/bin/bash
# Extract data from {{SOURCE}}
echo "Extracting data for {{PROJECT_NAME}}"
""",
    )

    # Create transform task
    transform_dir = template_dir / "transform"
    transform_dir.mkdir(parents=True)
    safe_write_file(
        transform_dir / "instruction.yaml",
        """name: transform
task_type: ai
description: Transform extracted data using AI for {{PROJECT_NAME}}
dependencies:
  - extract
inputs:
  - "extracted_data.{{OUTPUT_FORMAT}}"
outputs:
  - "transformed_data.{{OUTPUT_FORMAT}}"
""",
    )
    safe_write_file(
        transform_dir / "prompt.yaml",
        """model: gpt-3.5-turbo
temperature: 0.1
system_prompt: "You are a data transformation expert for {{PROJECT_NAME}}"
user_prompt: "Transform the data with format {{OUTPUT_FORMAT}}"
""",
    )

    return temp_workspace


class TestTemplateInitialization:
    """Test template functionality in init command."""

    def test_template_whole_expansion_dry_run(self, template_workspace):
        """Test whole template expansion with dry run."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--workspace",
                str(template_workspace),
                "init",
                "--template",
                "data-pipeline",
                "--dry-run",
            ],
        )

        assert result.exit_code == 0
        assert "Would expand template 'data-pipeline' as project:" in result.output
        assert "Would create: " in result.output
        assert "extract/instruction.yaml" in result.output
        assert "transform/instruction.yaml" in result.output

    def test_template_whole_expansion_force(self, template_workspace):
        """Test whole template expansion with force flag."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--workspace",
                str(template_workspace),
                "init",
                "--template",
                "data-pipeline",
                "--force",
            ],
        )

        assert result.exit_code == 0
        assert "Template 'data-pipeline' expanded as project 'data-pipeline'" in result.output
        assert "Created tasks:" in result.output
        assert "data-pipeline/extract" in result.output
        assert "data-pipeline/transform" in result.output

        # Verify files were created with placeholder substitution
        project_dir = template_workspace / "projects" / "data-pipeline"
        assert project_dir.exists()

        extract_instruction = project_dir / "extract" / "instruction.yaml"
        assert extract_instruction.exists()
        content = extract_instruction.read_text()
        assert "source_data" in content  # {{SOURCE}} replaced
        assert "json" in content  # {{OUTPUT_FORMAT}} replaced
        assert "data-pipeline" in content  # {{PROJECT_NAME}} replaced

    def test_template_partial_expansion_task(self, template_workspace):
        """Test partial template expansion for task creation."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--workspace",
                str(template_workspace),
                "init",
                "custom-project/my-extract",
                "--template",
                "data-pipeline/extract",
                "--force",
            ],
        )

        assert result.exit_code == 0
        assert "Created task 'custom-project/my-extract'" in result.output

        # Verify task was created with correct substitution
        task_dir = template_workspace / "projects" / "custom-project" / "my-extract"
        assert task_dir.exists()

        instruction = task_dir / "instruction.yaml"
        assert instruction.exists()
        content = instruction.read_text()
        assert "custom-project" in content  # {{PROJECT_NAME}} replaced
        assert "source_data" in content  # {{SOURCE}} replaced

    def test_template_partial_expansion_project(self, template_workspace):
        """Test partial template expansion for project creation."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--workspace",
                str(template_workspace),
                "init",
                "my-project",
                "--template",
                "data-pipeline/extract",
                "--force",
            ],
        )

        assert result.exit_code == 0
        assert "Created project 'my-project'" in result.output

        # Verify project was created from single task template
        project_dir = template_workspace / "projects" / "my-project"
        assert project_dir.exists()

    def test_template_not_found(self, template_workspace):
        """Test error handling for non-existent template."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["--workspace", str(template_workspace), "init", "--template", "non-existent"]
        )

        assert result.exit_code == 0
        assert "Error: Template 'non-existent' not found" in result.output

    def test_template_existing_project_without_force(self, template_workspace):
        """Test error handling for existing project without force flag."""
        runner = CliRunner()

        # First creation
        result1 = runner.invoke(
            cli,
            [
                "--workspace",
                str(template_workspace),
                "init",
                "--template",
                "data-pipeline",
                "--force",
            ],
        )
        assert result1.exit_code == 0

        # Second creation without force should fail
        result2 = runner.invoke(
            cli, ["--workspace", str(template_workspace), "init", "--template", "data-pipeline"]
        )
        assert result2.exit_code == 0
        assert "already exists. Use --force to overwrite" in result2.output

    def test_placeholder_substitution_complex(self, template_workspace):
        """Test complex placeholder substitution in multiple files."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--workspace",
                str(template_workspace),
                "init",
                "--template",
                "data-pipeline",
                "--force",
            ],
        )

        assert result.exit_code == 0

        # Check extract run.sh file
        run_script = template_workspace / "projects" / "data-pipeline" / "extract" / "run.sh"
        assert run_script.exists()
        content = run_script.read_text()
        assert "Extracting data for data-pipeline" in content

        # Check transform prompt.yaml file
        prompt_file = (
            template_workspace / "projects" / "data-pipeline" / "transform" / "prompt.yaml"
        )
        assert prompt_file.exists()
        content = prompt_file.read_text()
        assert "data transformation expert for data-pipeline" in content
        assert "format json" in content

    def test_dependency_preservation(self, template_workspace):
        """Test that dependencies are preserved in template expansion."""
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--workspace",
                str(template_workspace),
                "init",
                "--template",
                "data-pipeline",
                "--force",
            ],
        )

        assert result.exit_code == 0

        # Check that transform task depends on extract
        transform_instruction = (
            template_workspace / "projects" / "data-pipeline" / "transform" / "instruction.yaml"
        )
        assert transform_instruction.exists()
        content = transform_instruction.read_text()
        assert "extract" in content
        assert "dependencies:" in content
