---
name: github-deep-review
description: "GitHub deep review: bugs, PRs, best fix, stale-or-real, read code first, evidence-first."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
version: "1.0.0"
---

# GitHub Deep Review

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

## When to Use

- Deep-diving into bug reports or PRs to find root cause
- Evidence-first code review where you read code before forming opinions
- Determining if an issue is stale, a duplicate, or a real bug
- Proposing the best fix with high confidence

High-confidence, evidence-first, code-aware review. The goal is not a generic summary. The goal is to understand the bug class, find the real cause if possible, decide the best fix after reading enough code, and call out whether a larger refactor would improve the design.

## Start

Use `gh`, not web browsing, for GitHub refs:

```bash
gh issue view <n> --json number,title,state,author,body,comments,labels,updatedAt,url
gh pr view <n> --json number,title,state,author,body,comments,reviews,files,commits,statusCheckRollup,mergeStateStatus,headRefName,headRepositoryOwner,url
gh pr diff <n> --patch
```

For repo-local review, also inspect:

```bash
git status --short --branch
git fetch origin
git log --oneline --decorate -20
rg "<key symbol/error/config/endpoint>"
```

## Review Contract

Always answer these, explicitly:

- URL/ref: issue or PR number and affected surface.
- What is the bug or behavior being fixed?
- Can we identify the root cause? If yes, where in code and why. If no, what evidence is missing.
- For regressions, who/what introduced it and when?
- Is the current/proposed fix the best possible fix after reading adjacent code?
- Would a bigger refactor improve correctness, clarity, or future maintainability?
- What proof exists: tests, live repro, CI checks, docs, dependency docs/source.
- What remains risky or unverified.

## Code Reading Depth

Read past the first touched file. Follow the real call path:

- entrypoint -> validation/parsing -> routing/dispatch -> owner module -> shared helper -> persistence/network/runtime boundary
- config/schema/docs -> runtime usage -> doctor/migration/fix path
- tests around the touched surface plus adjacent regression tests

When behavior depends on a dependency, read the upstream docs/source/types or current package contract before assuming.

Prefer current source and executable proof over issue comments. Treat stale comments, old CI, and old release behavior as hints until rechecked.

## Provenance

For bug/regression reviews, include a compact `Provenance:` answer when feasible:

- Use `git log -S/-G`, `git blame`, linked PRs/issues, and tests.
- Phrase as `introduced by`, `made visible by`, or `carried forward by`.
- Include confidence: `clear`, `likely`, or `unknown`.

## Fix Quality Bar

Good fixes usually:

- live at the ownership boundary where the bug belongs
- preserve public/backward-compatible behavior unless the issue is about retiring it
- add a regression test at the smallest meaningful seam
- avoid broad special cases, hidden migrations, semantic sentinels
- update docs/changelog when user-visible behavior changes
- fail clearly in runtime paths

Call out when a fix is only symptom-level. If a slightly larger refactor makes the invariant obvious and reduces future bugs, recommend it.

## PR Review Shape

Lead with findings when reviewing a PR. Findings need file/line/symbol references and a concrete failure mode. Avoid vague "consider" comments.

If no blocking issues:

- say no blocking correctness issues found
- list the strongest proof checked
- name residual risk/test gaps
- answer whether the design is the best available shape

Do not approve, comment, close, merge, push, or land unless the user asked for that action.

## Issue Review Shape

For bugs/issues:

1. Reconstruct the reporter's scenario and affected version/surface.
2. Check whether current `main` already fixes it.
3. Reproduce or create a minimal local/live proof when feasible.
4. If clear, identify root cause and proposed fix.
5. If solved on `main`, only comment/close when the user asks.

## Output Template

```text
Ref: #123 / PR #456
Surface: <runtime/CLI/provider/channel/docs>

Bug: <one or two sentences>
Cause: <code path + confidence>
Provenance: <introduced/made visible/carried forward by commit/PR/date, or N/A/unknown>
Best fix: <what should change and why>
Refactor: <yes/no, specific shape>
Proof: <tests/live/CI/source/dependency docs>
Risk: <remaining uncertainty>
```
