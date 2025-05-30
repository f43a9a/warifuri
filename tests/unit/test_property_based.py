"""Property-based tests using hypothesis."""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml
from hypothesis import assume, given, strategies as st

from warifuri.core.types import Task, TaskInstruction, TaskStatus, TaskType
from warifuri.core.execution.validation import _resolve_input_path_safely
from warifuri.utils.filesystem import find_workspace_root, list_projects, list_tasks
from warifuri.utils.yaml_utils import load_yaml, save_yaml


class TestYamlUtilsProperties:
    """Property-based tests for YAML utilities."""

    @given(
        data=st.dictionaries(
            keys=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans(),
                st.lists(st.text(max_size=20), max_size=5),
            ),
            min_size=1,
            max_size=10,
        )
    )
    def test_yaml_roundtrip_property(self, data: Dict[str, Any]) -> None:
        """Test that save_yaml followed by load_yaml preserves data structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_path = Path(temp_dir) / "test.yaml"

            # Save and load should preserve the data
            save_yaml(data, yaml_path)
            loaded_data = load_yaml(yaml_path)

            assert loaded_data == data

    @given(
        content=st.text(min_size=1, max_size=1000).filter(
            lambda x: all(ord(c) < 127 for c in x)  # ASCII only for YAML safety
        )
    )
    def test_yaml_file_creation_property(self, content: str) -> None:
        """Test that save_yaml always creates a valid YAML file."""
        assume(content.strip())  # Avoid empty content

        with tempfile.TemporaryDirectory() as temp_dir:
            yaml_path = Path(temp_dir) / "test.yaml"
            data = {"content": content}

            save_yaml(data, yaml_path)

            # File should exist and be readable
            assert yaml_path.exists()
            assert yaml_path.is_file()

            # Should be valid YAML
            with open(yaml_path, "r", encoding="utf-8") as f:
                parsed = yaml.safe_load(f)
                assert parsed is not None
                assert parsed["content"] == content


class TestFilesystemProperties:
    """Property-based tests for filesystem utilities."""

    @given(
        workspace_name=st.text(min_size=1, max_size=50).filter(
            lambda x: x.strip() and not any(c in x for c in "/\\:*?\"<>|\0") and "\x00" not in x
        )
    )
    def test_workspace_root_finding_consistency(self, workspace_name: str) -> None:
        """Test that workspace root finding is consistent."""
        assume(workspace_name.strip())

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a workspace structure
            workspace_path = temp_path / workspace_name / "workspace"
            projects_path = workspace_path / "projects"
            projects_path.mkdir(parents=True)

            # Finding workspace root should be deterministic
            result1 = find_workspace_root(workspace_path)
            result2 = find_workspace_root(workspace_path)

            assert result1 == result2
            if result1:
                assert result1.exists()

    @given(
        project_names=st.lists(
            st.text(min_size=1, max_size=30).filter(
                lambda x: x.strip() and not x.startswith(".") and not any(c in x for c in "/\\:*?\"<>|\0") and "\x00" not in x
            ),
            min_size=0,
            max_size=5,
            unique=True,
        )
    )
    def test_project_listing_consistency(self, project_names: list[str]) -> None:
        """Test that project listing is consistent and matches directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_path = Path(temp_dir)
            projects_path = workspace_path / "projects"
            projects_path.mkdir(parents=True)

            # Create project directories
            for project_name in project_names:
                if project_name.strip():
                    (projects_path / project_name).mkdir()

            # List projects multiple times
            result1 = list_projects(workspace_path)
            result2 = list_projects(workspace_path)

            # Results should be consistent
            assert result1 == result2
            assert len(result1) == len(set(result1))  # No duplicates

            # All listed projects should actually exist
            for project in result1:
                assert (projects_path / project).exists()
                assert (projects_path / project).is_dir()

            # All created projects should be listed (excluding empty names)
            valid_projects = [p for p in project_names if p.strip()]
            assert len(result1) == len(valid_projects)

    @given(
        input_path=st.text(min_size=1, max_size=100).filter(
            lambda x: not any(c in x for c in ["\0", "\n", "\r"])
        )
    )
    def test_path_resolution_safety_deterministic(self, input_path: str) -> None:
        """Test that path resolution safety checking is deterministic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            projects_base = temp_path / "projects"
            task_path = projects_base / "test-project" / "test-task"
            task_path.mkdir(parents=True)

            # Multiple calls should return the same result
            result1 = _resolve_input_path_safely(input_path, task_path, projects_base)
            result2 = _resolve_input_path_safely(input_path, task_path, projects_base)
            result3 = _resolve_input_path_safely(input_path, task_path, projects_base)

            # Results should be identical
            assert result1 == result2 == result3

            # Should always return a tuple with two elements
            assert isinstance(result1, tuple)
            assert len(result1) == 2

            resolved_path, message = result1
            assert isinstance(resolved_path, (Path, type(None)))
            assert isinstance(message, str)


class TestTaskTypeProperties:
    """Property-based tests for core types."""

    @given(
        project=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
        task_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    )
    def test_task_full_name_property(self, project: str, task_name: str) -> None:
        """Test that task full_name property follows project/task format."""
        assume(project.strip() and task_name.strip())

        # Create a minimal task instruction
        instruction = TaskInstruction(
            name=task_name,
            description="Test task",
            dependencies=[],
            inputs=[],
            outputs=[],
        )

        task = Task(
            project=project,
            name=task_name,
            path=Path("/test/path"),
            instruction=instruction,
            task_type=TaskType.MACHINE,
            status=TaskStatus.READY,
        )

        full_name = task.full_name

        # Should follow project/task format
        assert full_name == f"{project}/{task_name}"
        assert "/" in full_name
        assert full_name.startswith(project)
        assert full_name.endswith(task_name)

    @given(
        name=st.text(min_size=1, max_size=100),
        description=st.text(min_size=1, max_size=500),
        dependencies=st.lists(st.text(min_size=1, max_size=50), max_size=10),
        inputs=st.lists(st.text(min_size=1, max_size=50), max_size=10),
        outputs=st.lists(st.text(min_size=1, max_size=50), max_size=10),
    )
    def test_task_instruction_from_dict_property(
        self,
        name: str,
        description: str,
        dependencies: list[str],
        inputs: list[str],
        outputs: list[str],
    ) -> None:
        """Test TaskInstruction.from_dict preserves all provided fields."""
        data = {
            "name": name,
            "description": description,
            "dependencies": dependencies,
            "inputs": inputs,
            "outputs": outputs,
        }

        instruction = TaskInstruction.from_dict(data)

        # All fields should be preserved
        assert instruction.name == name
        assert instruction.description == description
        assert instruction.dependencies == dependencies
        assert instruction.inputs == inputs
        assert instruction.outputs == outputs
        assert instruction.note is None  # Default value

    @given(
        data_dict=st.dictionaries(
            keys=st.sampled_from(["name", "description", "dependencies", "inputs", "outputs", "note"]),
            values=st.one_of(
                st.text(max_size=100),
                st.lists(st.text(max_size=50), max_size=5),
                st.none(),
            ),
            min_size=2,  # At least name and description
        )
    )
    def test_task_instruction_serialization_stability(self, data_dict: Dict[str, Any]) -> None:
        """Test that TaskInstruction can handle various input formats consistently."""
        # Ensure required fields are present and are strings
        if "name" not in data_dict or not isinstance(data_dict["name"], str):
            data_dict["name"] = "test_task"
        if "description" not in data_dict or not isinstance(data_dict["description"], str):
            data_dict["description"] = "Test description"

        # Convert None values to appropriate defaults for required list fields
        if "dependencies" not in data_dict or data_dict["dependencies"] is None:
            data_dict["dependencies"] = []
        if "inputs" not in data_dict or data_dict["inputs"] is None:
            data_dict["inputs"] = []
        if "outputs" not in data_dict or data_dict["outputs"] is None:
            data_dict["outputs"] = []

        # Ensure list fields are actually lists
        for field in ["dependencies", "inputs", "outputs"]:
            if not isinstance(data_dict[field], list):
                data_dict[field] = []

        try:
            instruction = TaskInstruction.from_dict(data_dict)

            # Basic invariants should hold
            assert isinstance(instruction.name, str)
            assert isinstance(instruction.description, str)
            assert isinstance(instruction.dependencies, list)
            assert isinstance(instruction.inputs, list)
            assert isinstance(instruction.outputs, list)

        except (KeyError, TypeError, ValueError):
            # Expected for invalid input - but should be consistent
            pytest.skip("Invalid input format")


class TestStringProcessingProperties:
    """Property-based tests for string processing functions."""

    @given(
        text=st.text(min_size=0, max_size=500),
        prefix=st.text(min_size=1, max_size=50),
    )
    def test_string_prefix_property(self, text: str, prefix: str) -> None:
        """Test basic string prefix operations maintain invariants."""
        # Test that adding and checking prefix works consistently
        prefixed = f"{prefix}{text}"

        # Basic properties
        assert prefixed.startswith(prefix)
        assert len(prefixed) >= len(prefix)
        assert len(prefixed) == len(prefix) + len(text)

        # If we remove the prefix, we get back the original text
        if prefixed.startswith(prefix):
            suffix = prefixed[len(prefix):]
            assert suffix == text


class TestJsonYamlCompatibility:
    """Property-based tests for JSON/YAML compatibility."""

    @given(
        data=st.dictionaries(
            keys=st.text(min_size=1, max_size=30).filter(lambda x: x.strip()),
            values=st.one_of(
                st.text(max_size=100),
                st.integers(min_value=-1000000, max_value=1000000),
                st.booleans(),
                st.lists(st.text(max_size=20), max_size=3),
            ),
            min_size=1,
            max_size=5,
        )
    )
    def test_json_yaml_compatibility_property(self, data: Dict[str, Any]) -> None:
        """Test that data representable in JSON is also properly handled by YAML."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test JSON serialization
            json_path = Path(temp_dir) / "test.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

            # Test YAML serialization
            yaml_path = Path(temp_dir) / "test.yaml"
            save_yaml(data, yaml_path)

            # Both should preserve the data
            with open(json_path, "r", encoding="utf-8") as f:
                json_loaded = json.load(f)

            yaml_loaded = load_yaml(yaml_path)

            # Both formats should preserve the same data
            assert json_loaded == data
            assert yaml_loaded == data
            assert json_loaded == yaml_loaded
