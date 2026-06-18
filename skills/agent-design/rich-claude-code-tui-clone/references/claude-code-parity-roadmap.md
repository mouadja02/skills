# Claude Code Parity Roadmap

Translate the supplied Claude Code visual report into staged Python work. Match hierarchy and behavior
before chasing pixel-level details.

## State Model

Start with explicit state:

```python
from dataclasses import dataclass, field
from enum import Enum

class ScreenMode(str, Enum):
    PROMPT = "prompt"
    TRANSCRIPT = "transcript"

class Activity(str, Enum):
    IDLE = "idle"
    THINKING = "thinking"
    STREAMING = "streaming"
    TOOL = "tool"
    STALLED = "stalled"

@dataclass(frozen=True)
class Message:
    id: str
    kind: str
    content: str
    complete: bool = True
    metadata: dict[str, object] = field(default_factory=dict)

@dataclass(frozen=True)
class PermissionRequest:
    id: str
    tool_name: str
    summary: str
    choices: tuple[str, ...] = ("allow_once", "allow_always", "deny")

@dataclass(frozen=True)
class ViewportState:
    top: int = 0
    follow_tail: bool = True
    unseen_count: int = 0
    search_query: str = ""
    search_match: int = 0

@dataclass(frozen=True)
class AppState:
    messages: tuple[Message, ...] = ()
    mode: ScreenMode = ScreenMode.PROMPT
    activity: Activity = Activity.IDLE
    spinner_verb: str = "Working"
    prompt_text: str = ""
    permission: PermissionRequest | None = None
    viewport: ViewportState = field(default_factory=ViewportState)
    reduced_motion: bool = False
    running: bool = True
```

Reducers should be deterministic. Timers emit events; they do not mutate renderables directly.

## Parity Ladder

### Milestone 1: Scrollback Conversation

Implement:
- Condensed project-owned logo line
- User message block
- Assistant Markdown block
- Tool invocation and tool result panels
- Spinner with verb and elapsed time
- Plain prompt
- Basic transcript export

Use:
- `Console.print()`
- `Panel`
- `Markdown`
- `Syntax`
- transient `Live`

Defer:
- Fullscreen viewport
- Search
- Hover and mouse interactions
- Modal overlays
- Vim mode

### Milestone 2: Rich Fullscreen

Implement:
- Header, message viewport, prompt, and footer regions
- `Live(screen=True)` owner
- Permission panel overlay
- Prompt and transcript modes
- Viewport slicing, sticky prompt indicator, unseen-message divider
- Transcript search state and plain-text dump
- Dark, light, ANSI, and reduced-motion settings

Use:
- `Layout`
- `Group`
- `Table.grid`
- `Rule`
- `Console(record=True).export_text()`

Application-owned work:
- Keyboard dispatch
- Visible message slice
- Search indexing
- Resize handling
- Focus rules

### Milestone 3: Claude Code-Level Interaction

Upgrade to Textual or an equivalent widget framework when required:
- Multiline editor with cursor movement and paste handling
- Slash completion and fuzzy file search
- Vim mode
- Clickable and collapsible tool blocks
- Mouse selection and clipboard
- Modal screens with focus isolation
- Virtualized long transcripts
- Concurrent agent/session panes
- Interactive shell pane

The official Textual README describes widgets, layouts, themes, async integration, testing, and a fuzzy
command palette. Toad demonstrates that a modern agentic TUI puts these interaction-heavy features in a
Textual application while still using Rich concepts underneath.

## Visual Mapping

