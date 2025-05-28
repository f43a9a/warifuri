Command Reference
=================

This section provides a comprehensive reference for all warifuri CLI commands.

Core Commands
-------------

warifuri init
~~~~~~~~~~~~~

Create new projects, tasks, or deploy templates.

**Syntax:**

.. code-block:: bash

    warifuri init <project>
    warifuri init <project>/<task>
    warifuri init --template <template>
    warifuri init <project> --template <template>/<task>

**Options:**

* ``--template <name>``: Use a specific template
* ``--force``: Overwrite existing files
* ``--dry-run``: Show what would be created without creating
* ``--non-interactive``: Skip interactive prompts

**Examples:**

.. code-block:: bash

    # Create a new project
    warifuri init my-project

    # Create a task in project
    warifuri init my-project/setup-task

    # Deploy from template
    warifuri init --template data-pipeline

warifuri list
~~~~~~~~~~~~~

Display tasks and their current status.

**Syntax:**

.. code-block:: bash

    warifuri list [--ready|--completed] [--project <name>] [--format <type>]

**Options:**

* ``--ready``: Show only ready-to-run tasks
* ``--completed``: Show only completed tasks
* ``--project <name>``: Filter by project
* ``--format <type>``: Output format (plain, json, tsv)
* ``--fields <list>``: Specify fields to display

**Examples:**

.. code-block:: bash

    # List all tasks
    warifuri list

    # List ready tasks in JSON format
    warifuri list --ready --format json

warifuri run
~~~~~~~~~~~~

Execute tasks with automatic dependency resolution.

**Syntax:**

.. code-block:: bash

    warifuri run [task-name]
    warifuri run --ready
    warifuri run --project <name>

**Options:**

* ``--ready``: Run all ready tasks automatically
* ``--project <name>``: Run all tasks in project
* ``--dry-run``: Show execution plan without running
* ``--force``: Re-run completed tasks

**Examples:**

.. code-block:: bash

    # Run specific task
    warifuri run my-task

    # Run all ready tasks
    warifuri run --ready

warifuri show
~~~~~~~~~~~~~

Display detailed task information and metadata.

**Syntax:**

.. code-block:: bash

    warifuri show <task-name>

**Examples:**

.. code-block:: bash

    # Show task details
    warifuri show data-processing

Validation Commands
-------------------

warifuri validate
~~~~~~~~~~~~~~~~~

Validate project configuration and check for issues.

**Syntax:**

.. code-block:: bash

    warifuri validate [--strict]

**Options:**

* ``--strict``: Enable strict validation mode

**Examples:**

.. code-block:: bash

    # Basic validation
    warifuri validate

    # Strict validation
    warifuri validate --strict

Visualization Commands
----------------------

warifuri graph
~~~~~~~~~~~~~~

Generate dependency graphs in various formats.

**Syntax:**

.. code-block:: bash

    warifuri graph [--format <type>] [--output <file>]

**Options:**

* ``--format <type>``: Output format (mermaid, html, ascii)
* ``--output <file>``: Save to file instead of display

**Examples:**

.. code-block:: bash

    # Generate Mermaid graph
    warifuri graph --format mermaid

    # Save HTML graph to file
    warifuri graph --format html --output deps.html

Workflow Commands
-----------------

warifuri mark-done
~~~~~~~~~~~~~~~~~~

Mark a task as completed by creating done.md file.

**Syntax:**

.. code-block:: bash

    warifuri mark-done <task-name>

**Examples:**

.. code-block:: bash

    # Mark task as done
    warifuri mark-done setup-database

Template Commands
-----------------

warifuri template list
~~~~~~~~~~~~~~~~~~~~~~

List available templates and their contained tasks.

**Syntax:**

.. code-block:: bash

    warifuri template list

GitHub Integration
------------------

warifuri issue
~~~~~~~~~~~~~~

Create and manage GitHub issues.

**Syntax:**

.. code-block:: bash

    warifuri issue create <task-name> [--repo <repo>]

**Options:**

* ``--repo <name>``: Target repository
* ``--title <text>``: Custom issue title
* ``--labels <list>``: Issue labels

**Examples:**

.. code-block:: bash

    # Create issue for task
    warifuri issue create my-task --repo myorg/myrepo

Global Options
--------------

These options are available for all commands:

* ``--workspace <path>``: Specify workspace directory
* ``--log-level <level>``: Set logging level (debug, info, warning, error)
* ``--version``: Show version information
* ``--help``: Show help information
