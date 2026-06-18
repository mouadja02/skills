---
name: swe-agent-issue-loop
description: Use when turning GitHub issues or bug reports into reproducible coding-agent repair loops with sandboxed execution, focused tests, patch generation, and regression verification.
source: "https://www.swebench.com/verified.html"
attribution: "Synthesized from SWE-bench Verified, mini-SWE-agent, SWE-ReX, and OpenHands Software Agent SDK research."
---

# SWE Agent Issue Loop

Use this skill to handle issue-driven software engineering tasks the way modern coding-agent benchmarks and production agent harnesses do: isolate the repository, reproduce the failure, edit narrowly, and verify with executable tests.

## When To Use

Activate when the user asks to:

- Fix a GitHub issue, bug report, failing test, or CI failure
- Build a coding-agent benchmark task
- Convert an issue into a reproducible repair workflow
- Compare agent scaffolds on software engineering tasks
- Add guardrails around autonomous coding agents

## Repair Loop

1. **Frame the issue**
   - Extract expected behavior, observed behavior, affected files, environment, and acceptance criteria.
   - Identify what evidence is missing before editing.
   - Record any user constraints such as no refactor, no dependency changes, or no UI changes.

2. **Build a reproduction**
   - Run the smallest relevant failing command.
   - Prefer a focused test over full-suite execution.
   - If no test exists, write or sketch one before implementation when feasible.
   - Store command, result, and failure reason.

3. **Patch narrowly**
   - Read the local code around the failing behavior.
   - Change the smallest coherent surface.
   - Avoid solving benchmark tasks by hardcoding issue text, test names, or environment-specific values.

4. **Verify**
   - Re-run the reproducer.
   - Run adjacent tests or a targeted suite.
   - Check for formatting, lint, type, or build regressions when relevant.
   - Summarize command outcomes in the final response.

5. **Harden the harness**
   - Use sandboxed execution for autonomous agents.
   - Cap command timeouts and output length.
   - Separate model instructions from tool output.
   - Preserve full trajectories for later review.

## Benchmark-Aware Guidance

SWE-bench Verified emphasizes clear issue descriptions, correct tests, and solvable tasks. Mirror that standard for internal benchmarks:

- Do not include ambiguous reports without expected behavior.
- Do not count a task as solved unless tests or deterministic checks pass.
- Track whether the agent used only allowed context.
- Capture the diff and trajectory, not only pass/fail.

## Helper Script

Use [issue_repro_matrix.py](./scripts/issue_repro_matrix.py) to convert issue text into a reproducibility matrix:

```bash
python scripts/issue_repro_matrix.py issue.md
```

## References

Read [agent-loop-checklist.md](./references/agent-loop-checklist.md) before designing a coding-agent harness or benchmark task.

External grounding:

- [SWE-bench Verified](https://www.swebench.com/verified.html)
- [mini-SWE-agent SWE-bench documentation](https://mini-swe-agent.com/latest/usage/swebench/)
- [SWE-ReX GitHub repository](https://github.com/SWE-agent/swe-rex)
- [OpenHands Software Agent SDK HuggingFace paper page](https://huggingface.co/papers/2511.03690)
- [OpenHands GitHub repository](https://github.com/All-Hands-AI/OpenHands)

