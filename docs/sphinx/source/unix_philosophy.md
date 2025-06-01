# Unix Philosophy in Warifuri

Warifuri is designed following the Unix Philosophy principles. This document outlines how these principles are applied and areas for improvement.

## Core Unix Philosophy Principles

### 1. Do One Thing and Do It Well

Each module in Warifuri has a focused responsibility:

- **CLI Commands**: Handle user interaction and command parsing
- **Core Discovery**: Find and analyze tasks and dependencies
- **Core Execution**: Execute tasks safely and manage environments
- **Utils**: Provide shared utilities

### 2. Make Programs Work Together

Warifuri follows composition patterns:

- Tasks can depend on outputs from other tasks
- Cross-project dependencies enable collaboration
- JSON/YAML data interchange formats
- Standard input/output handling

### 3. Handle Text Streams

- YAML configuration files
- JSON data interchange
- Text-based logging
- Standard shell integration

## Current Analysis Results

Based on the Unix Philosophy compliance analysis, we identified areas for improvement:

### Large Functions (>50 lines)

The following functions should be broken down:

**automation.py:**
- `automation_list()` (77 lines) → Extract template rendering logic
- `check_automation()` (87 lines) → Split validation and execution
- `create_pr()` (157 lines, 11 params) → Extract PR formatting and GitHub API calls

**graph.py:**
- `_create_html_graph()` (168 lines) → Extract HTML generation and styling

**execution.py:**
- `execute_machine_task()` (127 lines) → Split environment setup, execution, and cleanup
- `copy_input_files()` (85 lines) → Extract file validation and copying logic

### Large Files (>300 lines)

- **automation.py** (429 lines): Split into automation core and GitHub integration
- **graph.py** (339 lines): Extract visualization rendering
- **execution.py** (640 lines): Split into execution engine and file handling
- **github.py** (520 lines): Split API client from business logic

## Recommended Refactoring

### 1. Extract Service Objects

```python
# Instead of large functions, use service objects
class TaskExecutionService:
    def setup_environment(self, task: Task) -> Dict[str, str]: ...
    def validate_inputs(self, task: Task) -> bool: ...
    def execute_safely(self, task: Task) -> ExecutionResult: ...
    def cleanup_resources(self, task: Task) -> None: ...
```

### 2. Use Composition over Large Classes

```python
# Split large modules into focused components
class GitHubClient:  # Pure API interactions
class IssueFormatter:  # Format issue content
class LabelManager:  # Manage GitHub labels
```

### 3. Apply Command Pattern

```python
# Make CLI commands pure coordinators
class RunCommand:
    def __init__(self, discovery: DiscoveryService, execution: ExecutionService):
        self.discovery = discovery
        self.execution = execution

    def run(self, task_name: str) -> None:
        task = self.discovery.find_task(task_name)
        result = self.execution.execute(task)
        self.report_result(result)
```

## Implementation Priority

1. **High Priority**: Break down functions >100 lines
2. **Medium Priority**: Extract service objects from large files
3. **Low Priority**: Optimize for composition patterns

This refactoring will improve:
- Testability (smaller, focused units)
- Maintainability (clear separation of concerns)
- Reusability (composable components)
- Debugging (isolated failure points)
