"""Template expansion utilities."""

import re
from pathlib import Path
from typing import Dict, List, Optional

from .filesystem import copy_directory_contents, ensure_directory


def expand_template_placeholders(text: str, variables: Dict[str, str]) -> str:
    """Expand template placeholders in text.
    
    Replaces {{VARIABLE}} with the corresponding value from variables.
    """
    for var, value in variables.items():
        pattern = rf'\{{\{{\s*{re.escape(var)}\s*\}}\}}'
        text = re.sub(pattern, value, text)
    return text


def expand_template_file(file_path: Path, variables: Dict[str, str]) -> str:
    """Expand template placeholders in a file and return the content."""
    content = file_path.read_text(encoding='utf-8')
    return expand_template_placeholders(content, variables)


def expand_template_directory(
    template_dir: Path,
    target_dir: Path,
    variables: Dict[str, str],
    skip_patterns: Optional[List[str]] = None
) -> None:
    """Expand a template directory to a target directory with variable substitution.
    
    Args:
        template_dir: Source template directory
        target_dir: Target directory to create
        variables: Variables for placeholder expansion
        skip_patterns: File patterns to skip (e.g., ['*.pyc', '__pycache__'])
    """
    if skip_patterns is None:
        skip_patterns = ['*.pyc', '__pycache__', '.git', '.gitignore']
    
    ensure_directory(target_dir)
    
    for item in template_dir.rglob('*'):
        if item.is_file():
            # Skip files matching patterns
            if any(item.match(pattern) for pattern in skip_patterns):
                continue
            
            # Calculate relative path and target path
            relative_path = item.relative_to(template_dir)
            target_path = target_dir / relative_path
            
            # Ensure target directory exists
            ensure_directory(target_path.parent)
            
            # Expand file content and write to target
            try:
                expanded_content = expand_template_file(item, variables)
                target_path.write_text(expanded_content, encoding='utf-8')
                
                # Copy file permissions
                target_path.chmod(item.stat().st_mode)
            except UnicodeDecodeError:
                # Binary file, copy as-is
                copy_directory_contents(item.parent, target_path.parent)


def get_template_variables_from_user(template_name: str) -> Dict[str, str]:
    """Get template variables from user input.
    
    This is a simple implementation - could be enhanced with
    a template configuration file that defines required variables.
    """
    variables = {}
    
    # Common variables
    common_vars = {
        'PROJECT_NAME': f"Enter project name (default: {template_name}): ",
        'SOURCE': "Enter data source: ",
        'OUTPUT_FORMAT': "Enter output format (default: json): ",
        'INPUT_FILE': "Enter input file path: ",
    }
    
    for var, prompt in common_vars.items():
        value = input(prompt).strip()
        if not value and var == 'PROJECT_NAME':
            value = template_name
        elif not value and var == 'OUTPUT_FORMAT':
            value = 'json'
        variables[var] = value
    
    return variables
