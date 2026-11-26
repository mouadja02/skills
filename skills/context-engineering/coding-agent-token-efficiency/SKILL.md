---
name: coding-agent-token-efficiency
description: >-
  Use when a coding agent (Claude Code, Cursor, Codex, Copilot CLI) burns through tokens or usage limits,
  sessions get slow or hit context limits, or the user asks to cut agent cost. Measures where the tokens
  go, then applies levers in order: session hygiene, always-loaded context (CLAUDE.md, skills, MCP),
  tool-output filtering, subagent delegation, output verbosity, and model/effort choice.
version: "1.1.0"
license: MIT
source: "https://code.claude.com/docs/en/costs"
attribution: "Written for this collection from Anthropic's Claude Code cost guide and the RTK and caveman projects' published measurements"
---

# Coding Agent Token Efficiency

A coding agent re-sends the whole conversation — system prompt, memory files, skill descriptions, tool
schemas, every tool result so far — on every request. Prompt caching makes the repeats cheaper, not
free. Most waste comes from context that is loaded but never used and from tool output nobody needed.
Measure first, then cut in the order below; the early levers cost nothing in quality.

## When to Use

- "I hit my usage limit by lunch", "this session is eating tokens", or a large unexpected API bill.
- Sessions slow down, auto-compact repeatedly, or report context-limit warnings.
- Setting up a repo or a team for an agent and wanting sane defaults.
- After installing many skills, plugins, or MCP servers.

Not for cutting the cost of an application that calls an LLM API — use `llm-cost-optimization`.

## Workflow

```
Token efficiency pass:
- [ ] 1. Baseline measured
- [ ] 2. Always-loaded context trimmed
- [ ] 3. Session habits fixed
- [ ] 4. Tool output filtered
- [ ] 5. Output and model/effort tuned
- [ ] 6. Re-measured on comparable work
```

### 1. Measure the baseline

Pick the measurements the client offers:

| Client | Where tokens go | Spend over time |
| --- | --- | --- |
| Claude Code | `/context` (breakdown of the window), `/usage` (session tokens, cache hit rate, and on subscription plans a breakdown by skills, subagents, and MCP servers) | `/usage` daily/weekly view; `npx ccusage` reads local session logs |
| Any client | `python3 scripts/context_budget.py <project> --client claude` (or `cursor`, `agents`) | Provider console |

`scripts/context_budget.py` is read-only and uses only the Python standard library. It estimates the
context loaded before the first prompt: memory files (`CLAUDE.md`, `CLAUDE.local.md`, `AGENTS.md`,
`~/.claude/CLAUDE.md`) and the name and description of every installed skill, which clients keep in
context on every request. It does not see plugin skills, tool schemas, or MCP servers — `/context` does.

Write the baseline down: always-loaded tokens, cache hit rate, and tokens for one representative task.

### 2. Trim always-loaded context

