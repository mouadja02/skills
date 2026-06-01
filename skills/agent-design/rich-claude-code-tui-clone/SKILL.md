---
name: rich-claude-code-tui-clone
description: >
  Use when building a Python terminal UI inspired by Claude Code with Rich. Translates a detailed
  TypeScript/Ink-style visual reference into a staged Python architecture for logo, message stream,
  streaming Markdown, tools, diffs, prompt, footer, spinners, permissions, transcript mode, themes,
  accessibility, and tests. Separates Rich rendering from the input and widget responsibilities that
  require an application-owned event loop or an optional Textual layer.
source: "https://rich.readthedocs.io/en/stable/; https://github.com/Textualize/rich; https://github.com/Textualize/textual; https://github.com/batrachianai/toad"
attribution: "Derived from official Rich documentation and repository examples, official Textual materials, the Toad repository as an architecture reference, and a user-supplied Claude Code TUI visual report"
---

# Rich Claude Code TUI Clone

Build a Python terminal interface that recreates the interaction grammar of a modern coding agent:
conversation-first layout, streaming responses, compact tool summaries, permission gates, rich diffs,
transcript navigation, and restrained motion.

Do not treat Rich as a drop-in replacement for Ink. Rich is the rendering layer. Input editing,
keyboard dispatch, viewport state, search, and modal ownership must be implemented by the application
or delegated to an optional widget framework.

## When to Activate

Activate when:
- Rebuilding a Claude Code-like terminal experience in Python
- Converting a TypeScript/Ink TUI design into Rich renderables
- Adding full-screen mode, transcript export, tool panels, diffs, or themes to a Python agent CLI
- Deciding whether a Rich-only CLI is sufficient or a Textual application is justified
- Reviewing a Python coding-agent TUI for rendering, input, accessibility, or test gaps

For a generic TypeScript/OpenRouter scaffold, use `create-agent-tui` instead. This skill is specifically
for the Python/Rich implementation path.

## Source Boundary

Use:
- Official Rich documentation and repository examples for API behavior
- Official Textual materials for the optional widget-framework upgrade path
- Toad only as a high-level architecture reference for a current Rich/Textual agentic TUI
- The user-supplied visual report as a design target

Do not copy proprietary product code, trademarks, or mascot art. Recreate interaction patterns and
visual hierarchy. Use project-owned names and artwork unless the user has rights to branded assets.
Toad is AGPL-licensed: study its architecture, but do not copy implementation code into an
incompatibly licensed project.

## First Decision: Choose the Fidelity Level

| Level | Use when | Core approach |
| --- | --- | --- |
| `scrollback` | Fast CLI MVP, terminal history matters most | `Console.print()` for completed blocks and a transient `Live` spinner |
| `rich-screen` | Full-screen conversation UI with controlled regions | `Layout` + `Live(screen=True)` + application-owned state and input loop |
| `textual-app` | Claude Code-level prompt editor, mouse events, modal overlays, fuzzy pickers, or virtualized widgets | Textual application with Rich renderables inside widgets |

Start at the lowest level that meets the acceptance criteria. A full Claude Code visual clone normally
ends at `textual-app`; a convincing first milestone can remain `rich-screen`.

Read [references/rich-api-map.md](references/rich-api-map.md) before selecting a level.

## Non-Negotiable Architecture

Use one-way state flow:

```text
agent events + terminal input + timers
              |
              v
         reduce(state, event)
              |
              v
         immutable AppState
              |
              v
         render_app(state)
              |
              v
        Rich renderable tree
```

Keep transport, state transitions, and rendering separate. Never let an agent callback write directly
to stdout while a `Live` display owns the terminal.

Recommended project shape:

```text
src/
  app.py
  state.py
  theme.py
  runtime/
    agent_events.py
    input.py
    terminal.py
    transcript.py
  renderables/
    logo.py
    messages.py
    tools.py
    diff.py
    prompt.py
    footer.py
    dialogs.py
tests/
  test_render_snapshots.py
  test_reducer.py
  test_transcript.py
```

For the component map and state model, read
[references/claude-code-parity-roadmap.md](references/claude-code-parity-roadmap.md).

## Build Workflow

### Step 1: Write a Parity Contract

Record the requested fidelity before coding:

```markdown
## TUI Parity Contract
- Fidelity level: scrollback | rich-screen | textual-app
- Required modes: prompt | transcript | fullscreen
- Required message types:
- Required tool renderers:
- Prompt features: multiline | history | slash completion | vim | paste
- Permission flows:
- Diff requirements: unified | split | word-level
- Theme targets: dark | light | daltonized | ANSI
- Motion policy: standard | reduced
- Terminal targets: Linux | macOS | Windows Terminal | WSL
- Brand assets authorized: yes | no
```

