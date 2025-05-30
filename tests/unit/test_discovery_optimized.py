"""Comprehensive unit tests for discovery_optimized module.

Tests the optimized task discovery functions that provide performance enhancements
through caching, bulk processing, and optimized algorithms.
"""

import pytest
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Set

from src.warifuri.core.discovery_optimized import (
    TaskCache,
    _task_cache,
    discover_tasks_optimized,
    build_dependency_graph_optimized,
    find_ready_tasks_optimized,
    detect_cycles_optimized,
    monitor_performance,
    _cached_find_instruction_files,
)
from src.warifuri.core.types import Task, TaskInstruction, TaskType, TaskStatus


class TestTaskCache:
    """Test TaskCache class functionality."""

    def test_cache_initialization(self):
        """Test TaskCache initialization with empty caches."""
        cache = TaskCache()
        assert cache._task_cache == {}
        assert cache._dependency_cache == {}
        assert cache._last_modified == {}

    def test_get_task_not_cached(self):
        """Test getting a task that is not cached returns None."""
        cache = TaskCache()
        task_path = Path("/fake/path")

        result = cache.get_task(task_path)
        assert result is None

    def test_get_task_no_instruction_file(self):
        """Test getting a task when instruction file doesn't exist."""
        cache = TaskCache()
        task_path = Path("/fake/path")

        # Add to cache but no file exists
        cache._task_cache[str(task_path)] = Mock()

        result = cache.get_task(task_path)
        assert result is None

    def test_cache_task_without_instruction_file(self):
        """Test caching a task when instruction.yaml doesn't exist."""
        cache = TaskCache()

        # Create mock task
        mock_task = Mock()
        mock_task.path = Path("/fake/path")

        cache.cache_task(mock_task)

        assert str(mock_task.path) in cache._task_cache
        assert cache._task_cache[str(mock_task.path)] == mock_task

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_cache_task_with_instruction_file(self, mock_stat, mock_exists):
        """Test caching a task with instruction.yaml file."""
        cache = TaskCache()
        mock_exists.return_value = True
        mock_stat.return_value.st_mtime = 1234567890.0

        # Create mock task
        mock_task = Mock()
        mock_task.path = Path("/fake/path")

        cache.cache_task(mock_task)

        assert str(mock_task.path) in cache._task_cache
        assert cache._last_modified[str(mock_task.path)] == 1234567890.0

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_get_task_cache_valid(self, mock_stat, mock_exists):
        """Test getting a cached task when cache is still valid."""
        cache = TaskCache()
        mock_exists.return_value = True
        mock_stat.return_value.st_mtime = 1234567890.0

        # Create and cache task
        mock_task = Mock()
        mock_task.path = Path("/fake/path")
        cache._task_cache[str(mock_task.path)] = mock_task
        cache._last_modified[str(mock_task.path)] = 1234567890.0

        result = cache.get_task(mock_task.path)
        assert result == mock_task

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.stat')
    def test_get_task_cache_invalidated(self, mock_stat, mock_exists):
        """Test getting a cached task when cache is invalidated by file modification."""
        cache = TaskCache()
        mock_exists.return_value = True
        mock_stat.return_value.st_mtime = 1234567891.0  # Different time

        # Create and cache task with old modification time
        mock_task = Mock()
        mock_task.path = Path("/fake/path")
        cache._task_cache[str(mock_task.path)] = mock_task
        cache._last_modified[str(mock_task.path)] = 1234567890.0  # Old time

        result = cache.get_task(mock_task.path)
        assert result is None
        assert str(mock_task.path) not in cache._task_cache


class TestCachedFindInstructionFiles:
    """Test the cached instruction file finder."""

    @patch('src.warifuri.core.discovery_optimized.find_instruction_files')
    def test_cached_find_instruction_files(self, mock_find_files):
        """Test cached instruction file finding."""
        mock_paths = [Path("/path1/instruction.yaml"), Path("/path2/instruction.yaml")]
        mock_find_files.return_value = mock_paths

        result = _cached_find_instruction_files("/workspace")

        assert result == ("/path1/instruction.yaml", "/path2/instruction.yaml")
        mock_find_files.assert_called_once_with(Path("/workspace"))

    @patch('src.warifuri.core.discovery_optimized.find_instruction_files')
    def test_cached_find_instruction_files_caching(self, mock_find_files):
        """Test that the function caches results."""
        mock_paths = [Path("/path1/instruction.yaml")]
        mock_find_files.return_value = mock_paths

        # Clear any existing cache
        _cached_find_instruction_files.cache_clear()

        # First call
        result1 = _cached_find_instruction_files("/workspace")
        # Second call (should use cache)
        result2 = _cached_find_instruction_files("/workspace")

        assert result1 == result2
        # Should only be called once due to caching
        mock_find_files.assert_called_once()


