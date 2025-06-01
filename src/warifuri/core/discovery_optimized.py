"""Optimized task discovery with performance enhancements."""

import logging
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Callable, Any
from functools import lru_cache

from .types import Task
from ..utils.filesystem import find_instruction_files

logger = logging.getLogger(__name__)


class TaskCache:
    """Cache for task discovery results."""

    def __init__(self) -> None:
        self._task_cache: Dict[str, Task] = {}
        self._dependency_cache: Dict[str, Set[str]] = {}
        self._last_modified: Dict[str, float] = {}

    def get_task(self, task_path: Path) -> Optional[Task]:
        """Get cached task if still valid."""
        path_str = str(task_path)

        if path_str not in self._task_cache:
            return None

        # Check if instruction file was modified
        instruction_file = task_path / "instruction.yaml"
        if not instruction_file.exists():
            return None

        current_mtime = instruction_file.stat().st_mtime
        if current_mtime != self._last_modified.get(path_str, 0):
            # Invalidate cache
            self._task_cache.pop(path_str, None)
            self._dependency_cache.pop(path_str, None)
            return None

        return self._task_cache[path_str]

    def cache_task(self, task: Task) -> None:
        """Cache task with modification time."""
        path_str = str(task.path)
        self._task_cache[path_str] = task

        instruction_file = task.path / "instruction.yaml"
        if instruction_file.exists():
            self._last_modified[path_str] = instruction_file.stat().st_mtime


# Global cache instance
_task_cache = TaskCache()


@lru_cache(maxsize=128)
def _cached_find_instruction_files(workspace_path: str) -> Tuple[str, ...]:
    """Cached version of find_instruction_files."""
    return tuple(str(p) for p in find_instruction_files(Path(workspace_path)))


def discover_tasks_optimized(workspace_path: Path) -> List[Task]:
    """Discover tasks with performance optimizations."""
    logger.debug(f"Discovering tasks in: {workspace_path}")
    start_time = time.time()

    tasks = []
    instruction_files = _cached_find_instruction_files(str(workspace_path))

    # Batch process instruction files
    for instruction_file_str in instruction_files:
        instruction_file = Path(instruction_file_str)
        task_path = instruction_file.parent

        # Check cache first
        cached_task = _task_cache.get_task(task_path)
        if cached_task:
            tasks.append(cached_task)
            continue

        try:
            # Load task (this could be further optimized with bulk YAML loading)
            from .discovery import discover_task

            project_name = task_path.parent.name
            task = discover_task(project_name, task_path)

            if task:
                tasks.append(task)
                _task_cache.cache_task(task)

        except Exception as e:
            logger.warning(f"Failed to load task from {task_path}: {e}")
            continue

    elapsed = time.time() - start_time
    logger.debug(f"Discovered {len(tasks)} tasks in {elapsed:.3f}s")

    return tasks


def build_dependency_graph_optimized(tasks: List[Task]) -> Dict[str, Set[str]]:
    """Build dependency graph with optimizations."""
    logger.debug("Building optimized dependency graph")
    start_time = time.time()

    # Create task lookup for O(1) access
    task_lookup = {task.full_name: task for task in tasks}

    # Build adjacency list representation
    graph = {}

    for task in tasks:
        task_deps = set()

        # Process dependencies efficiently
        for dep in task.instruction.dependencies:
            if dep in task_lookup:
                task_deps.add(dep)
            else:
                logger.warning(f"Task {task.full_name} depends on non-existent task: {dep}")

        graph[task.full_name] = task_deps

    elapsed = time.time() - start_time
    logger.debug(f"Built dependency graph in {elapsed:.3f}s")

    return graph


def find_ready_tasks_optimized(
    tasks: List[Task], dependency_graph: Dict[str, Set[str]]
) -> List[Task]:
    """Find ready tasks using optimized algorithms."""
    if not tasks:
        return []

    logger.debug("Finding ready tasks with optimization")
    start_time = time.time()

    # Create lookup sets for O(1) membership testing
    completed_tasks = {task.full_name for task in tasks if (task.path / "done.md").exists()}

    ready_tasks = []

    for task in tasks:
        # Skip if already completed
        if task.full_name in completed_tasks:
            continue

        # Check if all dependencies are satisfied
        task_deps = dependency_graph.get(task.full_name, set())

        if task_deps.issubset(completed_tasks):
            ready_tasks.append(task)

    elapsed = time.time() - start_time
    logger.debug(f"Found {len(ready_tasks)} ready tasks in {elapsed:.3f}s")

    return ready_tasks


def detect_cycles_optimized(dependency_graph: Dict[str, Set[str]]) -> List[List[str]]:
    """Detect cycles using optimized DFS with early termination."""
    logger.debug("Detecting cycles with optimization")
    start_time = time.time()

    WHITE, GRAY, BLACK = 0, 1, 2
    colors = {node: WHITE for node in dependency_graph}
    cycles = []

    def dfs(node: str, path: List[str]) -> None:
        if colors[node] == GRAY:
            # Found cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return

        if colors[node] == BLACK:
            return

        colors[node] = GRAY
        path.append(node)

        for neighbor in dependency_graph.get(node, []):
            if neighbor in dependency_graph:  # Only visit existing nodes
                dfs(neighbor, path)

        path.pop()
        colors[node] = BLACK

    # Process nodes in topological order hint for better performance
    for node in sorted(dependency_graph.keys()):
        if colors[node] == WHITE:
            dfs(node, [])

        # Early termination if cycles found and we only need to detect existence
        if cycles and len(cycles) >= 10:  # Limit cycle detection for performance
            break

    elapsed = time.time() - start_time
    logger.debug(f"Cycle detection completed in {elapsed:.3f}s")

    return cycles


# Performance monitoring decorator
def monitor_performance(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to monitor function performance."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time

        if elapsed > 1.0:  # Log slow operations
            logger.warning(f"Slow operation detected: {func.__name__} took {elapsed:.3f}s")

        return result

    return wrapper


# Apply performance monitoring to key functions
discover_tasks_optimized = monitor_performance(discover_tasks_optimized)
build_dependency_graph_optimized = monitor_performance(build_dependency_graph_optimized)
