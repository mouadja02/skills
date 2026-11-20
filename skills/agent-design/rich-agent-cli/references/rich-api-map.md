# Rich API Map

Use this map to translate a Claude Code-style visual report into Python without claiming Rich provides
features it does not implement.

## Direct Rich Capabilities

| Design need | Rich API | Notes |
| --- | --- | --- |
| Terminal output owner | `rich.console.Console` | Centralize output, terminal capability detection, recording, and export |
| Full-screen repaint loop | `rich.live.Live(screen=True)` | Uses alternate screen; `refresh_per_second`, `auto_refresh`, `vertical_overflow`, and `transient` control behavior |
| Alternate-screen context | `Console.screen()` | Useful for screen updates outside a `Live` loop |
| Named screen regions | `rich.layout.Layout` | Split rows and columns; update named regions |
| Bordered blocks and dialogs | `rich.panel.Panel` | Titles, padding, border styles, and `Panel.fit()` |
| Renderable grouping | `rich.console.Group` | Stack renderables without manual concatenation |
| Grid-like alignment | `Table.grid()` | Good for headers, footers, metadata, and two-column rows |
| Styled inline content | `rich.text.Text` | Use spans for status colors, search highlights, and word-level diffs |
| Markdown | `rich.markdown.Markdown` | Good for complete assistant messages and static transcript blocks |
| Syntax highlighting | `rich.syntax.Syntax` | Supports lexer, theme, line numbers, wrapping, and highlighted lines |
| Divider | `rich.rule.Rule` | Use for transcript headers, sticky prompts, and unseen-message separators |
| Themes | `rich.theme.Theme` | Define named styles and pass them to `Console(theme=...)` |
| Spinner | `rich.spinner.Spinner` | Use built-in animation or a custom `Text` frame sequence |
| Progress rows | `rich.progress.Progress` | Useful for task lists and multi-agent activity |
| Transcript export | `Console(record=True).export_text()` | Render a transcript to a recording console, then export plain text |
| Custom renderables | Console Protocol | Implement `__rich_console__`; implement `__rich_measure__` only if needed |

## Features Rich Does Not Supply

| Needed behavior | Owner |
| --- | --- |
| Multiline prompt editing and cursor movement | Application input adapter or Textual widget |
| History navigation and fuzzy completion | Application logic or widget framework |
| Vim editing mode | Input subsystem |
| Modal focus and keyboard routing | Application state or Textual screens |
| Mouse hover, click, drag selection, clipboard | Terminal adapter or Textual widgets |
| Transcript virtual scrolling | Application viewport slicing or Textual scroll widgets |
| Sticky prompt tracking | Application viewport state |
| Resize-aware search highlights | Application search index |
| React-style memoization | Application render cache |
| Portal overlays | Application layout slots or Textual screen composition |

## Component Translation

| TypeScript/Ink concept | Rich-first translation |
| --- | --- |
| `ThemedText` | `Text` with named `Theme` styles |
| `ThemedBox`, `Pane`, `Dialog` | `Panel`, `Group`, `Table.grid`, and `Layout` |
| `SpinnerWithVerb` | `Spinner` or custom frame `Text` inside `Live` |
| `Markdown` | `rich.markdown.Markdown` |
| `StructuredDiff` | `Text` lines and spans; optionally `Syntax` for code context |
| `VirtualMessageList` | Cached message blocks plus app-owned visible slice |
| `AlternateScreen` | `Live(screen=True)` or `Console.screen()` |
| `PromptInput` | Separate input subsystem; Textual `TextArea` for full parity |
| Typeahead suggestions | App-owned completer; Textual option list for full parity |
| React memoization | Cache by stable state key and terminal width |

## Starter Theme

Use project-owned semantic names. The values below reproduce the visual grammar in the supplied report
without binding the implementation to a product name.

