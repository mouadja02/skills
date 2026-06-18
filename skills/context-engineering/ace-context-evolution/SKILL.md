---
name: ace-context-evolution
description: Use when long-lived agents, project memories, system prompts, or playbooks are repeatedly summarized, rewritten, or optimized and risk losing domain detail, provenance, or execution learnings.
source: "https://arxiv.org/abs/2510.04618"
---

# ACE Context Evolution

Treat durable context as an evolving playbook, not a shrinking summary. Preserve proven detail, update incrementally, and require execution evidence before promoting lessons.

## Use When

- Agent memory, `CLAUDE.md`, `AGENTS.md`, skill docs, or prompt files are being revised after repeated runs.
- Summaries are getting shorter but less useful.
- Lessons learned from failures need to become reusable project context.
- The user wants self-improving agents without fine-tuning.

## Core Workflow

1. Separate context into stable instructions, reusable strategies, task evidence, rejected ideas, and open questions.
2. Add new lessons as patches with source evidence instead of rewriting the whole context.
3. Promote only lessons backed by run logs, tests, user corrections, benchmark deltas, or repeated task outcomes.
4. Preserve provenance: include where the lesson came from, when it was observed, and when it should be reconsidered.
5. Prune by invalidating obsolete entries, not deleting them silently, when future agents may need the reason.
6. Run a collapse check before accepting a rewrite.

## Context Patch Contract

Every durable update should include:

| Field | Purpose |
| --- | --- |
| `claim` | The reusable instruction or lesson |
| `evidence` | Command, trace, eval, user correction, issue, PR, or paper source |
| `scope` | Where it applies and where it does not |
| `owner` | File, skill, team, or subsystem affected |
| `expiry` | Date or condition for review |
| `conflicts` | Older rules this supersedes or limits |

See [context-evolution-contract.md](references/context-evolution-contract.md) for templates.

## Collapse Guard

Before replacing any long-lived context, compare the old and new versions:

```bash
python skills/context-engineering/ace-context-evolution/scripts/context_update_guard.py OLD.md NEW.md
```

Reject the rewrite if it drops named tools, file paths, commands, metric thresholds, failure modes, citations, or explicit constraints without an invalidation note.

## Common Mistakes

| Mistake | Fix |
| --- | --- |
| Rewriting the whole context after each run | Apply small patches grouped by evidence type |
| Treating shorter as better | Preserve operational details that changed behavior |
| Promoting one-off anecdotes | Require repeated evidence or a clear high-impact failure |
| Deleting stale rules | Mark them superseded and keep the reason if future agents may rediscover them |
| Mixing task scratchpads with durable memory | Keep transient reasoning out of permanent context |

## References

- arXiv: Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models - https://arxiv.org/abs/2510.04618
- Hugging Face Papers: Agentic Context Engineering - https://huggingface.co/papers/2510.04618
- GitHub: ACE implementation - https://github.com/ace-agent/ace
- GitHub: ACE AppWorld experiments - https://github.com/ace-agent/ace-appworld
