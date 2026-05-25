---
name: discord-clawd
description: "Discord-backed OpenClaw agent/session relay — post/ask via relay, not archive search."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# Discord Clawd

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use this when the task is to talk with the Discord-backed agent/session, ask it a question, or post through that route.

For Discord archive/history/search, use a Discord search/crawl tool instead.

## Transport

Use the OpenClaw relay helper:

```bash
python3 skills/openclaw-relay/scripts/openclaw_relay.py targets
python3 skills/openclaw-relay/scripts/openclaw_relay.py resolve --target maintainers
```

If the target alias exists, prefer a private ask first:

```bash
python3 skills/openclaw-relay/scripts/openclaw_relay.py ask \
  --target maintainers \
  --message "Reply with exactly OK."
```

Use `publish` when the session should decide whether to post. Use `force-send` only when the user explicitly wants a message posted.

## Guardrails

- Resolve the target before sending real content.
- Report the target and delivery mode used.
- Do not use this for local Discord archive queries.
- Do not expose gateway tokens or session secrets.