class TestDiscoverTasksOptimized:
    """Test optimized task discovery."""

    @patch('src.warifuri.core.discovery_optimized._cached_find_instruction_files')
    def test_discover_tasks_optimized_empty(self, mock_find_files):
        """Test task discovery with no instruction files."""
        mock_find_files.return_value = ()

        result = discover_tasks_optimized(Path("/workspace"))

        assert result == []

    @patch('src.warifuri.core.discovery_optimized._cached_find_instruction_files')
    @patch('src.warifuri.core.discovery_optimized._task_cache')
    def test_discover_tasks_optimized_cached_task(self, mock_cache, mock_find_files):
        """Test task discovery using cached task."""
        mock_find_files.return_value = ("/project/task/instruction.yaml",)

        # Mock cached task
        cached_task = Mock()
        mock_cache.get_task.return_value = cached_task

        result = discover_tasks_optimized(Path("/workspace"))

        assert len(result) == 1
        assert result[0] == cached_task
        mock_cache.get_task.assert_called_once()

    @patch('src.warifuri.core.discovery_optimized._cached_find_instruction_files')
    @patch('src.warifuri.core.discovery_optimized._task_cache')
    @patch('src.warifuri.core.discovery.discover_task')
    def test_discover_tasks_optimized_new_task(self, mock_discover_task, mock_cache, mock_find_files):
        """Test task discovery loading new task."""
        mock_find_files.return_value = ("/project/task/instruction.yaml",)
        mock_cache.get_task.return_value = None  # Not cached

        # Mock discovered task
        discovered_task = Mock()
        mock_discover_task.return_value = discovered_task

        result = discover_tasks_optimized(Path("/workspace"))

        assert len(result) == 1
        assert result[0] == discovered_task
        mock_discover_task.assert_called_once_with("project", Path("/project/task"))
        mock_cache.cache_task.assert_called_once_with(discovered_task)

    @patch('src.warifuri.core.discovery_optimized._cached_find_instruction_files')
    @patch('src.warifuri.core.discovery_optimized._task_cache')
    @patch('src.warifuri.core.discovery.discover_task')
    def test_discover_tasks_optimized_task_load_exception(self, mock_discover_task, mock_cache, mock_find_files):
        """Test task discovery handling exceptions during task loading."""
        mock_find_files.return_value = ("/project/task/instruction.yaml",)
        mock_cache.get_task.return_value = None
        mock_discover_task.side_effect = Exception("Load error")

        result = discover_tasks_optimized(Path("/workspace"))

        assert result == []

    @patch('src.warifuri.core.discovery_optimized._cached_find_instruction_files')
    @patch('src.warifuri.core.discovery_optimized._task_cache')
    @patch('src.warifuri.core.discovery.discover_task')
    def test_discover_tasks_optimized_task_returns_none(self, mock_discover_task, mock_cache, mock_find_files):
        """Test task discovery when discover_task returns None."""
        mock_find_files.return_value = ("/project/task/instruction.yaml",)
        mock_cache.get_task.return_value = None
        mock_discover_task.return_value = None

        result = discover_tasks_optimized(Path("/workspace"))

        assert result == []


class TestBuildDependencyGraphOptimized:
    """Test optimized dependency graph building."""

    def test_build_dependency_graph_empty(self):
        """Test building dependency graph with no tasks."""
        result = build_dependency_graph_optimized([])
        assert result == {}

    def test_build_dependency_graph_no_dependencies(self):
        """Test building dependency graph with tasks that have no dependencies."""
        task1 = Mock()
        task1.full_name = "project/task1"
        task1.instruction.dependencies = []

        task2 = Mock()
        task2.full_name = "project/task2"
        task2.instruction.dependencies = []

        result = build_dependency_graph_optimized([task1, task2])

        assert result == {
            "project/task1": set(),
            "project/task2": set()
        }

    def test_build_dependency_graph_with_dependencies(self):
        """Test building dependency graph with valid dependencies."""
        task1 = Mock()
        task1.full_name = "project/task1"
        task1.instruction.dependencies = []

        task2 = Mock()
        task2.full_name = "project/task2"
        task2.instruction.dependencies = ["project/task1"]

        result = build_dependency_graph_optimized([task1, task2])

        assert result == {
            "project/task1": set(),
            "project/task2": {"project/task1"}
        }

    def test_build_dependency_graph_invalid_dependency(self):
        """Test building dependency graph with invalid dependencies."""
        task1 = Mock()
        task1.full_name = "project/task1"
        task1.instruction.dependencies = ["project/nonexistent"]

        with patch('src.warifuri.core.discovery_optimized.logger') as mock_logger:
            result = build_dependency_graph_optimized([task1])

            assert result == {"project/task1": set()}
            mock_logger.warning.assert_called_once()


