"""
Monkey patch for snapshottest to work with Python 3.12+
This replaces the deprecated imp module with importlib.
"""
import sys
import importlib.util
import types
from typing import Any


def load_source_python312(module_name: str, filepath: str) -> types.ModuleType:
    """Replacement for imp.load_source using importlib."""
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {filepath}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def apply_snapshottest_patch() -> None:
    """Apply the Python 3.12 compatibility patch to snapshottest."""
    try:
        import snapshottest.module
        # Replace imp.load_source with our importlib implementation
        snapshottest.module.imp = types.SimpleNamespace()
        snapshottest.module.imp.load_source = load_source_python312
    except ImportError:
        # snapshottest not installed, skip patching
        pass


# Apply the patch when this module is imported
apply_snapshottest_patch()
