---
name: clawsweeper-status
description: "ClawSweeper status: GitHub Actions workflow health, active workers, ops snapshot."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# ClawSweeper Status

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use when you need an ops snapshot of a GitHub Actions-driven automation (worker health, active jobs, recent activity).

## Output Contract

Report these sections concisely:

- **Workers**: active workflow count, queued/waiting count, active job estimate, active workflow groups.
- **Recently merged**: merged PR URLs plus one-line titles.
- **Recently reviewed**: review comment URLs plus one-line comment summary.
- **Recently commented**: other recent comment URLs plus one-line comment summary.
- **Recently closed**: closed issue/PR URLs plus one-line titles.

If a section has no rows, say `none found in window`.

## Efficient Data Sources

Use `gh` directly for bounded API calls:

```bash
# Active workflow runs
gh run list --repo <owner>/<repo> --json databaseId,name,status,conclusion,updatedAt --limit 20

# Jobs for a specific run
gh api repos/<owner>/<repo>/actions/runs/<run-id>/jobs --jq '.jobs[] | {name, status, conclusion}'

# Recent PR merges
gh pr list --repo <owner>/<repo> --state merged --limit 10 --json number,title,url,mergedAt

# Recent issue comments (for review/comment URLs)
gh api "repos/<owner>/<repo>/issues/comments?sort=updated&direction=desc&per_page=20" \
  --jq '.[] | {id, body: .body[:100], url: .html_url, user: .user.login}'

# Recent closed issues/PRs
gh issue list --repo <owner>/<repo> --state closed --limit 10 --json number,title,url,closedAt
gh pr list --repo <owner>/<repo> --state closed --limit 10 --json number,title,url,closedAt
```

## Interpretation

- Cancelled workflow runs are usually expected supersession when a newer event for the same item arrives.
- Count active jobs from in-progress/queued runs.
- Treat stale `gh run list` output cautiously; prefer direct API when numbers disagree.
- Use full GitHub URLs in the final answer.

## Notes

- Do not browse the web for these checks. Use `gh` directly.
- Replace `<owner>/<repo>` with the actual repository.
