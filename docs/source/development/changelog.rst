Changelog
=========

All notable changes to warifuri will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

[Unreleased]
------------

Added
~~~~~
* Initial public release
* Complete CLI interface with 9 core commands
* Task dependency resolution system
* GitHub integration for issue management
* Multi-format output support (YAML, JSON, TSV)
* Template system for reusable workflows
* Comprehensive documentation with Sphinx
* CI/CD pipeline with GitHub Actions

Changed
~~~~~~~
* Project structure moved to src/ layout
* Improved error handling and validation
* Enhanced test coverage (85%+)

[0.1.0] - 2025-05-28
--------------------

Added
~~~~~
* Core CLI commands: init, list, run, show, validate, graph, mark-done
* Task management with YAML configuration
* Dependency resolution engine
* GitHub API integration
* Template deployment system
* Multi-format graph visualization
* Comprehensive test suite
* Development tooling (pre-commit, type checking)

Technical Details
~~~~~~~~~~~~~~~~~
* Python 3.9+ support
* Poetry for dependency management
* Click for CLI framework
* Pydantic for data validation
* Rich for beautiful terminal output
* PyYAML for configuration parsing

Infrastructure
~~~~~~~~~~~~~~
* GitHub Actions CI/CD
* Pre-commit hooks for code quality
* Automated testing on multiple Python versions
* Code coverage reporting
* Security scanning with CodeQL
