# SWE Agent Loop Checklist

## Issue Intake

- What is the observed behavior?
- What is the expected behavior?
- What version, environment, or configuration matters?
- Which command or user action reproduces it?
- What would count as acceptance?

## Reproduction

Prefer this command ladder:

1. Single failing unit test
2. Narrow integration test
3. Package-level test command
4. Full suite only when the narrower command is unavailable

Record:

- Command
- Exit code
- Relevant failure lines
- Whether failure is deterministic

## Patch Constraints

- No unrelated refactors
- No benchmark-specific hardcoding
- No silent dependency upgrades
- No destructive commands outside the sandbox
- Preserve user changes in the worktree

## Verification

A repair is not done until:

- The original reproducer passes or the failure is explicitly invalidated
- At least one adjacent regression check passes
- The final diff is understandable
- Residual risk is stated

## References

- SWE-bench Verified: https://www.swebench.com/verified.html
- mini-SWE-agent benchmark docs: https://mini-swe-agent.com/latest/usage/swebench/
- SWE-ReX: https://github.com/SWE-agent/swe-rex
- OpenHands Software Agent SDK: https://huggingface.co/papers/2511.03690
- OpenHands: https://github.com/All-Hands-AI/OpenHands

