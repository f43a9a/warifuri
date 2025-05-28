warifuri documentation
======================

**warifuri** is a powerful CLI tool for task-driven workflow automation with dependency resolution, GitHub integration, and multi-format output support.

Features
--------

* 📋 **Task Management**: Define and organize tasks with dependencies
* 🔄 **Workflow Automation**: Execute tasks with intelligent dependency resolution
* 🔗 **GitHub Integration**: Create issues, manage PRs, and sync with GitHub
* 📊 **Multi-format Output**: Support for YAML, JSON, and visual graphs
* 🎯 **Template System**: Reusable project and task templates
* ⚡ **CLI Interface**: Fast and intuitive command-line interface

Quick Start
-----------

Install warifuri:

.. code-block:: bash

    pip install warifuri

Initialize a new project:

.. code-block:: bash

    warifuri init project my-project

Add a task:

.. code-block:: bash

    warifuri init task my-task

List all tasks:

.. code-block:: bash

    warifuri list

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   user-guide/installation
   user-guide/quickstart
   user-guide/commands
   user-guide/configuration
   user-guide/templates

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   api/modules

.. toctree::
   :maxdepth: 1
   :caption: Development:

   development/contributing
   development/changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
