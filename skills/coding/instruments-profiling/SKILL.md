---
name: instruments-profiling
description: "Instruments/xctrace profiling: macOS/iOS traces, binaries, args, exports, Time Profiler."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# Instruments Profiling (macOS/iOS)

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use this skill when the user wants performance profiling or stack analysis for native apps.
Focus: Time Profiler, `xctrace` CLI, and picking the correct binary/app instance.

## Quick Start (CLI)

```bash
# List templates
xcrun xctrace list templates

# Record Time Profiler (launch)
xcrun xctrace record --template 'Time Profiler' --time-limit 60s --output /tmp/App.trace --launch -- /path/To/App.app

# Record Time Profiler (attach)
xcrun xctrace record --template 'Time Profiler' --time-limit 60s --output /tmp/App.trace --attach <pid>

# Open trace in Instruments
open -a Instruments /tmp/App.trace
```

Note: `xcrun xctrace --help` is not a valid subcommand. Use `xcrun xctrace help record`.

## Picking the Correct Binary (Critical)

**Gotcha: Instruments may profile the wrong app** (e.g., one in `/Applications`) if LaunchServices resolves a different bundle.

- Prefer direct binary path for deterministic launch:
  - `xcrun xctrace record ... --launch -- /path/App.app/Contents/MacOS/App`
- After launch, confirm the process path before trusting the trace.

## Command Arguments

- `--template 'Time Profiler'`: template name from `xctrace list templates`.
- `--launch -- <cmd>`: everything after `--` is the target command.
- `--attach <pid|name>`: attach to running process.
- `--output <path>`: `.trace` output.
- `--time-limit 60s|5m`: set capture duration.
- `--device <name|UDID>`: required for iOS device runs.

## Exporting Stacks (CLI)

```bash
# Inspect trace tables
xcrun xctrace export --input /tmp/App.trace --toc

# Export raw time-profile samples
xcrun xctrace export --input /tmp/App.trace \
  --xpath '/trace-toc/run[@number="1"]/data/table[@schema="time-profile"]' \
  --output /tmp/time-profile.xml
```

## Instruments UI Workflow

- Template: Time Profiler
- Use "Record" and capture the slow path (startup vs steady-state)
- Call Tree tips:
  - Hide System Libraries
  - Invert Call Tree
  - Separate by Thread
  - Focus on hot frames and call counts

## Gotchas & Fixes

- **Wrong app profiled**: Use direct binary path or `--attach` with known PID.
- **No samples / empty trace**: Longer capture, trigger workload during recording.
- **Privacy prompts**: System Settings → Privacy & Security → Developer Tools → allow Terminal/Xcode.
- **Large XML exports**: Filter with XPath and aggregate offline; don't print to terminal.

## iOS Specific Notes

- Device: use `xcrun xctrace list devices` and `--device <UDID>`.
- Ensure debug symbols for meaningful stacks.

## Verification Checklist

- [ ] Confirm trace process path matches target build
- [ ] Confirm stacks show expected app frames
- [ ] Capture covers the slow operation (startup/refresh)
- [ ] Export stacks for automated diffing if optimizing
