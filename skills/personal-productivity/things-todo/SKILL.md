---
name: things-todo
description: "Things 3 via things CLI: add, list, search, update, delete, verify tasks."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
version: "1.0.0"
platform: macos
---

# Things Todo

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use this for Things 3 tasks on macOS. Prefer `things` for Things-backed todos; use `reminders` only when the user asks for Apple Reminders.

## Tool

- CLI: `things`
- Repo: https://github.com/ossianhempel/things3-cli

## Install

```bash
pip install things3
# or
brew install things3-cli
```

## Common Commands

```bash
# List today's tasks
things today

# List all tasks
things list

# List inbox
things inbox

# List by area
things areas
things list --area "Work"

# Search
things search "search term"

# Add task
things add "Task title"
things add "Task title" --notes "Notes here" --area "Work" --deadline "2025-12-31"

# Complete task
things complete <task-id>

# Show task details
things show <task-id>
```

## Notes

- Things 3 must be installed and running on macOS for CLI to work.
- The CLI communicates with Things 3 via URL scheme or AppleScript.
- Task IDs are UUID format.
- Deadlines use ISO date format: `YYYY-MM-DD`.
