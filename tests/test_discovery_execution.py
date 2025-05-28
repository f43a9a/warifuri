"""Test task discovery and execution functionality."""

import pytest
from unittest.mock import patch, MagicMock
from warifuri.core.discovery import (
    discover_task,
    discover_project,
    discover_all_projects,
    determine_task_type,
    find_ready_tasks,
)
from warifuri.core.execution import execute_task
from warifuri.core.types import TaskType
from warifuri.utils import safe_write_file


class TestTaskDiscovery:
    """Test task discovery functionality."""

    @pytest.fixture
    def project_with_tasks(self, temp_workspace):
        """Create a project with multiple tasks."""
        project_dir = temp_workspace / "projects" / "test-project"

        # Create machine task
        machine_task = project_dir / "extract"
        machine_task.mkdir(parents=True)
        safe_write_file(machine_task / "instruction.yaml", """
name: extract
task_type: machine
description: Extract data
auto_merge: false
dependencies: []
inputs: []
outputs: [data.json]
""")
        safe_write_file(machine_task / "run.sh", "#!/bin/bash\necho 'extracted' > data.json")
        (machine_task / "run.sh").chmod(0o755)

        # Create AI task depending on machine task
        ai_task = project_dir / "transform"
        ai_task.mkdir(parents=True)
        safe_write_file(ai_task / "instruction.yaml", """
name: transform
task_type: ai
description: Transform data
auto_merge: false
dependencies: [extract]
inputs: [../extract/data.json]
outputs: [transformed.json]
""")
        safe_write_file(ai_task / "prompt.yaml", """
model: gpt-3.5-turbo
temperature: 0.7
system_prompt: "You are a data transformation assistant."
user_prompt: "Transform the data from {input} to {output}"
""")

        # Create human task
        human_task = project_dir / "review"
        human_task.mkdir(parents=True)
        safe_write_file(human_task / "instruction.yaml", """
name: review
task_type: human
description: Review results
auto_merge: false
dependencies: [transform]
inputs: [../transform/transformed.json]
outputs: []
""")

        return temp_workspace

    def test_determine_task_type_machine(self, temp_workspace):
        """Test task type detection for machine tasks."""
        task_path = temp_workspace / "task"
        task_path.mkdir()
        (task_path / "run.sh").touch()

        task_type = determine_task_type(task_path)
        assert task_type == TaskType.MACHINE

    def test_determine_task_type_ai(self, temp_workspace):
        """Test task type detection for AI tasks."""
        task_path = temp_workspace / "task"
        task_path.mkdir()
        (task_path / "prompt.yaml").touch()

        task_type = determine_task_type(task_path)
        assert task_type == TaskType.AI

    def test_determine_task_type_human(self, temp_workspace):
        """Test task type detection for human tasks."""
        task_path = temp_workspace / "task"
        task_path.mkdir()
        # No specific files = human task

        task_type = determine_task_type(task_path)
        assert task_type == TaskType.HUMAN

    def test_discover_task(self, project_with_tasks):
        """Test task discovery."""
        task = discover_task("test-project", project_with_tasks / "projects" / "test-project" / "extract")

        assert task.name == "extract"
        assert task.project == "test-project"
        assert task.task_type == TaskType.MACHINE
        assert task.instruction.description == "Extract data"
        assert not task.is_completed

    def test_discover_project(self, project_with_tasks):
        """Test project discovery."""
        project = discover_project(project_with_tasks, "test-project")

        assert project.name == "test-project"
        assert len(project.tasks) == 3

        task_names = [task.name for task in project.tasks]
        assert "extract" in task_names
        assert "transform" in task_names
        assert "review" in task_names

    def test_discover_all_projects(self, project_with_tasks):
        """Test discovering all projects."""
        projects = discover_all_projects(project_with_tasks)

        assert len(projects) == 1
        assert projects[0].name == "test-project"

    def test_find_ready_tasks(self, project_with_tasks):
        """Test finding ready tasks."""
        projects = discover_all_projects(project_with_tasks)
        ready_tasks = find_ready_tasks(projects)

        # Only extract should be ready (no dependencies)
        assert len(ready_tasks) == 1
        assert ready_tasks[0].name == "extract"


