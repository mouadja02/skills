---
name: bulkpublish-social-publishing
description: Use when the user wants a finished social post drafted, scheduled, or published through BulkPublish, or asks to approve, reject, or retry a BulkPublish post — including a 403 APPROVAL_REQUIRED or an unconfirmed platform result.
version: "2.0.0"
license: MIT
source: "https://github.com/azeemkafridi/bulkpublish-ai-toolkit/tree/ca98104027b6fa2b085ad5cb6e2ab44d053a352c/skills"
attribution: "Procedure and parameter names are derived from azeemkafridi/bulkpublish-ai-toolkit (MIT), pinned at commit ca98104, cross-checked against azeemkafridi/bulkpublish-api at commit c31ba89 (MIT). See Sources."
---

# BulkPublish Social Publishing

## When to Use

- The user wants a finished post drafted, queued, or sent to connected social accounts through BulkPublish.
- A BulkPublish post is waiting on team approval and the user wants it approved or rejected.
- A publish attempt came back `403` with code `APPROVAL_REQUIRED`, or a destination ended `unconfirmed`.
- Do not use this skill for strategy, calendars, or copywriting that never touch BulkPublish — those belong to the strategy-only skills in this category.
- Do not use it for a single network's own API (for example posting to X directly).

**Related skill:** `marketing-and-growth/cs-social-media-manager` covers social strategy only and never publishes.

## Setup

BulkPublish needs an account with the destination channels already connected in the app. Two ways to reach it, both documented in the pinned toolkit README:

1. **Hosted, nothing stored on disk.** Add the remote MCP server `https://mcp.bulkpublish.com/mcp`. The hosted server signs in with OAuth 2.1 and exposes the 20-tool `core` profile. `approve_post` and `reject_post` are **not** in that profile, so approval over the hosted server goes through the REST calls below.
2. **Local stdio.** `npx -y @bulkpublish/mcp-server` with `BULKPUBLISH_API_KEY` set in the environment. The key is created under Settings, then Developer, at `https://app.bulkpublish.com/developer`, belongs to one organisation, and is sent as `Authorization: Bearer bp_...`. The local server defaults to the `full` profile, which includes `approve_post` and `reject_post`.

REST fallback for either setup: base URL `https://app.bulkpublish.com`, same bearer header. The OpenAPI description is `openapi.json` in `azeemkafridi/bulkpublish-api` at the pinned commit.

Before the first write, confirm the server answers `tools/list`. If `list_channels` is absent, stop and tell the user the server is not connected. Never paste the key into a prompt, a post, a log, or a file in the workspace.

## What you may and may not do

1. `create_post` defaults to `status: "draft"`. Drafting is the only write you may make before the user has seen the result.
2. Scheduling, publishing, approving, rejecting, retrying, and deleting are external side effects. Each one needs the user's explicit go-ahead for that specific post, stated after they have seen its exact text, channels, and time.
3. Never invent a channel id. `list_channels` returns `channelId`, `platform`, `accountName`, and `active`.
4. `publish_post` sends immediately and cannot be undone from here. `delete_post` on an already published post does not retract what went out.
5. Read the returned `status` and `approvalStatus` back to the user. A post with `approvalStatus: "pending"` has not been scheduled in any sense that will publish.

## Posts

`create_post` fields, from the toolkit's `schedule-post` reference:

```
content            post text; optional for a media-only post
channels           [{ channelId, platform }] — required, from list_channels
status             "draft" (default) or "scheduled"
scheduledAt        ISO 8601; required when status is "scheduled"
timezone           IANA zone, e.g. "Asia/Karachi"; defaults to UTC
mediaFileIds       [ids] from upload_media
platformContent    per-platform text overrides, e.g. {"x": "Short", "linkedin": "Longer"}
postTypeOverrides  per-platform type, e.g. {"instagram": "reel"}
postFormat         "post" (default), "video", "reel", "story", "carousel", "thread"
threadParts        [{ content, mediaFileIds }]; required for "thread", minimum 2
requestApproval    true holds a scheduled post for a teammate (approvalStatus "pending")
publishWhenApproved true publishes the moment it is approved, even after its time
```

