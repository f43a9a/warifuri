Configuration
=============

warifuri uses YAML configuration files for project and task definitions.

Project Configuration
---------------------

The main project configuration is stored in ``.warifuri/project.yaml``:

.. code-block:: yaml

    name: my-project
    description: A sample warifuri project
    version: 1.0.0
    templates:
      - data-pipeline
      - web-scraping

Task Configuration
------------------

Individual tasks are defined in ``.warifuri/tasks/`` directory:

.. code-block:: yaml

    name: data-processing
    description: Process raw data files
    type: shell
    dependencies:
      - data-download
    commands:
      - python scripts/process.py
      - echo "Processing complete"

Task Types
----------

**shell**
    Execute shell commands

**ai**
    Use AI assistance for task execution

**human**
    Require human intervention

**machine**
    Automated system tasks

Environment Variables
---------------------

Configure warifuri behavior with environment variables:

* ``WARIFURI_WORKSPACE``: Default workspace directory
* ``GITHUB_TOKEN``: GitHub API token for integration features
* ``WARIFURI_LOG_LEVEL``: Logging level (debug, info, warning, error)

Configuration Files
-------------------

**Global Config**: ``~/.warifuri/config.yaml``

.. code-block:: yaml

    github:
      token: your-github-token
      default_repo: myorg/myrepo
    defaults:
      log_level: info
      format: plain

**Project Config**: ``.warifuri/project.yaml``

.. code-block:: yaml

    name: my-project
    description: Project description
    version: 1.0.0
