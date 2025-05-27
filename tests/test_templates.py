"""Test template expansion functionality."""

import pytest
from pathlib import Path
from warifuri.utils.templates import (
    expand_template_placeholders,
    expand_template_file,
    expand_template_directory,
)


class TestTemplateExpansion:
    """Test template placeholder expansion."""
    
    def test_expand_template_placeholders(self):
        """Test basic placeholder expansion."""
        text = "Hello {{NAME}}, welcome to {{PROJECT}}!"
        variables = {"NAME": "World", "PROJECT": "warifuri"}
        result = expand_template_placeholders(text, variables)
        assert result == "Hello World, welcome to warifuri!"
    
    def test_expand_template_placeholders_with_spaces(self):
        """Test placeholder expansion with spaces."""
        text = "{{ NAME }} and {{  PROJECT  }}"
        variables = {"NAME": "Alice", "PROJECT": "test"}
        result = expand_template_placeholders(text, variables)
        assert result == "Alice and test"
    
    def test_expand_template_placeholders_missing_variable(self):
        """Test that missing variables are left as-is."""
        text = "Hello {{NAME}}, {{MISSING}} variable"
        variables = {"NAME": "World"}
        result = expand_template_placeholders(text, variables)
        assert result == "Hello World, {{MISSING}} variable"
    
    def test_expand_template_file(self, temp_workspace):
        """Test expanding template file."""
        template_file = temp_workspace / "template.txt"
        template_file.write_text("Project: {{PROJECT_NAME}}\nAuthor: {{AUTHOR}}")
        
        variables = {"PROJECT_NAME": "test-project", "AUTHOR": "Test User"}
        result = expand_template_file(template_file, variables)
        
        expected = "Project: test-project\nAuthor: Test User"
        assert result == expected
    
    def test_expand_template_directory(self, temp_workspace):
        """Test expanding entire template directory."""
        # Create template directory
        template_dir = temp_workspace / "templates" / "basic"
        template_dir.mkdir(parents=True)
        
        # Create template files
        (template_dir / "README.md").write_text("# {{PROJECT_NAME}}")
        (template_dir / "config.yaml").write_text("name: {{PROJECT_NAME}}\nauthor: {{AUTHOR}}")
        
        # Create subdirectory
        sub_dir = template_dir / "src"
        sub_dir.mkdir()
        (sub_dir / "main.py").write_text("# Main file for {{PROJECT_NAME}}")
        
        # Expand template
        target_dir = temp_workspace / "projects" / "expanded"
        variables = {"PROJECT_NAME": "my-project", "AUTHOR": "Test User"}
        
        expand_template_directory(template_dir, target_dir, variables)
        
        # Verify expanded files
        assert (target_dir / "README.md").read_text() == "# my-project"
        assert (target_dir / "config.yaml").read_text() == "name: my-project\nauthor: Test User"
        assert (target_dir / "src" / "main.py").read_text() == "# Main file for my-project"