| Visual report element | Python implementation |
| --- | --- |
| Full or condensed logo | `Group` or `Table.grid`; project-owned mascot renderable |
| Status notices | Styled `Text` fragments or one-row `Table.grid` |
| Message stream | Cached message renderables plus visible slice |
| User message background | `Panel` or padded `Text` with `message.user` style |
| Thinking block | Dim italic `Text`; collapsed by default |
| Tool call group | Compact `Text` summary; expand to `Panel` in transcript mode |
| Prompt border | `Panel` with `border.prompt`; input subsystem provides cursor |
| Footer | `Table.grid(expand=True)` with left and right columns |
| Permission mode pill | Short styled `Text` span |
| Spinner | Built-in `Spinner` or custom braille frame sequence |
| Markdown | `Markdown` for complete content; suffix renderer while streaming |
| Code fence | `Syntax` with detected or explicit lexer |
| Structured diff | `Text` spans with semantic background styles |
| Transcript footer | `Rule` plus status row |
| Search highlight | `Text.stylize()` spans |
| Unseen divider | `Rule("3 new")` |
| Agent activity tree | `Table.grid` or `Tree` with spinner/status columns |

## Logo and Mascot Policy

Default to a project-owned identity:

```text
* Project Agent | model | ~/workspace
```

If a mascot is wanted:
- Keep it narrow enough for a 60-column terminal.
- Provide Unicode and ASCII fallbacks.
- Render color and shape through a dedicated function.
- Change pose from state, not from arbitrary writes.
- Do not ship third-party brand artwork without permission.

## Message Rendering Rules

### User Messages

- Show a visible prompt prefix.
- Use a distinct background or border.
- Preserve wrapped multiline input.
- Summarize pasted blocks rather than flooding the transcript.

### Assistant Messages

- Render final blocks with `Markdown`.
- Keep active text visually stable while streaming.
- Collapse thinking by default; expose a transcript-mode expansion path.
- Cache complete blocks.

### Tool Messages

- Use compact completed summaries for reads and searches.
- Use a visible activity state for active tools.
- Show errors with both a label and an error color.
- Render dangerous commands inside permission panels before execution.

### Diffs

Start with `difflib.unified_diff`. For word-level highlighting:

1. Pair nearby removed and added lines.
2. Use `difflib.SequenceMatcher` on tokens or words.
3. Apply background styles to changed segments.
4. Keep line numbers dim and right-aligned.
5. Cap rendered lines and report truncation.

Do not make `Syntax` responsible for word-level diff backgrounds. Compose styled `Text` lines and use
syntax highlighting only where the combination remains legible.

## Streaming Cache Key

Cache immutable message blocks by:

```text
(message_id, content_version, terminal_width, theme_name, expanded)
```

Rebuild on:
- Width changes
- Theme changes
- Expansion toggles
- New content versions

Keep the active response out of the immutable cache until it reaches stable block boundaries.

## Feature Ownership Matrix

| Feature | `scrollback` | `rich-screen` | `textual-app` |
| --- | --- | --- | --- |
| Logo and messages | Rich | Rich | Rich renderables in widgets |
| Spinner | transient `Live` | top-level `Live` | timer/reactive widget |
| Prompt | plain line input | app-owned input adapter | `TextArea`-style widget |
| Fullscreen | no | `Live(screen=True)` | application screen |
| Transcript export | recording console | recording console | render/export action |
| Search | terminal native | app-owned index | widget-level interaction |
| Permission UI | line prompt | overlay region | modal/focused widget |
| Mouse events | no | terminal adapter | framework events |
| Virtualization | no | app-owned slice | scroll/virtualized widgets |

## Optional Textual Upgrade

Use Textual when the requirements justify it. Keep the same domain model and reducers. Replace only the
outer rendering and input adapters:

```text
runtime events -> reducer -> AppState -> Textual widgets/screens
                              |
                              +-> Rich Text, Markdown, Syntax, Panel renderables
```

Architecture lessons visible in Toad:
- An async application owns screens and bindings.
- Prompt input is a widget concern.
- Permission questions are focused widget state.
- Streaming Markdown may need custom widget behavior.
- Diffs may justify a dedicated view component.
- Shell integration is substantially more complex than printing command output.

These are architecture observations, not permission to copy implementation.

## Sources

- [Textual repository](https://github.com/Textualize/textual)
- [Textual README](https://github.com/Textualize/textual/blob/main/README.md)
- [Toad repository](https://github.com/batrachianai/toad)
- [Toad README](https://github.com/batrachianai/toad/blob/main/README.md)
- [Toad license](https://github.com/batrachianai/toad/blob/main/LICENSE)
