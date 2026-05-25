---
name: release-tweets
description: "Release tweets/social copy: draft from changelog, tags, npm/appcast, artifacts — X/Twitter announcements."
source: "https://github.com/steipete/agent-scripts"
attribution: "steipete/agent-scripts by Peter Steinberger"
---

# Release Tweets

> **Attribution:** Sourced from [steipete/agent-scripts](https://github.com/steipete/agent-scripts) by [Peter Steinberger](https://github.com/steipete).

Use when the user asks for a release tweet, launch tweet, X announcement, release thread, changelog-to-tweet rewrite, or social copy for a shipped version. This skill is about release copy, not cutting the release.

## Ground The Copy

- Verify the release target before writing confident copy:
  - Read the relevant `CHANGELOG.md` section or GitHub release notes.
  - Check the tag/release/npm/appcast/artifact state that applies to the project.
  - Distinguish `Unreleased`, beta/prerelease, stable, hotfix, and correction releases.
- Lead with user-visible wins: features, integrations, workflow improvements, install/update reliability, security fixes.
- Avoid leading with CI, coverage, validation, refactors, internal migrations, or release mechanics unless that is the actual story.
- If evidence is incomplete, say what is unverified and draft with softer wording.

## Launch Tweet Shape

- One standard tweet under 280 characters, with room for one URL.
- Typical format:
  - product + version
  - blank line
  - 3-4 compact emoji-led feature bullets
  - blank line
  - one short punchline
  - release/changelog URL
- Use emoji bullets by default. Pick clear, low-noise emoji that match the feature or product.
- Tone: high-signal, compact, confident, a little dry when earned. Not corporate.
- One joke max. Let the feature bullets do the work.
- Count final raw characters before presenting it as ready to post.

## Beta, Hotfix, Correction

- **Beta/prerelease**: make beta status explicit; avoid implying stable promotion.
- **Hotfix/correction**: be direct and accountable; state what slipped, what is fixed, and the new version; skip jokes unless the user asks for a lighter tone.

## Threads

- First agree on the generic launch tweet.
- Then write follow-ups one at a time. When the user says `next`, provide only the next reply.
- Each follow-up should focus on one feature or user workflow.
- Include a docs/release URL for the specific feature when available.
- Good follow-up length: 160-220 raw characters. Hard cap: 280.

## Quality Pass

Before final:

- Character count under 280 for each tweet.
- Exact version string and channel.
- Release URL included when requested or expected.
- No unverified claims.
- No more than 3-4 emoji-led bullets in the launch tweet.
- Concise language; trim filler before trimming facts.

## Examples

```text
ProductName 2.1.0

🚀 Feature one, brief description
🔧 Feature two, brief description
🐛 Bug fix summary

Short memorable punchline.
https://github.com/owner/repo/releases/tag/v2.1.0
```

```text
Hotfix 2.1.1 — fixes install issue from 2.1.0.

Upgrade via: npm install package@2.1.1
https://github.com/owner/repo/releases/tag/v2.1.1
```