class TestFindReadyTasksOptimized:
    """Test optimized ready task finding."""

    def test_find_ready_tasks_empty(self):
        """Test finding ready tasks with empty task list."""
        result = find_ready_tasks_optimized([], {})
        assert result == []

    def test_find_ready_tasks_no_dependencies(self):
        """Test finding ready tasks with no dependencies."""
        task1 = Mock()
        task1.full_name = "project/task1"
        task1.path = Path("/project/task1")

        dependency_graph = {"project/task1": set()}

        with patch.object(Path, 'exists', return_value=False):
            result = find_ready_tasks_optimized([task1], dependency_graph)

        assert len(result) == 1
        assert result[0] == task1

    def test_find_ready_tasks_completed_task(self):
        """Test finding ready tasks excluding completed tasks."""
        task1 = Mock()
        task1.full_name = "project/task1"
        task1.path = Path("/project/task1")

        dependency_graph = {"project/task1": set()}

        # Mock that done.md exists (task is completed)
        with patch.object(Path, 'exists', return_value=True):
            result = find_ready_tasks_optimized([task1], dependency_graph)

        assert result == []

    def test_find_ready_tasks_dependencies_satisfied(self):
        """Test finding ready tasks with satisfied dependencies."""
        task1 = Mock()
        task1.full_name = "project/task1"
        task1.path = Mock()
        done_path1 = Mock()
        done_path1.exists.return_value = True  # task1 is completed
        task1.path.__truediv__ = Mock(return_value=done_path1)

        task2 = Mock()
        task2.full_name = "project/task2"
        task2.path = Mock()
        done_path2 = Mock()
        done_path2.exists.return_value = False  # task2 is not completed
        task2.path.__truediv__ = Mock(return_value=done_path2)

        dependency_graph = {
            "project/task1": set(),
            "project/task2": {"project/task1"}
        }

        result = find_ready_tasks_optimized([task1, task2], dependency_graph)

        assert len(result) == 1
        assert result[0] == task2

    def test_find_ready_tasks_dependencies_not_satisfied(self):
        """Test finding ready tasks with unsatisfied dependencies."""
        task1 = Mock()
        task1.full_name = "project/task1"
        task1.path = Path("/project/task1")

        task2 = Mock()
        task2.full_name = "project/task2"
        task2.path = Path("/project/task2")

        dependency_graph = {
            "project/task1": set(),
            "project/task2": {"project/task1"}
        }

        # Neither task is completed
        with patch.object(Path, 'exists', return_value=False):
            result = find_ready_tasks_optimized([task1, task2], dependency_graph)

        # Only task1 should be ready (no dependencies)
        assert len(result) == 1
        assert result[0] == task1


class TestDetectCyclesOptimized:
    """Test optimized cycle detection."""

    def test_detect_cycles_empty_graph(self):
        """Test cycle detection with empty graph."""
        result = detect_cycles_optimized({})
        assert result == []

    def test_detect_cycles_no_cycles(self):
        """Test cycle detection with acyclic graph."""
        graph = {
            "A": {"B"},
            "B": {"C"},
            "C": set()
        }

        result = detect_cycles_optimized(graph)
        assert result == []

    def test_detect_cycles_simple_cycle(self):
        """Test cycle detection with simple cycle."""
        graph = {
            "A": {"B"},
            "B": {"A"}
        }

        result = detect_cycles_optimized(graph)
        assert len(result) >= 1
        # Check that a cycle was found
        assert any("A" in cycle and "B" in cycle for cycle in result)

    def test_detect_cycles_self_loop(self):
        """Test cycle detection with self-loop."""
        graph = {
            "A": {"A"}
        }

        result = detect_cycles_optimized(graph)
        assert len(result) >= 1
        assert any("A" in cycle for cycle in result)

    def test_detect_cycles_complex_graph(self):
        """Test cycle detection with complex graph."""
        graph = {
            "A": {"B"},
            "B": {"C"},
            "C": {"A"},  # Creates cycle A->B->C->A
            "D": {"E"},
            "E": set()
        }

        result = detect_cycles_optimized(graph)
        assert len(result) >= 1
        # Check that the cycle includes A, B, C
        assert any(all(node in cycle for node in ["A", "B", "C"]) for cycle in result)

    def test_detect_cycles_early_termination(self):
        """Test that cycle detection terminates early with many cycles."""
        # Create a graph with many potential cycles
        graph = {}
        for i in range(20):
            next_i = (i + 1) % 20
            graph[str(i)] = {str(next_i)}

        result = detect_cycles_optimized(graph)
        # Should find cycles but stop at limit
        assert len(result) > 0


