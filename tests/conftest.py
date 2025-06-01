"""Test configuration."""

# Standard library imports first
import shutil
import tempfile
from pathlib import Path
from typing import Generator

# Third-party imports
import pytest

# Local imports
from warifuri.utils import ensure_directory


@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """Create temporary workspace for testing."""
    temp_dir = Path(tempfile.mkdtemp(prefix="warifuri_test_"))

    try:
        # Create basic workspace structure
        ensure_directory(temp_dir / "projects")
        ensure_directory(temp_dir / "templates")
        ensure_directory(temp_dir / "schemas")

        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_task_instruction() -> dict:
    """Sample task instruction data."""
    return {
        "name": "test_task",
        "description": "A test task for validation",
        "dependencies": [],
        "inputs": ["input.txt"],
        "outputs": ["output.txt"],
        "note": "Test note",
    }
