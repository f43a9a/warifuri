"""Test configuration."""

# Standard library imports first
import importlib.util
import shutil
import sys
import tempfile
import types
from pathlib import Path
from typing import Generator

# Third-party imports
import pytest

# Local imports
from warifuri.utils import ensure_directory


def _apply_snapshottest_python312_patch():
    """Apply Python 3.12 compatibility patch to snapshottest before it's imported."""

    def load_source_python312(module_name: str, filepath: str) -> types.ModuleType:
        """Replacement for imp.load_source using importlib."""
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module {module_name} from {filepath}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    # Create a mock imp module with our implementation
    mock_imp = types.SimpleNamespace()
    mock_imp.load_source = load_source_python312

    # Install the mock before snapshottest tries to import imp
    sys.modules['imp'] = mock_imp

    try:
        # Now safely import snapshottest
        import snapshottest.module
        # Also patch the module directly in case it's already imported
        snapshottest.module.imp = mock_imp
    except ImportError:
        # snapshottest not installed, skip patching
        pass


def pytest_configure(config):
    """Pytest configuration hook - called very early in pytest initialization."""
    _apply_snapshottest_python312_patch()


def pytest_sessionstart(session):
    """Pytest session start hook - apply patch if not already applied."""
    _apply_snapshottest_python312_patch()


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