class TestMonitorPerformance:
    """Test performance monitoring decorator."""

    def test_monitor_performance_fast_function(self):
        """Test performance monitoring with fast function."""
        @monitor_performance
        def fast_function():
            return "result"

        with patch('src.warifuri.core.discovery_optimized.logger') as mock_logger:
            result = fast_function()

            assert result == "result"
            # Should not log warning for fast function
            mock_logger.warning.assert_not_called()

    def test_monitor_performance_slow_function(self):
        """Test performance monitoring with slow function."""
        @monitor_performance
        def slow_function():
            time.sleep(0.1)  # Simulate slow operation
            return "result"

        with patch('src.warifuri.core.discovery_optimized.logger') as mock_logger:
            with patch('time.time', side_effect=[0, 1.5]):  # Mock slow operation
                result = slow_function()

                assert result == "result"
                mock_logger.warning.assert_called_once()

    def test_monitor_performance_with_args_kwargs(self):
        """Test performance monitoring with function arguments."""
        @monitor_performance
        def function_with_args(arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"

        result = function_with_args("a", "b", kwarg1="c")
        assert result == "a-b-c"


class TestGlobalCacheInstance:
    """Test global cache instance behavior."""

    def test_global_cache_instance_exists(self):
        """Test that global cache instance exists."""
        assert _task_cache is not None
        assert isinstance(_task_cache, TaskCache)

    def test_global_cache_shared_state(self):
        """Test that global cache maintains state across calls."""
        # Clear any existing state
        _task_cache._task_cache.clear()
        _task_cache._dependency_cache.clear()
        _task_cache._last_modified.clear()

        # Create mock task
        mock_task = Mock()
        mock_task.path = Path("/test/path")

        # Cache task
        _task_cache.cache_task(mock_task)

        # Verify it's cached
        assert str(mock_task.path) in _task_cache._task_cache
        assert _task_cache._task_cache[str(mock_task.path)] == mock_task


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple optimized functions."""

    @patch('src.warifuri.core.discovery_optimized._cached_find_instruction_files')
    @patch('src.warifuri.core.discovery.discover_task')
    def test_full_optimized_workflow(self, mock_discover_task, mock_find_files):
        """Test complete workflow using optimized functions."""
        mock_find_files.return_value = (
            "/workspace/project1/task1/instruction.yaml",
            "/workspace/project1/task2/instruction.yaml",
        )

        # Create mock tasks
        task1 = Mock()
        task1.full_name = "project1/task1"
        task1.path = Path("/workspace/project1/task1")
        task1.instruction.dependencies = []

        task2 = Mock()
        task2.full_name = "project1/task2"
        task2.path = Path("/workspace/project1/task2")
        task2.instruction.dependencies = ["project1/task1"]

        mock_discover_task.side_effect = [task1, task2]

        # Clear global cache
        _task_cache._task_cache.clear()

        # Discover tasks
        tasks = discover_tasks_optimized(Path("/workspace"))

        # Build dependency graph
        graph = build_dependency_graph_optimized(tasks)

        # Find ready tasks
        with patch.object(Path, 'exists', return_value=False):
            ready_tasks = find_ready_tasks_optimized(tasks, graph)

        # Detect cycles
        cycles = detect_cycles_optimized(graph)

        # Verify results
        assert len(tasks) == 2
        assert len(ready_tasks) == 1  # Only task1 should be ready
        assert ready_tasks[0] == task1
        assert cycles == []  # No cycles in this graph
        assert graph == {
            "project1/task1": set(),
            "project1/task2": {"project1/task1"}
        }