The MCP field is `mediaFileIds`; the server sends it to the API as `mediaFiles`. `update_post` is `PUT /api/posts/{id}` and replaces `platformContent`, `platformSpecific`, and `postTypeOverrides` wholesale, so send the complete object for every platform you want to keep. `platform` on a channel entry is resolved server-side from the channel record.

Character limits enforced per platform: X 280, Bluesky 300, Threads 500, Mastodon 500, Pinterest 500, Snapchat 160, Google Business (`gmb`) 1,500, Discord 2,000, Instagram 2,200, TikTok 2,200, LinkedIn 3,000, Telegram 4,096, YouTube 5,000, Facebook 63,206, Tumblr 32,768. On X and Mastodon every URL counts as 23 characters. YouTube and TikTok need video; an image-only post must not include them. Instagram defaults to `feed_photo`, so set `postTypeOverrides` to `reel` or `feed_video` for video.

`upload_media` takes either a public `url` or an absolute `filePath`, not both, and returns the id you attach.

`get_queue_slot` reads only `timezone`, `position` (`"next"` or `"end"`), and `excludePostId`. It does not take a channel or a date, and returns `{ scheduledAt, dayLabel }`.

`list_channels` also returns `capabilities`: `canCreatePosts`, `canPublishPosts`, `canApprovePosts`. Check those before a write instead of discovering the refusal from a 403.

## Approval

`approvalStatus` is separate from `status`. It is `none` (default), `pending`, `approved`, or `rejected`. `pending` and `rejected` posts do not publish, however overdue. `requestApproval` only takes effect on a **scheduled** post: a draft stays `none`. For a member whose role lacks `post:publish` (a contributor), the server forces `requestApproval` on, so always trust the returned `approvalStatus` rather than the flag you sent.

Transitions:

- **Draft, no review.** `create_post` with `status: "draft"`. Nothing leaves the account. Show it, then either `publish_post` (postId) to send now, or `update_post` with `status: "scheduled"` and a `scheduledAt` to queue it. Moving a draft to scheduled is a `PUT /api/posts/{id}`, which is what `update_post` calls. `PATCH` only changes the recurring schedule and rejects every other field.
- **Scheduled, no review.** `create_post` with `status: "scheduled"` and `scheduledAt`. It publishes at that time only when `approvalStatus` is `none` or `approved`.
- **Scheduled, with review.** `create_post` with `status: "scheduled"`, `scheduledAt`, and `requestApproval: true`. It comes back `approvalStatus: "pending"` and waits. An authorised teammate (owner, admin, or approver) then calls `approve_post` — `POST /api/posts/{id}/approve` with an optional body. A conversational "yes" updates nothing on its own.
- **Publish on approval.** For "send it the moment it's approved", schedule at the current time with `requestApproval: true` and `publishWhenApproved: true`. Do not set `publishWhenApproved` when the user picked a specific time.
- **Approve.** `approve_post` releases the post: it publishes at its scheduled time, or immediately if that time passed less than 15 minutes ago. More than 15 minutes late, the optional `whenLate` decides: `"publish"` sends it now (status `publishing`), `"hold"` approves it but returns it as `draft` for a new time. Omit `whenLate` and the post's own `publishWhenApproved` decides. Tell the user whichever `status` came back; do not report a late hold as published.
- **Reject.** `reject_post` (postId, optional `reason` of at most 2,000 characters) — `POST /api/posts/{id}/reject`. The post returns to `draft` with `approvalStatus: "rejected"`.
- **Approve only the version reviewed.** Both calls take optional `ifUnmodifiedSince`: pass the `updatedAt` of the post as it was shown. If it changed, nothing is written and the call returns **409** with the current `updatedAt`. Reload with `get_post`, show it again, and review again.

`approve_post` answers **200** with the post, **400** when the post is not awaiting approval or `whenLate`/`ifUnmodifiedSince` is malformed, **403** when the role lacks `post:approve`, **404** when the post does not exist, **409** when it changed or somebody else already acted.

## Publishing and retries

