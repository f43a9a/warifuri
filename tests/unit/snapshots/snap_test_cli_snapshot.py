# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestCliSnapshotOutput::test_automation_help_snapshot automation_help_output'] = '''Usage: python -m warifuri automation [OPTIONS] COMMAND [ARGS]...

  Automation and GitHub Actions integration commands.

Options:
  --help  Show this message and exit.

Commands:
  check      Check if a task can be automated.
  create-pr  Create a pull request for automated task execution.
  list       List tasks suitable for automation.
  merge-pr   Merge a pull request immediately.
'''

snapshots['TestCliSnapshotOutput::test_error_output_snapshot show_nonexistent_error'] = '''Error: Task 'nonexistent/task' not found.
'''

snapshots['TestCliSnapshotOutput::test_graph_command_help_snapshot graph_help_output'] = '''Usage: python -m warifuri graph [OPTIONS]

  Generate dependency graph visualization.

Options:
  --project TEXT                 Filter by project name
  --format [mermaid|ascii|html]  Output format
  --web                          Open in web browser (HTML format only)
  --help                         Show this message and exit.
'''

snapshots['TestCliSnapshotOutput::test_help_output_snapshot help_output'] = '''Usage: python -m warifuri [OPTIONS] COMMAND [ARGS]...

  warifuri - A minimal CLI for task allocation.

Options:
  --log-level [DEBUG|INFO|WARNING|ERROR|CRITICAL]
                                  Set logging level
  --workspace DIRECTORY           Workspace directory path
  --version                       Show the version and exit.
  --help                          Show this message and exit.

Commands:
  automation  Automation and GitHub Actions integration commands.
  graph       Generate dependency graph visualization.
  init        Initialize project or task.
  issue       Create GitHub issues for projects and tasks.
  list        List tasks in workspace.
  mark-done   Mark task as completed by creating done.md file.
  run         Run task(s).
  show        Show task definition and metadata.
  template    Manage templates.
  validate    Validate workspace configuration and dependencies.
'''

snapshots['TestCliSnapshotOutput::test_init_help_snapshot init_help_output'] = '''Usage: python -m warifuri init [OPTIONS] [TARGET]

  Initialize project or task.

  TARGET can be: - project_name: Create new project -
  project_name/task_name: Create new task - Empty with --template:
  Expand template to current workspace

Options:
  --template TEXT    Template to use for initialization
  --force            Overwrite existing files
  --dry-run          Show what would be created without creating
  --non-interactive  Use default values without prompting
  --help             Show this message and exit.
'''

snapshots['TestCliSnapshotOutput::test_issue_help_snapshot issue_help_output'] = '''Usage: python -m warifuri issue [OPTIONS]

  Create GitHub issues for projects and tasks.

Options:
  --project TEXT    Create parent issue for project
  --task TEXT       Create child issue for specific task (project/task)
  --all-tasks TEXT  Create child issues for all tasks in project
  --assignee TEXT   Assign issue to user
  --label TEXT      Comma-separated labels to apply
  --dry-run         Show what would be created without creating
  --help            Show this message and exit.
'''

snapshots['TestCliSnapshotOutput::test_list_command_json_output_snapshot list_json_output'] = '''[]
'''

snapshots['TestCliSnapshotOutput::test_list_command_output_snapshot list_default_output'] = '''No tasks found.
'''

snapshots['TestCliSnapshotOutput::test_list_command_ready_filter_snapshot list_ready_output'] = '''No tasks found.
'''

snapshots['TestCliSnapshotOutput::test_mark_done_help_snapshot mark_done_help_output'] = '''Usage: python -m warifuri mark-done [OPTIONS] TASK_NAME

  Mark task as completed by creating done.md file.

  TASK_NAME should be in format "project/task".

Options:
  --message TEXT  Custom message for done.md
  --help          Show this message and exit.
'''

snapshots['TestCliSnapshotOutput::test_run_dry_run_snapshot run_dry_run_output'] = ''

snapshots['TestCliSnapshotOutput::test_show_command_output_snapshot show_task_output'] = ''

snapshots['TestCliSnapshotOutput::test_template_help_snapshot template_help_output'] = '''Usage: python -m warifuri template [OPTIONS] COMMAND [ARGS]...

  Manage templates.

Options:
  --help  Show this message and exit.

Commands:
  list  List available templates.
'''

snapshots['TestCliSnapshotOutput::test_validate_command_output_snapshot validate_output'] = '''Validating workspace...
✅ Schema loaded successfully
✅ No circular dependencies found

Validation Summary:
  Tasks validated: 0
  Errors: 0
  Warnings: 1

Warnings:
  - No projects found in workspace

✅ Validation passed
'''

snapshots['TestCliSnapshotOutput::test_version_output_snapshot version_output'] = '''warifuri, version X.X.X
'''
