---
name: github-project-triage
description: "GitHub issue/PR triage: summarize, assess risk/testability, inspect CI/diffs/trust, autonomous work mode."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# GitHub Project Triage

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use the current GitHub project by default when the user says `triage` from inside a repo. Triage means maintainer-facing item cards: what each issue/PR is about, why it matters, author trust, fit, risk, proof/test state, blockers, and next action. Never return only queue numbers or opaque refs.

## Scope Rule

If the user says `triage` and the current working directory is a Git repo with a GitHub remote, triage only that project. Do not broaden to all org queues unless the user says `broad`, `all`, `everything`, names multiple owners/orgs, or asks for cross-repo triage.

Find the current project:

```bash
repo=$(gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || true)
if [ -z "$repo" ]; then
  url=$(git remote get-url origin 2>/dev/null || true)
  repo=$(printf '%s\n' "$url" | sed -E 's#^git@github.com:##; s#^https://github.com/##; s#\\.git$##')
fi
printf '%s\n' "$repo"
```

Current-project triage starts with:

```bash
gh issue list --repo "$repo" --state open --limit 50 \
  --json number,title,author,labels,createdAt,updatedAt,url
gh pr list --repo "$repo" --state open --limit 50 \
  --json number,title,author,isDraft,reviewDecision,mergeStateStatus,createdAt,updatedAt,url
```

Before acting on any issue or PR, read the latest comments. For small queues (about 10 open items or fewer), inspect all items. For larger queues, inspect the top priority slice.

```bash
gh issue view <n> --repo "$repo" \
  --json number,title,author,body,comments,labels,createdAt,updatedAt,url
gh pr view <n> --repo "$repo" \
  --json number,title,author,body,comments,files,commits,isDraft,reviewDecision,mergeStateStatus,statusCheckRollup,createdAt,updatedAt,url
gh pr diff <n> --repo "$repo" --patch
```

Only comment, close, merge, rerun, or patch with strong evidence.

## Item Evaluation

Classify each item:

- `bug`: require repro/log/failing test/current-main proof; identify root cause before recommending fix/merge.
- `feature`: require end-to-end test plan. State exactly what credential/access is missing before work can be considered complete.
- `dependency`: explain package group, major/minor risk, failing checks, runtime/engine changes.
- `security`: raise priority, require careful code-path proof, tests, and trust/context.
- `docs/internal`: lower risk, but explain user-visible relevance.

Judge:

- `Fit`: good / mixed / poor, with one reason.
- `Risk`: low / medium / high, with blast radius.
- `Proof`: current CI, local repro, failing test, live E2E, or missing proof.
- `Blocker`: first-time contributor CI approval, failing check, missing key, unclear direction, stale branch, conflicts.
- `Next`: approve CI, run test, request repro, split PR, patch locally, merge after green, close with proof, or defer.

## Triage Heuristics

Prioritize:

- PRs with green or nearly-green CI, recent maintainer activity, or low-risk dependency/docs/test changes.
- Issues that are reproducible, recently reported, or block releases.
- Security, release, auth, install, CI, and data-loss reports before cosmetic items.
- Bugs with clear current-main reproduction and narrow owner path.

Deprioritize:

- Old broad feature requests with no reproduction or owner signal.
- Feature/provider PRs that need unavailable API keys or accounts for end-to-end proof.
- Broad generated changes without a clear user problem, test plan, or trusted author signal.

## Output Shape

```text
Repo: owner/name
Source: gh list/view/diff/checks, local source/tests where inspected

Immediate:
- #123 PR: title
  What: one-line summary in plain words.
  Type/Fit/Risk: bug|feature|dependency; good|mixed|poor; low|medium|high because ...
  Trust: @login; acct date; repo/global activity; known/unknown/bot.
  Proof: CI/repro/test/e2e state.
  Blocker: none / missing key / first-time CI approval / failing lint / unclear direction.
  Next: exact maintainer action.

Needs judgment:
- #124 issue: ...

Defer/close:
- #125 issue: ...
```
