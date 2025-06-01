"""Test configuration."""

# Standard library imports first
import importlib.util
import shutil
import sys
import tempfile
import types
from pathlib import Path
from typing import Generator


def _apply_snapshottest_python312_patch():
    """Apply Python 3.12 compatibility patch to snapshottest before it's imported."""
    if sys.version_info >= (3, 12) and "imp" not in sys.modules:
        # Create a mock imp module with our replacement function
        class MockImpModule:
            """Mock imp module for Python 3.12 compatibility."""

            def __init__(self):
                self.load_source = self._load_source_python312
                self.__name__ = "imp"
                self.__file__ = "<mock>"

            def _load_source_python312(self, module_name: str, filepath: str) -> types.ModuleType:
                """Replacement for imp.load_source using importlib."""
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not load module {module_name} from {filepath}")

                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                return module

            def __hash__(self):
                return hash(self.__name__)

            def __eq__(self, other):
                return isinstance(other, MockImpModule) or (
                    hasattr(other, "__name__") and other.__name__ == "imp"
                )

            def __repr__(self):
                return f"<MockImpModule '{self.__name__}'>"

        # Install mock imp module before any snapshottest imports
        sys.modules["imp"] = MockImpModule()


# Apply patch immediately when conftest.py is imported
_apply_snapshottest_python312_patch()

# Third-party imports
import pytest

# Local imports
from warifuri.utils import ensure_directory


def pytest_configure(config):
    """Pytest configuration hook - called very early in pytest initialization."""
    # Patch is already applied at module level
    pass


def pytest_sessionstart(session):
    """Pytest session start hook - apply patch if not already applied."""
    # Patch is already applied at module level
    pass


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
