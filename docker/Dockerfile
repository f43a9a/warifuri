FROM python:3.11.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    make \
    jq \
    pandoc \
    # mmdc (mermaid-cli) requires Node.js, install Node.js first
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and mmdc (mermaid-cli)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g @mermaid-js/mermaid-cli

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set PATH for Poetry
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /workspace

# Copy application files
COPY . /workspace

# Install Python dependencies
# First copy only the files needed for dependency installation to leverage Docker cache
COPY pyproject.toml /workspace/
# Generate a new poetry.lock and then install the dependencies
RUN poetry config virtualenvs.create false && poetry lock && poetry install --no-root --without dev

# Copy the rest of the application code
COPY . /workspace

# Install dev dependencies if needed, or handle this in setup.sh
# RUN poetry install --no-root

# Expose any necessary ports
# EXPOSE 8000

# Default command
# CMD ["bash"]
