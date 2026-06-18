# Research Ledger

Research captured on 2026-06-02 for this skill.

## Official Rich Documentation

| Source | Used for |
| --- | --- |
| [Rich documentation](https://rich.readthedocs.io/en/stable/) | Package overview and documentation entry point |
| [Live displays](https://rich.readthedocs.io/en/stable/live.html) | Auto-updating displays, alternate screen, refresh control, transient displays, overflow behavior |
| [Layouts](https://rich.readthedocs.io/en/stable/layout.html) | Named regions, row and column splits, updates |
| [Console API](https://rich.readthedocs.io/en/stable/reference/console.html) | `Console.screen`, terminal output ownership, recording and export |
| [Themes](https://rich.readthedocs.io/en/stable/themes.html) | Named semantic styles |
| [Styles](https://rich.readthedocs.io/en/stable/style.html) | Foreground, background, and text attributes |
| [Panels](https://rich.readthedocs.io/en/stable/panel.html) | Dialog and tool block framing |
| [Syntax highlighting](https://rich.readthedocs.io/en/stable/syntax.html) | Highlighted code blocks |
| [Console Protocol](https://rich.readthedocs.io/en/stable/protocol.html) | Custom renderables through `__rich_console__` and optional measurement |

## Official Rich Repository

Repository: [Textualize/rich](https://github.com/Textualize/rich)

Inspected:
- `examples/layout.py`
- `examples/fullscreen.py`
- `examples/screen.py`
- `examples/live_progress.py`
- `rich/live.py`
- `rich/console.py`
- `rich/layout.py`
- `rich/markdown.py`
- `rich/syntax.py`
- `rich/theme.py`
- `rich/spinner.py`
- `rich/panel.py`
- `pyproject.toml`

Findings:
- `Live` supports `screen`, `auto_refresh`, `refresh_per_second`, `transient`, and
  `vertical_overflow`.
- `Console.screen()` enters an alternate-screen context.
- `Console(record=True)` is required for `export_text()` and other exports.
- `Layout` composes named regions and updates them independently.
- Rich supplies renderables and a console protocol, not a widget-level application framework.
- The inspected repository metadata declared Rich `15.0.0`; pin and test a project version instead of
  assuming an unbounded latest dependency.

## Official Textual Materials

Repository: [Textualize/textual](https://github.com/Textualize/textual)

The official README describes Textual as a Python application framework with widgets, layouts, themes,
async integration, testing support, and a fuzzy command palette. It is the optional upgrade path when
the TUI needs widget-grade interaction instead of a small app-owned input adapter.

## Agentic TUI Architecture Reference

Repository: [batrachianai/toad](https://github.com/batrachianai/toad)

Rich's own README links Toad as an agentic coding interface built with Rich and Textual. Inspected:
- `README.md`
- `pyproject.toml`
- `src/toad/app.py`
- `src/toad/conversation_markdown.py`
- `src/toad/widgets/prompt.py`
- `src/toad/widgets/conversation.py`
- `src/toad/widgets/question.py`
- `src/toad/widgets/diff_view.py`

Architecture observations:
- The async application owns screens and bindings.
- Prompt editing is a widget concern.
- Permission questions are interactive widget state.
- Streaming Markdown and diffs justify focused components.
- Shell integration is a separate subsystem, not a decorated subprocess print.

Licensing note: Toad is AGPL-licensed. These observations are for architecture orientation only. Check
license compatibility before reusing any implementation.

## User-Supplied Visual Reference

The user supplied a detailed visual decomposition of the Claude Code terminal UI covering:
- Layout zones and screen modes
- Mascot and logo system
- Theme palette and typography
- Message grouping and virtualization
- Prompt editor, footer, spinner, and permission dialogs
- Markdown, code highlighting, and structured diffs
- Transcript mode, alternate screen, overlays, agents, motion, and accessibility

This skill converts that visual target into a Python implementation roadmap. It does not claim access
to or reuse of proprietary source code.
