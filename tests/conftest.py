"""Test configuration."""

# Apply Python 3.12 compatibility patch for snapshottest
import sys
import importlib.util
import types

def _patch_snapshottest_for_python312():
    """Patch snapshottest to work with Python 3.12+ by replacing imp with importlib."""
    def load_source_python312(module_name: str, filepath: str) -> types.ModuleType:
        """Replacement for imp.load_source using importlib."""
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module {module_name} from {filepath}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    try:
        import snapshottest.module
        # Replace imp.load_source with our importlib implementation
        snapshottest.module.imp = types.SimpleNamespace()
        snapshottest.module.imp.load_source = load_source_python312
    except ImportError:
        # snapshottest not installed, skip patching
        pass

# Apply the patch immediately
_patch_snapshottest_for_python312()

import pytest
from pathlib import Path
import tempfile
import shutil
from typing import Generator

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