class TestTaskExecution:
    """Test task execution functionality."""

    @pytest.fixture
    def simple_machine_task(self, temp_workspace):
        """Create simple machine task."""
        task_dir = temp_workspace / "projects" / "test" / "simple"
        task_dir.mkdir(parents=True)

        safe_write_file(task_dir / "instruction.yaml", """
name: simple
task_type: machine
description: Simple test task
auto_merge: false
dependencies: []
inputs: []
outputs: [result.txt]
""")
        safe_write_file(task_dir / "run.sh", "#!/bin/bash\necho 'success' > result.txt")
        (task_dir / "run.sh").chmod(0o755)

        task = discover_task("test", task_dir)
        return task

    @pytest.fixture
    def simple_ai_task(self, temp_workspace):
        """Create simple AI task."""
        task_dir = temp_workspace / "projects" / "test" / "ai"
        task_dir.mkdir(parents=True)

        safe_write_file(task_dir / "instruction.yaml", """
name: ai
task_type: ai
description: Simple AI task
auto_merge: false
dependencies: []
inputs: []
outputs: [ai_result.txt]
""")
        safe_write_file(task_dir / "prompt.yaml", """
model: gpt-3.5-turbo
temperature: 0.7
system_prompt: "You are a helpful assistant."
user_prompt: "Generate a test output for file {output}"
""")

        task = discover_task("test", task_dir)
        return task

    @pytest.fixture
    def ai_task_with_inputs(self, temp_workspace):
        """Create AI task with input dependencies."""
        task_dir = temp_workspace / "projects" / "test" / "ai_with_input"
        task_dir.mkdir(parents=True)

        # Create input file
        input_file = task_dir / "input.txt"
        safe_write_file(input_file, "This is test input data for AI processing.")

        safe_write_file(task_dir / "instruction.yaml", """
name: ai_with_input
task_type: ai
description: AI task with input
auto_merge: false
dependencies: []
inputs: [input.txt]
outputs: [output.txt]
""")
        safe_write_file(task_dir / "prompt.yaml", """
model: gpt-3.5-turbo
temperature: 0.7
system_prompt: "You are a text processor."
user_prompt: "Process this input: {input_content} and generate output file {output}"
""")

        task = discover_task("test", task_dir)
        return task

    def test_execute_machine_task_dry_run(self, simple_machine_task):
        """Test machine task execution in dry run mode."""
        result = execute_task(simple_machine_task, dry_run=True)
        assert result is True

        # Output file should not exist in dry run
        output_file = simple_machine_task.path / "result.txt"
        assert not output_file.exists()

    def test_execute_machine_task(self, simple_machine_task):
        """Test actual machine task execution."""
        result = execute_task(simple_machine_task, dry_run=False)
        assert result is True

        # Check if done.md was created
        done_file = simple_machine_task.path / "done.md"
        assert done_file.exists()

        # Check if output was created
        output_file = simple_machine_task.path / "result.txt"
        assert output_file.exists()
        assert output_file.read_text().strip() == "success"

    def test_execute_ai_task_dry_run(self, simple_ai_task):
        """Test AI task execution in dry run mode."""
        result = execute_task(simple_ai_task, dry_run=True)
        assert result is True

    @patch('warifuri.utils.llm.LLMClient')
    def test_execute_ai_task_success(self, mock_llm_class, simple_ai_task):
        """Test successful AI task execution with mocked LLM."""
        # Mock LLM client
        mock_client = MagicMock()
        mock_client.generate_response.return_value = "Generated AI content for test output"
        mock_llm_class.return_value = mock_client

        # Execute task
        result = execute_task(simple_ai_task, dry_run=False)
        assert result is True

        # Check if done.md was created
        done_file = simple_ai_task.path / "done.md"
        assert done_file.exists()

        # Check if LLM was called
        mock_llm_class.assert_called_once()
        mock_client.generate_response.assert_called_once()

        # Check if AI response was saved in correct location
        response_file = simple_ai_task.path / "output" / "response.md"
        assert response_file.exists()
        content = response_file.read_text()
        assert "Generated AI content" in content

    @patch('warifuri.utils.llm.LLMClient')
    def test_execute_ai_task_with_inputs(self, mock_llm_class, ai_task_with_inputs):
        """Test AI task execution with input file processing."""
        # Mock LLM client
        mock_client = MagicMock()
        mock_client.generate_response.return_value = "Processed: This is test input data for AI processing."
        mock_llm_class.return_value = mock_client

        # Execute task
        result = execute_task(ai_task_with_inputs, dry_run=False)
        assert result is True

        # Check if LLM was called
        mock_client.generate_response.assert_called_once()

        # Check if AI response was saved
        response_file = ai_task_with_inputs.path / "output" / "response.md"
        assert response_file.exists()

    @patch('warifuri.utils.llm.LLMClient')
    def test_execute_ai_task_llm_error(self, mock_llm_class, simple_ai_task):
        """Test AI task execution when LLM fails."""
        from warifuri.utils.llm import LLMError

        # Mock LLM client to raise error
        mock_client = MagicMock()
        mock_client.generate_response.side_effect = LLMError("API key not found")
        mock_llm_class.return_value = mock_client

        # Execute task should handle error gracefully
        result = execute_task(simple_ai_task, dry_run=False)
        assert result is False  # Task should fail

        # Check that done.md was not created
        done_file = simple_ai_task.path / "done.md"
        assert not done_file.exists()

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key-123'})
    @patch('warifuri.utils.llm.LLMClient')
    def test_execute_ai_task_with_env_vars(self, mock_llm_class, simple_ai_task):
        """Test AI task execution with environment variables."""
        # Mock LLM client
        mock_client = MagicMock()
        mock_client.generate_response.return_value = "Success with env vars"
        mock_llm_class.return_value = mock_client

        result = execute_task(simple_ai_task, dry_run=False)
        assert result is True

        # Verify LLM client was instantiated
        mock_llm_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_ai_task(self, simple_ai_task):
        """Test actual AI task execution with mocked LLM client."""
        # Mock the LLM client and its methods
        mock_llm_client = MagicMock()
        mock_llm_client.generate_response.return_value = "mocked response"

        with patch("warifuri.utils.llm.LLMClient", return_value=mock_llm_client):
            result = execute_task(simple_ai_task, dry_run=False)
            assert result is True
        mock_llm_client.generate_response.assert_called_once()

        result = execute_task(simple_ai_task, dry_run=False)
        assert result is True