`publish_post` returns **403** with code `APPROVAL_REQUIRED` for a role without `post:publish`; `retry_post` also answers 403 for such a role. Do not retry the same call. Submit the post for approval (`requestApproval: true` on a scheduled create or update) and tell the user a teammate has to approve it. An approver publishing a pending or rejected post approves it implicitly.

A destination can finish as `unconfirmed`: the request may have reached the network but the response was lost, so the post may already be live. It is never retried automatically. When a post has unconfirmed destinations and no failed ones, `retry_post` returns **400** with code `UNCONFIRMED_REQUIRES_REPUBLISH`. Ask the user to look at the account on that network first, and only pass `republish: true` after they confirm it is not already live — it can duplicate the post.

`retry_post` otherwise re-queues only the destinations in status `failed`. `partial` means some succeeded; it is neither success nor failure.

## Error recovery

| Result | What to do |
|---|---|
| **400** `CHANNEL_INACTIVE` | `error.channelIds` names disconnected channels. Ask the user to reconnect them or drop them. A draft may still name one. |
| **400** `UNCONFIRMED_REQUIRES_REPUBLISH` | Verify on the network before any republish. See above. |
| **400** validation | Fix the named field. An over-long thread part names its part number, platform, and limit. |
| **401** | The key or token is missing or revoked. Stop. Ask the user to check Settings, then Developer. |
| **403** `APPROVAL_REQUIRED` | Do not retry. Submit for approval. |
| **403** `FORBIDDEN` | The role cannot do this. Report it; do not look for another route. |
| **403** `FEATURE_DISABLED` / `PLATFORM_DISABLED` | Not on this plan, or switched off. `GET /api/platforms` reports current availability. |
| **403** `SEAT_LIMIT` | The member is beyond the plan's seats and read-only. Only the owner can fix it. |
| **404** | The post or channel is gone. Re-list instead of reusing the id. |
| **409** | Someone changed the post, or a publish is already running (`ALREADY_PUBLISHING`). Reload with `get_post`; never approve blind. |
| **422** quota exceeded | Stop and tell the user. Daily limits reset at midnight UTC. |

*Recommendation (not from the sources):* after a timeout or any other ambiguous failure on a write, check `get_post` or `list_posts` before creating the post again, so a retry does not duplicate it.

## Completion

You are done only when all of these hold:

- Every requested destination appears in the returned post with a `postPlatforms` status, and you have reported the post id, `status`, `approvalStatus`, `scheduledAt`, and any per-platform failure.
- A post meant to go out shows `approvalStatus` of `none` or `approved`. `pending` means it is waiting, and you say so.
- No destination is `unconfirmed` or `failed` unless the user has been told and chosen to stop.
- Nothing was published, retried, approved, or deleted without an explicit go-ahead given after the preview.

## Evaluations

Normal, difficult-edge, and should-not-activate prompts with deterministic assertions are in [evaluations](references/evaluations.md). They need no BulkPublish account and make no live calls.

## Sources

Sourced facts above come from these pinned files. Items marked *Recommendation* and the Completion checklist are repository recommendations, not BulkPublish documentation.

- `azeemkafridi/bulkpublish-ai-toolkit` @ `ca98104027b6fa2b085ad5cb6e2ab44d053a352c` (MIT) — `skills/using-bulkpublish/SKILL.md`, `skills/schedule-post/SKILL.md`, `README.md`
- `azeemkafridi/bulkpublish-api` @ `c31ba8919dbbf31feac1e4666ef4befbf6fcb3de` (MIT) — `mcp-server/src/index.ts` (`CORE_TOOLS`, `approve_post`, `reject_post`, media field mapping), `openapi.json` (`POST /api/posts`, `/approve`, `/publish`, `/retry`, `GET /api/channels`)
- Public pages checked the same day: `https://www.bulkpublish.com/integrations/mcp-server/` (hosted endpoint, OAuth 2.1, 20 operations, 15 networks) and `https://app.bulkpublish.com/docs` (interactive reference; the pinned `openapi.json` is the source for response codes).

Anything not stated in those sources is left out rather than guessed.
