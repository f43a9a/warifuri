#!/bin/bash

# Exit on error
set -e

# Install Poetry if not present
if ! command -v poetry &> /dev/null
then
    echo "Poetry not found. Installing..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Disable in-project virtualenvs
poetry config virtualenvs.create false

# Install all dependencies (including dev)
echo "Installing dependencies..."
poetry install

# Run type checker and linter
echo "Running mypy..."
poetry run mypy .

echo "Running ruff (static analysis)..."
poetry run ruff check .

echo "Running pytest..."
poetry run pytest

echo "Setup complete."
