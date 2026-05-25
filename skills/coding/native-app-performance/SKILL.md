---
name: native-app-performance
description: "Native macOS/iOS app performance: xctrace, Time Profiler, traces, hotspot analysis — CLI-only."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# Native App Performance (CLI-only)

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Goal: record Time Profiler via `xctrace`, extract samples, symbolicate, and propose hotspots without opening Instruments.

## Quick Start (CLI)

### 1. Record Time Profiler (attach)

```bash
# Start app yourself, then attach
xcrun xctrace record --template 'Time Profiler' --time-limit 90s --output /tmp/App.trace --attach <pid>
```

### 2. Record Time Profiler (launch)

```bash
xcrun xctrace record --template 'Time Profiler' --time-limit 90s --output /tmp/App.trace --launch -- /path/App.app/Contents/MacOS/App
```

### 3. Extract time samples

```bash
xcrun xctrace export --input /tmp/App.trace \
  --xpath '/trace-toc/run[@number="1"]/data/table[@schema="time-profile"]' \
  --output /tmp/time-sample.xml
```

### 4. Get load address for symbolication

```bash
# While app is running
vmmap <pid> | rg -m1 "__TEXT" -n
```

### 5. Symbolicate + rank hotspots

```bash
# Symbolicate using atos
atos -o /path/App.app/Contents/MacOS/App -l <load-address> <address>
```

## Workflow Notes

- Always confirm you're profiling the correct binary (local build vs /Applications). Prefer direct binary path for `--launch`.
- Ensure you trigger the slow path during capture (menu open/close, refresh, etc.).
- If stacks are empty, capture longer or avoid idle sections.
- `xcrun xctrace help record` and `xcrun xctrace help export` show correct flags.

## Gotchas

- ASLR means you must use the runtime `__TEXT` load address from `vmmap`.
- If using a new build, update the binary path; symbols must match the trace.
- CLI-only flow: no need to open Instruments if stacks are symbolicated via `atos`.
