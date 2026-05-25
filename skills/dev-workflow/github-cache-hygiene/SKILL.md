---
name: github-cache-hygiene
description: "GitHub quota/cache hygiene: answer reads from cache first, spend live API calls only for freshness or writes."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# GitHub Cache Hygiene

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Goal: answer common GitHub read questions from local cache first, then spend live GitHub API calls only where freshness or writes matter.

## Default Path

Use `gh` normally. Prefer these local/cached reads first:

```bash
gh search issues "<terms>" -R owner/repo --state open --json number,title,state,url,updatedAt,labels,author
gh search prs "<terms>" -R owner/repo --state open --json number,title,state,url,updatedAt,isDraft,author
gh issue list -R owner/repo --state open --author user --assignee user --label bug --json number,title,url
gh pr list -R owner/repo --state open --author user --label dependencies --json number,title,url
gh issue view 123 -R owner/repo --json number,title,state,body,comments,labels,url
gh pr view 123 -R owner/repo --json number,title,state,body,comments,labels,files,commits,statusCheckRollup,url
gh pr checks 123 -R owner/repo --json name,state,detailsUrl,workflow
gh run list -R owner/repo --branch branch-name --json databaseId,workflowName,status,conclusion,url
gh pr diff 123 -R owner/repo --patch
```

Use exact refs and narrow fields. Avoid broad loops like one `gh issue view` per result when a single `gh search` or `gh issue list --json ...` can answer the first-pass question.

For CI, avoid tight `gh run list` / `gh run view` polling loops. After a push or workflow dispatch, identify one exact run, then poll it with backoff. Fetch full logs only for failed jobs or when the user explicitly asks for logs.

## Freshness

Local answers are good for discovery, duplicate search, old thread review, author/label triage, and "is there likely already an issue/PR?" checks.

Use a live call when:

- writing, commenting, closing, merging, rerunning, or editing
- checking final current state before a maintainer action
- verifying CI status after a push
- the local result is missing or obviously stale
- the user asks for latest/live state

For PR review, prefer hydrating exact PR details once with `gh pr view --json` when you know you will inspect files, commits, checks, or run summaries repeatedly.

After a write, do one targeted readback, not a broad rescan.

## Agent Etiquette

Batch questions by repo and state. Reuse data already printed in the session. Back off CI polling; inspect logs only for failing runs or the exact run under review.
