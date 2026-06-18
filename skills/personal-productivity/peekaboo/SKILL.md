---
name: peekaboo
description: "macOS screenshots, UI inspection, clicks, typing, app/window automation via Peekaboo."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
version: "1.0.0"
platform: macos
---

# Peekaboo

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use for macOS screen capture, UI inspection, and GUI automation.

## Binary

- Check first: `peekaboo --version`.
- Prefer `~/bin/peekaboo` when present (local release copy), else `peekaboo`.

## Safety

- Check permissions before capture/automation: `peekaboo permissions status --json`.
- Screenshot needs Screen Recording; clicks/typing/window control need Accessibility.
- Do not click/type/destructively automate unless user asked or target is a controlled test.

## Common Commands

```bash
PB="${PEEKABOO_BIN:-$HOME/bin/peekaboo}"
[ -x "$PB" ] || PB="$(command -v peekaboo)"

# Check permissions
"$PB" permissions status --json

# List screens and apps
"$PB" list screens --json
"$PB" list apps --json
"$PB" list windows --app Safari --json

# Screenshots
"$PB" image --mode screen --screen-index 0 --path /tmp/screen.png --json
"$PB" see --app frontmost --path /tmp/frontmost.png --json --annotate

# Automation
"$PB" click --coords 100,100 --json
"$PB" type "text" --json

# Discovery
"$PB" tools --json
"$PB" learn
```

## Workflow

1. Resolve binary and confirm version.
2. Run `permissions status --json`; if missing TCC, report exact missing grant.
3. For screenshots, use `image`; include `--path`, `--json`, and usually `--no-remote`.
4. For element targeting, run `see --json --annotate`, then click by element id/snapshot.
5. Verify output files with `sips -g pixelWidth -g pixelHeight <path>` or view the image.

## TCC Requirements

| Task | Permission needed |
|------|-------------------|
| Screen capture | Screen Recording |
| Click / type | Accessibility |
| Window list | Accessibility |
| App list | None |
