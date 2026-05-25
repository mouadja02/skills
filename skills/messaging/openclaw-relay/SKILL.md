---
name: openclaw-relay
description: "OpenClaw session relay: prompts/posts via local/remote relay over SSH — ask, publish, force-send."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# OpenClaw Relay

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use this when the job is to relay a prompt or post through an OpenClaw session (local or remote via SSH).

Two transports:
1. `local` — direct telephone-game work from the current checkout.
2. `ssh` — when the target agent/session lives on another machine.

## Quick Start

```bash
# Health check
python3 scripts/openclaw_relay.py doctor

# List known target aliases
python3 scripts/openclaw_relay.py targets

# Resolve a target alias
python3 scripts/openclaw_relay.py resolve --target maintainers

# Ask a target session a question privately
python3 scripts/openclaw_relay.py ask \
  --target maintainers \
  --message "Summarize the current vibe in this channel."

# Force-send text to the resolved target
python3 scripts/openclaw_relay.py force-send \
  --target maintainers \
  --text "Deploy is done."
```

## Session Rules

| Goal | Command |
|------|---------|
| Private reply from specific session | `ask` |
| Let target session decide whether to post | `publish` |
| Guaranteed direct post | `force-send` |
| Blocking continuity with control brain | `send` |
| Fire-and-forget async | `start`, then `wait` + `show` |
| Stop queued work | `cancel` |

## Async Workflow

```bash
python3 scripts/openclaw_relay.py start --message "Work on X and reply when done."
python3 scripts/openclaw_relay.py wait --after-seq <last-seq>
python3 scripts/openclaw_relay.py show
```

## Remote Host Example

```bash
python3 scripts/openclaw_relay.py doctor --transport ssh --host user@remote-host
python3 scripts/openclaw_relay.py send \
  --transport ssh \
  --host user@remote-host \
  --message "Reply with exactly OK."
```

## Failure Handling

1. Run `doctor`.
2. Run `status`.
3. Run `show`.
4. If control session is wedged: run `cancel`, then `ensure`, then retry.

## Output

Return the actual assistant text or delivery result, not shell noise. Report:
- transport used
- target session key
- whether the route probe/resolve succeeded
- final posted or returned result
