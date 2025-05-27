# warifuri

A minimal CLI for task allocation between humans, AI, and machines in GitHub repositories.

## Overview

warifuri enables seamless task distribution and execution across different actors:
- **Machine tasks**: Automated scripts (`.sh`, `.py`)
- **AI tasks**: LLM-powered tasks (via `prompt.yaml`)
- **Human tasks**: Manual intervention required

## Key Features

- **State-less**: Task completion determined by `done.md` file existence
- **Dependency-driven**: Execution order based on task dependencies
- **Role-free**: Task type automatically determined by file presence
- **Safety-first**: Sandboxed execution and circular dependency detection
- **Template support**: Reusable task templates across projects

## Installation

```bash
# Install with Poetry
poetry install

# Or install with pip
pip install -e .
```

## Quick Start

1. **Initialize a project**:
   ```bash
   warifuri init my-project
   ```

2. **Create a task**:
   ```bash
   warifuri init my-project/setup-database
   ```

3. **List tasks**:
   ```bash
   warifuri list --ready
   ```

4. **Run ready tasks**:
   ```bash
   warifuri run
   ```

5. **Validate workspace**:
   ```bash
   warifuri validate
   ```

## Directory Structure

```
workspace/
├── projects/
│   └── <project>/
│       └── <task>/
│           ├── instruction.yaml    # Task definition
│           ├── run.sh             # Machine task (optional)
│           ├── prompt.yaml        # AI task (optional)
│           ├── done.md            # Completion marker
│           └── auto_merge.yaml    # Auto-merge flag (optional)
├── templates/                     # Reusable task templates
└── schemas/                       # Local schema overrides
```

## Commands

- `warifuri init` - Create projects and tasks
- `warifuri list` - List tasks with status
- `warifuri run` - Execute ready tasks
- `warifuri show` - Display task details
- `warifuri validate` - Check workspace integrity
- `warifuri graph` - Visualize dependencies
- `warifuri mark-done` - Mark tasks as completed
- `warifuri template list` - List available templates
- `warifuri issue` - Create GitHub issues

## Task Types

### Machine Tasks
Contain executable scripts (`.sh` or `.py`). Executed in sandboxed temporary directories.

### AI Tasks
Contain `prompt.yaml` for LLM interaction. Responses saved to `output/response.md`.

### Human Tasks
No executable files. Require manual intervention.

## Configuration

Set log level via environment variable or CLI option:
```bash
export WARIFURI_LOG_LEVEL=DEBUG
warifuri --log-level INFO run
```

## Development

```bash
# Install development dependencies
poetry install --with dev

# Run tests
pytest

# Run linting
ruff check .
black --check .

# Type checking
mypy warifuri/
```

## License

MIT License - see LICENSE file for details.
