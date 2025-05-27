#!/bin/bash
echo "=== Setup Environment Task ==="
echo "Current directory: $(pwd)"
echo "Task: ${WARIFURI_TASK_NAME:-N/A}"
echo "Project: ${WARIFURI_PROJECT_NAME:-N/A}"
echo "Workspace: ${WARIFURI_WORKSPACE_DIR:-N/A}"
echo "Environment setup completed successfully!"
echo "$(date): Task completed" > setup.log
ls -la
