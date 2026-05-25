---
name: one-password
description: "1Password CLI (op): service-account first, targeted secret read/store/inject, tmux session."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# 1Password CLI

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Official docs: https://developer.1password.com/docs/cli/get-started/

## Workflow

1. Check OS + shell.
2. Verify CLI present inside tmux: `op --version`.
3. **REQUIRED**: create exactly one persistent named tmux session for the whole secret task.
4. Try service-account access first when a matching token/workflow exists — no dialogs.
5. If service-account access is missing or lacks the exact item/field needed, stop and ask before desktop-app sign-in.
6. Desktop fallback: confirm app integration/unlock, then `op signin` once inside the same session.
7. Verify chosen access path inside that same session: `op whoami`.
8. If a command fails, reuse the same tmux session; do not start a second session.

## Default Account

- Default account: `my.1password.com`
- Pass `--account my.1password.com` on every `op` command when storing or reading secrets.

## Required Persistent Tmux Session

The shell tool uses a fresh TTY per command. Run `op` inside one dedicated tmux session:

```bash
SESSION="op-work"
tmux has-session -t "$SESSION" 2>/dev/null || tmux new -d -s "$SESSION" -n shell
tmux send-keys -t "$SESSION:" -- "op signin --account my.1password.com" Enter
tmux send-keys -t "$SESSION:" -- "op whoami" Enter
tmux capture-pane -p -J -t "$SESSION:" -S -200
```

## Exact Field Reads (safe pattern)

For a known item/field:

```bash
op item get "Item Title" --account my.1password.com --fields label=field_name
```

Print shape only, never values:
```bash
value="$(op item get "Item Title" --account my.1password.com --fields label=api_key)"
echo "field_len:${#value}"
```

## Service-Specific Workflows

- For npm registry/package work, use the `npm` skill.
- This skill owns only the generic 1Password rules: tmux-only `op`, targeted reads, one persistent session, no broad enumeration, no secret output.

## Guardrails

- Never paste secrets into logs, chat, or code.
- Prefer `op run` / `op inject` over writing secrets to disk.
- Do not run `op` outside tmux; stop and ask if tmux is unavailable.
- Print presence/shape only, never token or secret values.