| Source | Do | Default target |
| --- | --- | --- |
| `CLAUDE.md` / `AGENTS.md` | Keep only what every task needs. Move workflow-specific instructions (release steps, migration rules) into skills, which load on demand. | Under 200 lines (Anthropic's guidance) |
| Installed skills | Every description is sent on every request. Uninstall unused ones; install by need, not whole libraries. For large libraries, discover skills on demand (this repository's skills MCP server, `docs/skills-mcp.md`). | Only skills you used this month |
| Skill bodies | A skill body over ~500 lines costs that much on every use. Split reference into `references/`. | Under 500 lines |
| MCP servers | Disable servers you are not using (`/mcp`). Prefer a CLI (`gh`, `aws`, `kubectl`) when one exists: it adds no tool listing. | Only servers this project needs |

### 3. Fix session habits

- **`/clear` between unrelated tasks.** Stale history is re-sent with every message. `/clear` costs
  nothing; `/compact` is itself a large request because it reads what it summarizes.
- **Compact with intent:** `/compact keep the failing test output and the API decisions`.
- **Hand off instead of dragging a session on:** the `session-handoff` skill writes a summary a fresh
  session can start from.
- **Mind the cache lifetime.** The first message after a pause longer than the prompt-cache TTL
  re-processes the whole context at full price (in Claude Code: an hour on a subscription, five minutes
  once you draw on usage credits, five minutes by default on API keys and cloud providers). Long idle sessions with scheduled loops or check-ins re-send full
  context each time they fire.
- **Be specific.** "Add input validation to `login()` in `auth.ts`" reads one file; "improve this
  codebase" reads many. Use plan mode for large changes so a wrong direction is caught before it is
  built, and stop a wrong turn early (Esc, `/rewind`).

### 4. Filter tool output before it enters context

Tool results are usually the largest input. In order of effort:

1. **Delegate bounded legwork to a smaller-model subagent.** Good units are investigation (locate the
   relevant code and explain it), reproduction (build and run the smallest reproducer), and verification
   (run the reproducer and relevant tests). The lead agent keeps the final patch or decision; do not hand
   off the whole task merely because the subagent is cheaper.
   - Launch independent subtasks in the same turn or parallel call instead of serially paying for another
     full-context lead-model step between them.
   - Ask for a short report containing only decision-relevant facts, file paths, line numbers, and exact
     error messages—not raw logs or a transcript of every tool call.
   - Treat the report as compressed evidence, not truth. Recheck any fact or claim that the final fix,
     patch, or decision depends on.
   - Prefer work whose result is cheap to verify. Keep tightly coupled reasoning in the lead context when
     summarization would hide constraints or when the verification cost approaches the delegated saving.
2. **Filter with a hook.** A `PreToolUse` hook can rewrite `npm test` to keep only failures
   (`grep -A 5 -E '(FAIL|ERROR|error:)' | head -100`); Anthropic's cost guide has a complete example.
3. **Use a filtering proxy.** [RTK](https://github.com/rtk-ai/rtk) rewrites common commands (`git`,
   `ls`, test runners, linters, `docker`) to compressed forms through a hook installed with
   `rtk init -g`, and reports savings with `rtk gain`. It publishes 60–90% reductions on command output,
   but command output is only part of the input bill. Caveats: it only sees shell commands, so built-in
   Read/Grep/Glob tools bypass it; and the compression engine is BUSL-1.1 source-available (an
   Apache-only edition omits it).
4. **Use code intelligence** (language-server plugins) so the agent jumps to definitions instead of
   grepping and reading candidate files.

### 5. Tune output, model, and effort

- **Output tokens** cost several times input tokens. Ask for the shape you want ("diff only", "one
  paragraph"). For a terse voice across a session, the `caveman` skill applies rules that keep code,
  commands, and errors verbatim. Its own benchmark is honest about the size: about 3% fewer output tokens
  than a plain "answer concisely" at the median, with its rules costing about 1,160 input tokens. It
  saves nothing on per-request billing (some IDE plans), and `caveman-compress` shrinks memory files
  instead (it sends their text to a model provider).
- **Model:** use the mid-tier model for most coding and the top tier for hard architecture or long
  multi-step reasoning; give simple subagents the small model (`model: haiku` in a subagent definition).
- **Effort / thinking:** lower effort for routine work (`/effort` in Claude Code). Thinking tokens bill
  as output.
- **Agent teams** multiply cost by the number of active teammates (Anthropic measured about 7× tokens
  for teams in plan mode). Keep teams small and shut teammates down when done.

### 6. Re-measure

Repeat step 1 as a matched comparison: run baseline and delegated candidates on the same representative
tasks and completed-task checks. Record lead/frontier-model tokens and cost separately, but also report
total delegated compute, wall-clock latency, retries, pass rate or completion quality, and any human
rework. Keep a change only if cost per completed task fell without moving cost into slower local compute,
extra retries, or missed requirements. A lower frontier-model bill alone is not an efficiency win.

## Gotchas

- **A smaller context is not automatically a cheaper task.** If the agent now has to rediscover what
  `CLAUDE.md` used to tell it, it spends turns reading files. Move instructions into skills, do not
  delete them.
- **Editing `CLAUDE.md`, the tool list, or MCP servers mid-session invalidates the prompt cache.** Make
  those changes between sessions.
- **Do not trust headline percentages.** Savings tools measure their own slice (command output, response
  text). Judge them by your bill or `/usage` on real work.
- **Commands and limits change between client versions.** The commands above match Claude Code's cost
  guide as of its October 2026 version; check `claude --version` and the guide if one is missing.

## Related skills

`caveman`, `caveman-compress`, `session-handoff`, `context-compression`, `context-optimization`,
`llm-cost-optimization`.

## Sources

- Anthropic, [Manage costs effectively](https://code.claude.com/docs/en/costs) (Claude Code).
- Anthropic, [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — metadata preloading, 500-line guidance.
- [rtk-ai/rtk](https://github.com/rtk-ai/rtk) README — mechanism, measurements, licensing.
- [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman) README — benchmark method and caveats.
- [ccusage](https://github.com/ccusage/ccusage) — local Claude Code usage reports.
- Gu & Lin, [Delegent: A Multi-Agent Harness That Reduces Cost without Sacrificing Performance](https://arxiv.org/abs/2611.33098v1)
  and [castorini/delegent](https://github.com/castorini/delegent) — bounded smaller-model delegation and
  matched task-level evaluation; results are workload- and hardware-specific, not universal savings.
