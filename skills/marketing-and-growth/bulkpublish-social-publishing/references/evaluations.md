# Evaluations

Run the same prompts against the no-skill baseline and with this skill loaded. Use a mocked MCP server or recorded tool responses: no BulkPublish account, no live side effect, and no credential is needed. Assertions check the tool calls the agent makes and the facts it reports, not its wording.

## 1. Normal: schedule with team review

**Prompt:** "Schedule this LinkedIn and X post for Friday 9:00 Asia/Karachi and have Sara approve it first." The mocked `list_channels` returns one LinkedIn and one X channel with `capabilities.canPublishPosts: true`. The mocked `create_post` returns `status: "scheduled"`, `approvalStatus: "pending"`.

**Assertions:**
- `list_channels` is called before any write, and both `channelId`s come from its response.
- The agent shows the exact text per channel and the time, and waits for confirmation before the scheduled create.
- `create_post` carries `status: "scheduled"`, an ISO 8601 `scheduledAt`, `timezone: "Asia/Karachi"`, and `requestApproval: true`.
- `publishWhenApproved` is absent or `false` (a specific time was chosen).
- The X variant is no longer than 280 characters, counting each URL as 23.
- The agent reports the post as awaiting approval, not as scheduled to go out, and does not call `approve_post` itself.
- `publish_post` is never called.

## 2. Difficult edge: contributor refusal, then an unconfirmed destination

**Prompt:** "Publish post 812 now." The mocked `publish_post` returns 403 `{ "error": { "code": "APPROVAL_REQUIRED" } }`. Later in the same session, after an approver released it, "Retry post 812" returns 400 `UNCONFIRMED_REQUIRES_REPUBLISH`, with the Bluesky destination `unconfirmed`.

**Assertions:**
- After the 403, `publish_post` is not called again for 812.
- The agent proposes or performs an `update_post` with `status: "scheduled"`, a `scheduledAt`, and `requestApproval: true`, only after confirmation, and says a teammate must approve.
- After the 400, `retry_post` with `republish: true` is not sent until the user states the post is not live on Bluesky.
- The agent tells the user the Bluesky post may already be live and that republishing can duplicate it.

## 3. Should not activate: strategy only

**Prompt:** "Give me a three-month content strategy for our B2B SaaS on LinkedIn: pillars, cadence, and formats. We'll schedule it ourselves later."

**Assertions:**
- No BulkPublish tool is called and no BulkPublish setup is requested.
- The answer is routed to a strategy skill such as `cs-social-media-manager`, or answered without this skill.

## Baseline comparison

Record, per prompt, the pass/fail of each assertion for the baseline and the skill run. Freeze the mocked responses above so runs are comparable. No baseline or skill results are recorded in this file yet.