```python
from rich.console import Console
from rich.theme import Theme

APP_THEME = Theme(
    {
        "brand": "#d77757",
        "brand.shimmer": "#eb9f7f",
        "text.primary": "#ffffff",
        "text.inactive": "#999999",
        "text.subtle": "#505050",
        "status.success": "#4eba65",
        "status.error": "#ff6b80",
        "status.warning": "#ffc107",
        "status.permission": "#b1b9f9",
        "status.plan": "#48968c",
        "status.auto": "#af87ff",
        "border.prompt": "#888888",
        "border.tool": "#fd5db1",
        "diff.added": "white on #225c2b",
        "diff.removed": "white on #7a2936",
        "diff.added.word": "white on #38a660",
        "diff.removed.word": "white on #b3596b",
        "message.user": "white on #373737",
        "selection": "white on #264f78",
    }
)

console = Console(theme=APP_THEME)
```

Add light, daltonized, and ANSI variants behind the same semantic keys. Detect capability with console
properties and configuration; do not branch style decisions throughout render functions.

## Layout Skeleton

```python
from rich.layout import Layout

def make_layout() -> Layout:
    root = Layout(name="root")
    root.split_column(
        Layout(name="header", size=5),
        Layout(name="messages", ratio=1),
        Layout(name="overlay", size=0),
        Layout(name="prompt", size=4),
        Layout(name="footer", size=2),
    )
    return root
```

Change region sizes from state. For a permission dialog, update `overlay` and allocate height. For a
full modal, render a centered panel inside the message region or upgrade to a Textual screen.

## Scrollback MVP Pattern

```python
from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.text import Text

console = Console(theme=APP_THEME)

def print_completed_message(renderable) -> None:
    console.print(renderable)

def waiting_row(verb: str) -> Text:
    return Text.assemble(("Working ", "text.inactive"), (verb, "brand"))

with Live(
    waiting_row("Analyzing..."),
    console=console,
    transient=True,
    refresh_per_second=12,
) as live:
    # Route model events here and update the active row.
    live.update(Spinner("dots", text=" Analyzing..."))
```

Prefer scrollback mode until the product actually requires owned viewport navigation.

## Full-Screen Rich Pattern

```python
from rich.live import Live

layout = make_layout()
state = initial_state()

with Live(
    layout,
    console=console,
    screen=True,
    refresh_per_second=20,
    vertical_overflow="crop",
) as live:
    while state.running:
        event = next_event()
        state = reduce(state, event)
        update_layout(layout, state)
```

Use a single `Live` owner. Do not create nested repaint loops for messages, spinner, and progress rows.
Nested `Live` displays may be supported by current Rich versions, but one top-level owner is easier to
reason about for an agent application.

## Custom Renderable Pattern

```python
from collections.abc import Iterable
from rich.console import Console, ConsoleOptions, RenderResult
from rich.text import Text

class SpinnerRow:
    def __init__(self, frame: str, verb: str, elapsed: str) -> None:
        self.frame = frame
        self.verb = verb
        self.elapsed = elapsed

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = max(0, options.max_width - len(self.frame) - len(self.elapsed) - 3)
        label = self.verb[:width]
        yield Text.assemble(
            (self.frame, "brand"),
            (" ", ""),
            (label, "text.inactive"),
            (" " * max(1, width - len(label) + 1), ""),
            (self.elapsed, "text.subtle"),
        )
```

Implement custom renderables only where semantic composition is clearer than repeated layout code.

## Official Sources

- [Rich documentation](https://rich.readthedocs.io/en/stable/)
- [Live displays](https://rich.readthedocs.io/en/stable/live.html)
- [Layouts](https://rich.readthedocs.io/en/stable/layout.html)
- [Console API](https://rich.readthedocs.io/en/stable/reference/console.html)
- [Themes](https://rich.readthedocs.io/en/stable/themes.html)
- [Styles](https://rich.readthedocs.io/en/stable/style.html)
- [Panels](https://rich.readthedocs.io/en/stable/panel.html)
- [Syntax highlighting](https://rich.readthedocs.io/en/stable/syntax.html)
- [Console Protocol](https://rich.readthedocs.io/en/stable/protocol.html)
- [Rich repository](https://github.com/Textualize/rich)
