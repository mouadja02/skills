---
name: reminders
description: "Apple Reminders via rem CLI: add, list, search, update, complete, delete."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# Reminders

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use this for Apple Reminders tasks. Prefer `rem` over Things/AppleScript when
the user wants an AI-friendly personal todo backend on macOS.

## Tool

- CLI: `rem`
- Repo: https://github.com/BRO3886/rem

## Install

```bash
brew install BRO3886/tap/rem
```

## Common Commands

```bash
# List all reminders
rem list

# List by list name
rem list "Work"

# Add reminder
rem add "Task title"
rem add "Task title" --list "Work"
rem add "Task title" --due "2025-12-31"
rem add "Task title" --note "Notes here"

# Search
rem search "search term"

# Complete
rem complete <reminder-id>

# Delete
rem delete <reminder-id>

# Show lists
rem lists
```

## Notes

- Requires macOS with Apple Reminders app.
- `rem` communicates with Reminders via EventKit.
- Due dates use ISO format: `YYYY-MM-DD` or `YYYY-MM-DD HH:MM`.
- Reminder IDs are unique identifiers from EventKit.
