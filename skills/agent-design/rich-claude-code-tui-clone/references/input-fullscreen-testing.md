# Input, Fullscreen, and Testing

The difficult part of a Claude Code-like TUI is not drawing panels. It is keeping terminal ownership,
input editing, transcript state, and repaint behavior coherent under streaming updates.

## Terminal Ownership Rules

1. Create one `Console`.
2. Create at most one top-level `Live` display for the active mode.
3. Route agent deltas, logs, subprocess output, timers, and input through an event queue.
4. Render from state.
5. Shut down `Live` before handing terminal control to an external interactive program.

For shell-like scrollback, print completed messages normally and use only a transient status row. For a
full-screen interface, use `Live(screen=True)` and keep all visible regions inside its render tree.

## Input Options

### Basic Input

Use a plain prompt when:
- Single-line input is sufficient
- Terminal-native history is acceptable
- The agent interaction loop matters more than editor behavior

### Raw-Terminal Adapter

Use an application-owned raw-terminal adapter when:
- You need a bordered prompt while staying Rich-only
- Required bindings are small and explicit
- Cross-platform input behavior is tested

The adapter owns:
- Key decoding
- Cursor position
- Buffer edits
- Paste boundaries
- History index
- Resize events
- Cancellation

Keep this adapter separate from renderables.

### Textual Upgrade

Use Textual when requirements include several of:
- Multiline editing
- Mouse support
- Modal focus isolation
- Fuzzy completion
- File picker
- Text selection and clipboard
- Multiple panes
- Persistent interactive shell
- Widget-level testing

Do not spend weeks rebuilding a general widget toolkit inside a Rich-only loop.

## Fullscreen Modes

### Prompt Mode

Recommended layout:

```text
header
messages viewport
optional overlay
prompt
footer
```

Behavior:
- Follow the tail while the user is at the bottom.
- Increment an unseen counter if messages arrive while scrolled up.
- Show a sticky representation of the latest user prompt when useful.
- Pause follow-tail briefly after manual navigation.

### Transcript Mode

Recommended behavior:
- Enter alternate-screen transcript view.
- Slice visible cached message blocks by viewport.
- Expand collapsed reads, searches, and thinking blocks.
- Support `/` search plus next and previous navigation.
- Support transcript export to plain text.
- Clear or rebuild search offsets after resize.

Rich provides the rendering and alternate screen. The application provides search positions,
viewport offsets, expanded state, and navigation.

## Transcript Export

Render transcript content to a separate recording console:

```python
from io import StringIO
from rich.console import Console

def export_transcript(renderable, width: int = 100) -> str:
    output = StringIO()
    console = Console(
        file=output,
        width=width,
        record=True,
        color_system=None,
        force_terminal=False,
    )
    console.print(renderable)
    return console.export_text(clear=True, styles=False)
```

Export should remain useful without ANSI styles.

## Accessibility

### Color

- Use semantic theme keys.
- Provide dark, light, daltonized, and ANSI variants.
- Respect no-color operation.
- Pair every important color with text, icon, prefix, or border meaning.

### Motion

Add `prefers_reduced_motion`:
- Freeze spinner animation to one frame.
- Disable shimmer interpolation.
- Disable cursor blink.
- Keep status text updated.

### Character Width

Test:
- ASCII-only terminal fallback
- Box-drawing glyphs
- Braille spinner frames
- Double-width characters
- Combining marks
- Narrow terminal wrapping

### Keyboard

Every action must have a text-visible keyboard path:
- Submit
- Cancel
- Allow once
- Allow always
- Deny
- Transcript toggle
- Search
- Exit transcript

## Snapshot Testing

Use fixed-width consoles:

```python
from io import StringIO
from rich.console import Console

def render_plain(renderable, width: int) -> str:
    output = StringIO()
    console = Console(
        file=output,
        width=width,
        color_system=None,
        force_terminal=False,
    )
    console.print(renderable)
    return output.getvalue()
```

Snapshot at:
- `60` columns: narrow fallback
- `100` columns: normal development terminal
- `140` columns: wide terminal

Snapshot states:
- Empty session logo
- User message
- Streaming assistant suffix
- Completed Markdown with table and code fence
- Active tool, completed tool, failed tool
- Collapsed read/search summary
- Permission dialog
- Unified diff with word-level change
- Transcript search match
- Reduced-motion spinner
- ANSI/no-color theme

## Reducer Testing

Test state transitions independently:

```text
user submitted -> prompt clears -> user message appended
agent thinking -> activity thinking
first token -> activity streaming
tool started -> activity tool
tool completed -> result appended
permission requested -> overlay visible
permission answered -> audit record appended -> overlay cleared
scroll up -> follow_tail false
new message while scrolled up -> unseen_count increments
resize -> render cache invalidated -> search offsets rebuilt
```

## Performance Checks

Measure:
- Repaints per second during fast token streaming
- Time to render a transcript with 100, 1,000, and 10,000 blocks
- Cache hit rate for completed messages
- Resize latency
- Search index build time
- Memory growth over a long session

Do not reparse complete Markdown blocks after every token. Do not render all transcript blocks when only
a viewport slice is visible.

## Cross-Platform Matrix

| Target | Check |
| --- | --- |
| Linux terminal | Color, resize, raw mode, paste, signals |
| macOS terminal | Unicode widths, fallback art, alternate screen |
| Windows Terminal | VT support, color capability, resize, key decoding |
| WSL | Clipboard assumptions and path presentation |
| Redirected output | Disable interactive rendering and emit plain logs |

## Failure Modes

1. Agent callbacks print directly during `Live`: screen corruption.
2. Alternate-screen mode enabled for every interaction: lost shell-like scrollback expectations.
3. Rendering logic contains input edits: difficult tests and focus bugs.
4. Search offsets survive resize: highlights point at wrong cells.
5. Unicode art has no fallback: broken alignment on older terminals.
6. Color carries the only meaning: inaccessible status and diff states.
7. External shell program runs while the app owns raw input: terminal corruption.
