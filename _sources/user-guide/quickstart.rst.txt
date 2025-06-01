Quick Start Guide
=================

This guide will help you get started with warifuri in 5 minutes.

1. Create Your First Project
-----------------------------

Initialize a new warifuri project:

.. code-block:: bash

    mkdir my-project
    cd my-project
    warifuri init project my-project

This creates a ``.warifuri/`` directory with project configuration.

2. Add Your First Task
-----------------------

Create a simple task:

.. code-block:: bash

    warifuri init task hello-world

Edit the generated task file to add your commands:

.. code-block:: yaml

    name: hello-world
    description: My first warifuri task
    type: shell
    commands:
      - echo "Hello, warifuri!"

3. List All Tasks
------------------

View all tasks in your project:

.. code-block:: bash

    warifuri list

4. Run Your Task
-----------------

Execute the task:

.. code-block:: bash

    warifuri run hello-world

5. Create Dependencies
-----------------------

Create a task that depends on another:

.. code-block:: bash

    warifuri init task goodbye-world

Edit the task to include dependencies:

.. code-block:: yaml

    name: goodbye-world
    description: Task with dependency
    type: shell
    dependencies:
      - hello-world
    commands:
      - echo "Goodbye, warifuri!"

When you run ``goodbye-world``, warifuri will automatically run ``hello-world`` first.

6. Visualize Dependencies
-------------------------

Generate a dependency graph:

.. code-block:: bash

    warifuri graph --format mermaid

What's Next?
------------

* Learn about all available :doc:`commands`
* Explore :doc:`configuration` options
* Create reusable :doc:`templates`
* Set up GitHub integration
