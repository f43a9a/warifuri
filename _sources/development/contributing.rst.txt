Contributing
============

We welcome contributions to warifuri! This guide will help you get started.

Development Setup
-----------------

1. **Fork and Clone**

.. code-block:: bash

    git clone https://github.com/yourusername/warifuri.git
    cd warifuri

2. **Install Dependencies**

.. code-block:: bash

    poetry install
    poetry shell

3. **Install Pre-commit Hooks**

.. code-block:: bash

    pre-commit install

Running Tests
-------------

Run the full test suite:

.. code-block:: bash

    pytest

Run with coverage:

.. code-block:: bash

    pytest --cov=warifuri --cov-report=html

Code Quality
------------

We use several tools to maintain code quality:

* **Black**: Code formatting
* **Ruff**: Linting
* **MyPy**: Type checking
* **Pre-commit**: Git hooks

Run quality checks:

.. code-block:: bash

    # Format code
    black src/ tests/

    # Lint code
    ruff check src/ tests/

    # Type checking
    mypy src/

Submitting Changes
------------------

1. **Create a Branch**

.. code-block:: bash

    git checkout -b feature/my-new-feature

2. **Make Changes**

   * Write tests for new functionality
   * Ensure all tests pass
   * Follow coding standards
   * Update documentation

3. **Submit Pull Request**

   * Use clear, descriptive commit messages
   * Reference related issues
   * Include tests for new features
   * Update documentation as needed

Coding Standards
----------------

* **Follow PEP 8** for Python code style
* **Write type hints** for all functions
* **Document public APIs** with docstrings
* **Keep functions small** and focused
* **Write tests** for new functionality

Project Structure
-----------------

.. code-block::

    warifuri/
    ├── src/warifuri/          # Main source code
    │   ├── cli/              # CLI commands
    │   ├── core/             # Core functionality
    │   ├── utils/            # Utility functions
    │   └── schemas/          # Data schemas
    ├── tests/                # Test files
    ├── docs/                 # Documentation
    └── templates/            # Built-in templates

Reporting Issues
----------------

When reporting bugs, please include:

* **warifuri version**: ``warifuri --version``
* **Python version**: ``python --version``
* **Operating system**
* **Detailed steps to reproduce**
* **Expected vs actual behavior**
* **Error messages** (if any)

Feature Requests
----------------

For feature requests, please describe:

* **Use case**: What problem does this solve?
* **Proposed solution**: How should it work?
* **Alternatives considered**: Other approaches you've thought of
* **Additional context**: Examples, mockups, etc.