### Step 2: Scaffold the Rendering Layer

Use a custom `Theme`, then implement renderables in this order:

1. Logo header and status notices
2. User, assistant, thinking, and tool message blocks
3. Spinner row with verb, elapsed time, and state color
4. Prompt shell and footer
5. Permission dialog
6. Structured diff
7. Transcript layout and export

Use `Text`, `Panel`, `Group`, `Table.grid`, `Rule`, `Markdown`, and `Syntax` before creating custom
renderables. Implement `__rich_console__` only when composition is no longer enough.

### Step 3: Add the Runtime Loop

For `rich-screen`, keep one `Live` owner:

```python
with Live(
    render_app(state),
    console=console,
    screen=True,
    refresh_per_second=20,
    vertical_overflow="crop",
) as live:
    while state.running:
        event = await event_queue.get()
        state = reduce(state, event)
        live.update(render_app(state))
```

Use `auto_refresh=False` and `live.update(..., refresh=True)` when deterministic repaint timing matters.
Use a transient non-screen `Live` display for the scrollback MVP.

### Step 4: Implement Streaming Deliberately

Do not re-render the entire transcript for every token:

1. Freeze completed message blocks.
2. Cache renderables by message id, width, theme, and content version.
3. Rebuild only the active streaming suffix.
4. Parse Markdown at stable block boundaries when possible.
5. Throttle repaints independently from token arrival.

Rich `Markdown` is sufficient for complete blocks. A production streaming renderer may need a stable
prefix plus an active suffix, especially for open code fences and long responses.

### Step 5: Treat Input as a Separate Subsystem

Rich does not provide a multiline prompt editor, fuzzy completion, Vim mode, cursor editing, mouse
selection, or modal focus management.

Choose one:
- Basic MVP: `asyncio` plus a small raw-terminal input adapter
- Intermediate: a dedicated prompt library for multiline editing and history
- Full parity: Textual widgets, bindings, screens, and reactive state

Do not fake widget behavior with scattered ANSI writes inside render functions.

### Step 6: Add Transcript and Fullscreen Behavior

For transcript export, use a recording console:

```python
recording = Console(record=True, width=width)
recording.print(render_transcript(state))
plain_text = recording.export_text(clear=True, styles=False)
```

For alternate-screen rendering, use `Live(screen=True)` or `Console.screen()`. Keep transcript search,
viewport slicing, sticky prompts, and unseen-message counters in application state.

### Step 7: Verify at Multiple Widths and Capabilities

Snapshot renderables at `60`, `100`, and `140` columns. Test:
- Dark, light, daltonized, ANSI, and no-color modes
- Reduced-motion mode
- Long paths, wide characters, wrapped code, and partial Markdown fences
- Permission allow, deny, and cancel paths
- Streaming updates, resize events, transcript export, and search
- Windows Terminal or WSL behavior if Windows is a target

Read [references/input-fullscreen-testing.md](references/input-fullscreen-testing.md) for the detailed
test matrix.

## Definition of Done

A finished implementation:
- Has a declared fidelity level and terminal support matrix
- Keeps agent events separate from terminal writes
- Has one owner for each live terminal region
- Renders complete and streaming messages without transcript-wide repaint churn
- Uses explicit fallbacks for Unicode, color, and reduced motion
- Keeps dangerous tool approvals keyboard-operable and auditable
- Exports a plain-text transcript
- Has snapshot tests at narrow and wide widths
- Documents which Claude Code-like features are implemented, deferred, or delegated to Textual

## Gotchas

1. **Rich is not Ink.** It renders terminal content; it does not provide a React component lifecycle or
   a full input widget system.
2. **Alternate screen changes scrollback expectations.** Use normal printing for shell-like history and
   `screen=True` only when the application should own the viewport.
3. **Concurrent writes corrupt live displays.** Route logs, subprocess output, and agent deltas through
   events.
4. **Virtualization is application behavior.** Rich `Layout` does not virtualize a long transcript.
5. **Streaming Markdown is incremental parsing work.** Cache completed blocks and isolate the unstable
   suffix.
6. **Unicode width varies by terminal.** Test mascot art, box borders, braille spinners, and wide glyphs;
   ship ASCII fallbacks.
7. **Color is not the only signal.** Pair colors with labels, prefixes, or icons.
8. **Reference implementations have licenses.** Learn from Toad's structure; do not paste AGPL code into
   a project with incompatible distribution terms.

## References

- [Rich API map](references/rich-api-map.md)
- [Claude Code parity roadmap](references/claude-code-parity-roadmap.md)
- [Input, fullscreen, and testing](references/input-fullscreen-testing.md)
- [Research ledger](references/research-ledger.md)

---

## Skill Metadata

**Created**: 2026-06-02
**Version**: 1.0.0
