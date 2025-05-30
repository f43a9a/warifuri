# Warifuri Documentation

Welcome to Warifuri's documentation!

Warifuri is a task management system designed with Unix philosophy principles:
- Do one thing and do it well
- Make programs work together
- Handle text streams

## Quick Start

```bash
# Initialize a new workspace
warifuri init

# List available tasks
warifuri list

# Run a specific task
warifuri run <task-name>

# Show task dependencies
warifuri graph
```

## Architecture Overview

Warifuri consists of several core modules:

- **CLI Commands**: User interface commands
- **Core**: Task discovery, execution, and dependency resolution
- **Utils**: Shared utilities for validation, templates, and logging

## Contents

```{toctree}
:maxdepth: 2
:caption: User Guide

installation
quickstart
commands
templates
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/modules
api/cli
api/core
api/utils
```

```{toctree}
:maxdepth: 2
:caption: Development

development
contributing
unix_philosophy
```

## Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
