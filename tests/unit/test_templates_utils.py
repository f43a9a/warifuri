"""Unit tests for template utilities."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from warifuri.utils.templates import (
    expand_template_placeholders,
    expand_template_file,
    expand_template_directory,
    get_template_variables_from_user,
)


def test_expand_template_placeholders_success():
    """Test successful placeholder expansion."""
    text = "Hello {{NAME}}, welcome to {{PROJECT}}!"
    variables = {"NAME": "Alice", "PROJECT": "Warifuri"}

    result = expand_template_placeholders(text, variables)

    assert result == "Hello Alice, welcome to Warifuri!"


def test_expand_template_placeholders_with_whitespace():
    """Test placeholder expansion with whitespace."""
    text = "Hello {{ NAME }}, project: {{  PROJECT  }}!"
    variables = {"NAME": "Bob", "PROJECT": "Test"}

    result = expand_template_placeholders(text, variables)

    assert result == "Hello Bob, project: Test!"


def test_expand_template_placeholders_no_variables():
    """Test placeholder expansion with no variables."""
    text = "No placeholders here"
    variables = {}

    result = expand_template_placeholders(text, variables)

    assert result == "No placeholders here"


def test_expand_template_placeholders_missing_variable():
    """Test placeholder expansion with missing variable."""
    text = "Hello {{NAME}}, missing {{MISSING}}!"
    variables = {"NAME": "Alice"}

    result = expand_template_placeholders(text, variables)

    # Missing variables are left unchanged
    assert result == "Hello Alice, missing {{MISSING}}!"


def test_expand_template_file_success():
    """Test successful template file expansion."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write("Project: {{PROJECT}}\nAuthor: {{AUTHOR}}")
        temp_file.flush()
        temp_path = Path(temp_file.name)

    try:
        variables = {"PROJECT": "Test Project", "AUTHOR": "Test Author"}
        result = expand_template_file(temp_path, variables)

        assert result == "Project: Test Project\nAuthor: Test Author"
    finally:
        temp_path.unlink()


def test_expand_template_file_unicode():
    """Test template file expansion with unicode characters."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as temp_file:
        temp_file.write("Welcome {{NAME}} 🎉\nProject: {{PROJECT}} ⭐")
        temp_file.flush()
        temp_path = Path(temp_file.name)

    try:
        variables = {"NAME": "Alice", "PROJECT": "Warifuri"}
        result = expand_template_file(temp_path, variables)

        assert result == "Welcome Alice 🎉\nProject: Warifuri ⭐"
    finally:
        temp_path.unlink()


def test_expand_template_directory_success():
    """Test successful template directory expansion."""
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir) / "template"
        target_dir = Path(temp_dir) / "target"
        template_dir.mkdir()

        # Create template files
        (template_dir / "README.md").write_text("# {{PROJECT}}\nAuthor: {{AUTHOR}}")
        sub_dir = template_dir / "src"
        sub_dir.mkdir()
        (sub_dir / "main.py").write_text("# Main file for {{PROJECT}}")

        variables = {"PROJECT": "Test Project", "AUTHOR": "Test Author"}

        expand_template_directory(template_dir, target_dir, variables)

        # Check files were created and expanded
        assert (target_dir / "README.md").exists()
        assert (target_dir / "src" / "main.py").exists()

        readme_content = (target_dir / "README.md").read_text()
        assert readme_content == "# Test Project\nAuthor: Test Author"

        main_content = (target_dir / "src" / "main.py").read_text()
        assert main_content == "# Main file for Test Project"


def test_expand_template_directory_with_skip_patterns():
    """Test template directory expansion with skip patterns."""
    with tempfile.TemporaryDirectory() as temp_dir:
        template_dir = Path(temp_dir) / "template"
        target_dir = Path(temp_dir) / "target"
        template_dir.mkdir()

        # Create files including ones to skip
        (template_dir / "README.md").write_text("# {{PROJECT}}")
        (template_dir / "test.pyc").write_text("compiled")
        pycache_dir = template_dir / "__pycache__"
        pycache_dir.mkdir()
        (pycache_dir / "cache.pyc").write_text("cache")

        variables = {"PROJECT": "Test Project"}
        skip_patterns = ["*.pyc", "__pycache__"]

        expand_template_directory(template_dir, target_dir, variables, skip_patterns)

        # Check only README was copied
        assert (target_dir / "README.md").exists()
        assert not (target_dir / "test.pyc").exists()
        assert not (target_dir / "__pycache__").exists()


@patch('builtins.input')
def test_get_template_variables_interactive(mock_input):
    """Test getting template variables interactively."""
    mock_input.side_effect = ["My Project", "data.csv", "xml", "input.txt"]

    result = get_template_variables_from_user("test_template")

    expected = {
        "PROJECT_NAME": "My Project",
        "SOURCE": "data.csv",
        "OUTPUT_FORMAT": "xml",
        "INPUT_FILE": "input.txt"
    }
    assert result == expected


@patch('builtins.input')
def test_get_template_variables_with_defaults(mock_input):
    """Test getting template variables with default values."""
    mock_input.side_effect = ["", "custom_source", "", ""]

    result = get_template_variables_from_user("my_template")

    expected = {
        "PROJECT_NAME": "my_template",  # Used default
        "SOURCE": "custom_source",      # Custom value
        "OUTPUT_FORMAT": "json",        # Used default
        "INPUT_FILE": "input.txt"       # Used default
    }
    assert result == expected


def test_get_template_variables_non_interactive():
    """Test getting template variables in non-interactive mode."""
    result = get_template_variables_from_user("test_template", non_interactive=True)

    expected = {
        "PROJECT_NAME": "test_template",
        "SOURCE": "source_data",
        "OUTPUT_FORMAT": "json",
        "INPUT_FILE": "input.txt"
    }
    assert result == expected
