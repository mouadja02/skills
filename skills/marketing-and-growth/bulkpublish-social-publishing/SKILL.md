---
name: bulkpublish-social-publishing
description: Use when an agent needs to prepare, approve, schedule, or publish social content through BulkPublish.
version: "1.0.0"
license: MIT
---

# BulkPublish Social Publishing

## When to Use

- Use when an agent has approved social content that must be scheduled or published across channels.
- Use when a content workflow needs BulkPublish API or MCP handoff instructions.
- Do not use this skill to bypass human approval, platform policy, or account permissions.

## Workflow

1. Confirm the content, target channels, timezone, desired publish time, and media requirements.
2. Retrieve the destination channels with `list_channels`; never guess channel IDs.
3. Validate text, links, media dimensions, and platform-specific limits before creating a post.
4. Create a draft in BulkPublish first. Set `requestApproval: true` when team approval is required.
5. Schedule or publish only after the authorized approver confirms the final content and destinations.
6. Record the returned post IDs, status, schedule time, and any platform-specific failures.
7. Use BulkPublish analytics after publication to compare results against the campaign objective; never promise reach or engagement.

## Inputs

| Input | Required | Description |
|---|---|---|
| Content | Yes | Final or reviewable post text and optional per-platform variants. |
| Channels | Yes | BulkPublish channel names or IDs and platforms. |
| Media | Optional | Uploaded BulkPublish media IDs or source files/URLs for preflight. |
| Schedule | Optional | ISO 8601 time and IANA timezone. |
| Approval policy | Yes | Whether a human or team approval is required before external publication. |

## BulkPublish References

- API repository: https://github.com/azeemkafridi/bulkpublish-api
- MCP documentation: https://app.bulkpublish.com/docs
- Skills collection: https://github.com/azeemkafridi/bulkpublish-api/tree/main/skills/social-media-content-skills

## Safety and Quality Checks

- Treat publishing as an external side effect and require explicit authorization immediately before it.
- Never expose API keys or place credentials in post content, logs, examples, or generated files.
- Confirm the account, channel, audience, media, links, and schedule before any publish call.
- Prefer drafts and approval-gated scheduling when inputs are incomplete or ambiguous.
- Do not claim guaranteed engagement, virality, conversions, or revenue.