class TestAITaskExecution:
    """Test AI task execution functionality."""

    @pytest.fixture
    def mock_llm_response(self):
        """Standard mock LLM response."""
        return "This is a mock AI response generated for testing purposes."

    @pytest.fixture
    def simple_ai_task(self, temp_workspace):
        """Create simple AI task."""
        task_dir = temp_workspace / "projects" / "test" / "ai"
        task_dir.mkdir(parents=True)

        safe_write_file(task_dir / "instruction.yaml", """
name: ai
task_type: ai
description: Simple AI task
auto_merge: false
dependencies: []
inputs: []
outputs: [ai_result.txt]
""")
        safe_write_file(task_dir / "prompt.yaml", """
model: gpt-3.5-turbo
temperature: 0.7
system_prompt: "You are a helpful assistant."
user_prompt: "Generate a test output for file {output}"
""")

        task = discover_task("test", task_dir)
        return task

    @pytest.fixture
    def complex_ai_task(self, temp_workspace):
        """Create complex AI task with multiple inputs and outputs."""
        task_dir = temp_workspace / "projects" / "test" / "complex_ai"
        task_dir.mkdir(parents=True)

        # Create multiple input files
        safe_write_file(task_dir / "data1.txt", "First input data")
        safe_write_file(task_dir / "data2.json", '{"key": "value"}')

        safe_write_file(task_dir / "instruction.yaml", """
name: complex_ai
task_type: ai
description: Complex AI task with multiple inputs
auto_merge: false
dependencies: []
inputs: [data1.txt, data2.json]
outputs: [summary.txt, analysis.json]
""")
        safe_write_file(task_dir / "prompt.yaml", """
model: gpt-4
temperature: 0.3
system_prompt: "You are a data analyst."
user_prompt: |
  Analyze the following inputs:
  - Text data: {data1.txt}
  - JSON data: {data2.json}

  Generate:
  1. A summary in {summary.txt}
  2. Analysis results in {analysis.json}
""")

        task = discover_task("test", task_dir)
        return task

    @patch('warifuri.utils.llm.LLMClient')
    def test_ai_task_basic_execution(self, mock_llm_class, simple_ai_task, mock_llm_response):
        """Test basic AI task execution with mocked LLM."""
        mock_client = MagicMock()
        mock_client.generate_response.return_value = mock_llm_response
        mock_llm_class.return_value = mock_client

        result = execute_task(simple_ai_task, dry_run=False)
        assert result is True

        # Verify LLM was called with correct method
        mock_client.generate_response.assert_called_once()
        call_args = mock_client.generate_response.call_args[0]
        system_prompt, user_prompt = call_args

        assert "helpful assistant" in system_prompt
        assert "Simple AI task" in user_prompt

    @patch('warifuri.utils.llm.LLMClient')
    def test_ai_task_prompt_template_expansion(self, mock_llm_class, complex_ai_task, mock_llm_response):
        """Test that AI task properly expands prompt templates with input content."""
        mock_client = MagicMock()
        mock_client.generate_response.return_value = mock_llm_response
        mock_llm_class.return_value = mock_client

        result = execute_task(complex_ai_task, dry_run=False)
        assert result is True

        # Verify LLM was called with expanded prompt
        mock_client.generate_response.assert_called_once()

    @patch('warifuri.utils.llm.LLMClient')
    def test_ai_task_output_generation(self, mock_llm_class, simple_ai_task):
        """Test that AI task generates expected output files."""
        mock_client = MagicMock()
        mock_client.generate_response.return_value = "Generated content for ai_result.txt"
        mock_llm_class.return_value = mock_client

        result = execute_task(simple_ai_task, dry_run=False)
        assert result is True

        # Check AI response file was created in output directory
        response_file = simple_ai_task.path / "output" / "response.md"
        assert response_file.exists()

        content = response_file.read_text()
        assert "Generated content for ai_result.txt" in content

    @patch('warifuri.utils.llm.LLMClient')
    def test_ai_task_model_configuration(self, mock_llm_class, complex_ai_task):
        """Test that AI task respects model configuration from prompt.yaml."""
        mock_client = MagicMock()
        mock_client.generate_response.return_value = "Model config test"
        mock_llm_class.return_value = mock_client

        result = execute_task(complex_ai_task, dry_run=False)
        assert result is True

        # Verify LLM client was created with correct model and temperature
        mock_llm_class.assert_called_once_with(model="gpt-4", temperature=0.3)

    @patch('warifuri.utils.llm.LLMClient')
    def test_ai_task_llm_error_handling(self, mock_llm_class, simple_ai_task):
        """Test AI task handling when LLM fails."""
        from warifuri.utils.llm import LLMError

        # Mock LLM client to raise error
        mock_client = MagicMock()
        mock_client.generate_response.side_effect = LLMError("API key not found")
        mock_llm_class.return_value = mock_client

        # Execute task should handle error gracefully
        result = execute_task(simple_ai_task, dry_run=False)
        assert result is False  # Task should fail

        # Check that done.md was not created
        done_file = simple_ai_task.path / "done.md"
        assert not done_file.exists()

    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key-123'})
    @patch('warifuri.utils.llm.LLMClient')
    def test_ai_task_with_env_vars(self, mock_llm_class, simple_ai_task):
        """Test AI task execution with environment variables."""
        mock_client = MagicMock()
        mock_client.generate_response.return_value = "Success with env vars"
        mock_llm_class.return_value = mock_client

        result = execute_task(simple_ai_task, dry_run=False)
        assert result is True

        # Verify LLM client was instantiated
        mock_llm_class.assert_called_once()

    def test_ai_task_dry_run(self, simple_ai_task):
        """Test AI task execution in dry run mode."""
        result = execute_task(simple_ai_task, dry_run=True)
        assert result is True

    @patch('warifuri.utils.llm.LLMClient')
    def test_ai_task_missing_inputs_error(self, mock_llm_class, temp_workspace):
        """Test AI task handling when input files are missing."""
        task_dir = temp_workspace / "projects" / "test" / "missing_input"
        task_dir.mkdir(parents=True)

        safe_write_file(task_dir / "instruction.yaml", """
name: missing_input
task_type: ai
description: AI task with missing input
auto_merge: false
dependencies: []
inputs: [nonexistent.txt]
outputs: [output.txt]
""")
        safe_write_file(task_dir / "prompt.yaml", """
model: gpt-3.5-turbo
temperature: 0.7
system_prompt: "You are an assistant."
user_prompt: "Process {nonexistent.txt}"
""")

        task = discover_task("test", task_dir)

        mock_client = MagicMock()
        mock_client.generate_response.return_value = "Handled missing input"
        mock_llm_class.return_value = mock_client

        # Should handle missing input gracefully
        execute_task(task, dry_run=False)
        # Should succeed even with missing input (depends on implementation)

    @patch('warifuri.utils.llm.LLMClient')
    def test_ai_task_empty_prompt_config(self, mock_llm_class, temp_workspace):
        """Test AI task with empty or invalid prompt configuration."""
        task_dir = temp_workspace / "projects" / "test" / "empty_prompt"
        task_dir.mkdir(parents=True)

        safe_write_file(task_dir / "instruction.yaml", """
name: empty_prompt
task_type: ai
description: AI task with empty prompt
auto_merge: false
dependencies: []
inputs: []
outputs: [output.txt]
""")
        safe_write_file(task_dir / "prompt.yaml", "")  # Empty prompt config

        task = discover_task("test", task_dir)

        mock_client = MagicMock()
        mock_client.generate_response.return_value = "Default response"
        mock_llm_class.return_value = mock_client

        # Should handle empty config gracefully
        execute_task(task, dry_run=False)
        # Exact behavior depends on implementation


class TestDependencyResolution:
    """Test dependency resolution and validation."""

    def test_circular_dependency_detection(self, temp_workspace):
        """Test detection of circular dependencies."""
        project_dir = temp_workspace / "projects" / "circular"

        # Create task A depending on B
        task_a = project_dir / "task_a"
        task_a.mkdir(parents=True)
        safe_write_file(task_a / "instruction.yaml", """
name: task_a
task_type: human
description: Task A
auto_merge: false
dependencies: [task_b]
inputs: []
outputs: []
""")

        # Create task B depending on A (circular)
        task_b = project_dir / "task_b"
        task_b.mkdir(parents=True)
        safe_write_file(task_b / "instruction.yaml", """
name: task_b
task_type: human
description: Task B
auto_merge: false
dependencies: [task_a]
inputs: []
outputs: []
""")

        # This should be detected during project discovery
        from warifuri.utils.validation import CircularDependencyError

        # Should detect circular dependency during project discovery
        with pytest.raises(CircularDependencyError):
            discover_project(temp_workspace, "circular")
