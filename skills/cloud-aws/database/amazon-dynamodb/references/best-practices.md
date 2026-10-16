# Operational best practices

Moved verbatim from SKILL.md so the entry file stays small. Axiom citations refer to the `axioms-*.md` files in this folder.

## Best practices

These are recommended defaults, not axioms. They do not shape the design; they are operational safeguards that should be enabled unless a specific reason argues against them. An agent producing a design should turn each of these on unless the justification for disabling is explicit in the artifacts.

1. **Enable deletion protection on every table.** DynamoDB's deletion-protection flag blocks `DeleteTable` at the service boundary until it is explicitly disabled. It costs nothing, has no performance impact, and prevents an entire class of incidents — an IaC misconfiguration, a copy-paste command, a stack tear-down that should have been scoped — from destroying a production table. The one-step disable is cheap when deliberate deletion is genuinely intended; the protection should be on everywhere else.

    Two important details people miss:

    - **Deletion protection defaults to FALSE.** New tables are created without it unless you set `--deletion-protection-enabled` on `create-table` (or the equivalent property in CloudFormation/CDK or any third-party IaC tool). This is why it is so commonly absent on tables that predate the feature or were created without deliberate thought — you have to explicitly turn it on.
    - **Service-boundary protection is not redundant with IaC guards.** CDK `RemovalPolicy.RETAIN`, a third-party IaC tool's prevent-destroy / retain-on-delete guard, and similar mechanisms only protect the IaC path — a direct `aws dynamodb delete-table` CLI call, a different IaC state file targeting the same resource, or a rogue script all bypass them. Deletion protection lives on the table itself at the service boundary and catches every destruction path. Use both together; do not treat IaC guards as sufficient on their own.

2. **Enable point-in-time recovery (PITR) on every table.** PITR provides continuous backup with 35-day retention and per-second restore granularity. Cost is a fraction of storage cost, and the day it is needed — accidental deletion, a bad migration, a logic bug that wrote corrupted values — it is the only thing that recovers the data. Disable PITR only on ephemeral tables whose contents can be rebuilt from another source (idempotency caches, dedupe stores with TTL). PITR divergence across tables is also a modeling signal per Data modeling #3.

3. **Make the table observable — alarms and an audit trail for production tables.** A table with no monitoring fails silently; the first sign of throttling or a runaway cost is often a customer complaint or the monthly bill. For every production table, recommend:

    - **CloudWatch alarms** on `ThrottledRequests`, `SystemErrors`, and `UserErrors` (and, on provisioned tables, on consumed-vs-provisioned capacity). At minimum a starter alarm on `ThrottledRequests > 0` sustained — that is the earliest signal of a hot partition or under-provisioning, and it ties directly to the Mechanics #3 ceilings.
    - **CloudTrail data-event logging** for tables holding sensitive or regulated data, so item-level reads and writes are auditable. CloudTrail captures DynamoDB *management* events by default; item-level (data) events are opt-in per table and are what an audit or incident investigation actually needs. When the audit/operational logs themselves hold sensitive data, **encrypt the CloudWatch Logs log group (and the CloudTrail trail's S3 bucket) with an AWS KMS customer-managed key** so the logged data is protected at rest, not just the source table.

    These are operational safeguards, not design inputs — but because this skill's guidance is replicated across many customer environments, surfacing them is part of a defensible design rather than an afterthought.
