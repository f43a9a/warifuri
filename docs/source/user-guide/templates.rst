Templates
=========

warifuri templates provide reusable project and task structures for common workflows.

Using Templates
---------------

List available templates:

.. code-block:: bash

    warifuri template list

Deploy a template:

.. code-block:: bash

    warifuri init --template data-pipeline

Built-in Templates
------------------

**data-pipeline**
    Complete data processing pipeline with extraction, transformation, and loading tasks.

**web-scraping**
    Web scraping project with data collection and processing tasks.

**ml-training**
    Machine learning workflow with data preparation, training, and evaluation.

Creating Custom Templates
--------------------------

Templates are stored in the ``templates/`` directory with this structure:

.. code-block::

    templates/
    └── my-template/
        ├── project.yaml
        ├── tasks/
        │   ├── task1.yaml
        │   └── task2.yaml
        └── files/
            └── script.py

**Template project.yaml:**

.. code-block:: yaml

    name: "{{project_name}}"
    description: "{{project_description}}"
    version: 1.0.0

**Template task file:**

.. code-block:: yaml

    name: "{{task_name}}"
    description: "{{task_description}}"
    type: shell
    commands:
      - echo "Hello from template!"

Template Variables
------------------

Use Jinja2 template variables in your templates:

* ``{{project_name}}``: Project name
* ``{{project_description}}``: Project description
* ``{{task_name}}``: Task name
* ``{{task_description}}``: Task description
* ``{{author}}``: Author name
* ``{{date}}``: Current date

Sharing Templates
-----------------

Templates can be shared as:

* Git repositories
* ZIP archives
* Directory structures

To use external templates:

.. code-block:: bash

    # From Git repository
    warifuri init --template https://github.com/user/template-repo

    # From local directory
    warifuri init --template /path/to/template
