---
name: codex-debugging
description: "Codex debugging: codex-rs core/tui/exec/cli/app-server/config."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
version: "1.0.0"
---

# Codex Debugging

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

## When to Use

- Debugging Codex CLI/app behavior, config parsing, or tool invocations
- Navigating the codex-rs codebase (core/tui/exec/cli/app-server)

Use when investigating Codex CLI/app behavior, config parsing, tool behavior, prompts, MCP/app wiring, or runtime bugs.

## Source First

Prefer local source before web/docs:

```bash
cd ~/Projects/codex
sed -n '1,220p' codex-rs/AGENTS.md
```

Then search targeted areas:

```bash
rg "<symbol|setting|error|feature>" codex-rs/{core,tui,exec,cli,app-server,app-server-protocol,config}
```

## Workflow

1. Identify whether the behavior is CLI, TUI, app server, protocol, config, or exec/tooling.
2. Read the owning module and adjacent tests before proposing changes.
3. Check local config in `~/.codex/config.toml` only after understanding the source contract.
4. Prefer small repros or focused tests over broad speculation.

## Notes

- For OpenAI API/product docs, use the official-docs path only when source is insufficient.
- For local browser automation in CLI, use `$browser-use`; the bundled Browser plugin is Codex app-only.
