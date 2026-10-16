# Design interview: per-entity operational config and attribute walkthrough

Moved verbatim from SKILL.md so the entry file stays small. Run both parts of this interview before proposing table boundaries or estimating cost. Axiom citations refer to the `axioms-*.md` files in this folder.

## Per-entity operational-config inputs

> **This interview is required before proposing any table boundary.** Producing a full multi-table design first and then backfilling "here are the assumptions I made" is a workflow violation, not a shortcut. The per-entity questions below drive the table-splitting decision via Data modeling #3; when the answers are agent-assumed rather than user-stated, the signal fires spuriously and the design ends up over-fragmented (or under-fragmented if the agent guessed "no divergence" to keep things simple). Ask first, then design.

Before grouping entities into tables, gather operational-config requirements from the user per entity (or per logical aggregate — a parent and its tightly-bound children can share one answer set). Do not assume these defaults silently, because Data modeling #3 uses operational-config divergence as a signal to split tables — if the divergence is *agent-assumed* rather than *user-stated*, the signal fires spuriously and the design ends up over-fragmented.

For each entity, ask:

- **Backup and recovery granularity.** Does this entity need PITR? If so, what retention (default 35 days, can be shorter)? Would this entity ever be restored independently of other entities, or always together with them? (Independent-restore requirements force table separation per Data modeling #5.)
- **Streams consumers.** Does any downstream system need change events for this entity — search indexing, analytics export, notifications, audit, CDC? Which stream view type (`NEW_AND_OLD_IMAGES` is the default per Integration #3)? A "no" here is a positive answer: no Streams consumer means Streams can stay disabled, which is cheaper and simpler.
- **Capacity mode.** Does this workload's shape justify provisioned (sustained, predictable traffic over months, per Mechanics #19), or does on-demand remain the default? "Unknown" means on-demand.
- **TTL.** Is there a per-item expiration attribute the application will set? If yes, the attribute is a Unix epoch second (per Patterns #3). If no, TTL stays off and items persist until deleted.
- **Encryption and IAM scope.** Any non-default requirement — customer-managed KMS key, specific IAM boundary, cross-account resource policy? Default is AWS-owned KMS and standard IAM; divergence is an explicit answer.

Treat these as design inputs on par with RPS. A missing answer is a gap to close, not a value to guess. If the user says "same across all entities," record that and **do not** treat the entities as operationally divergent — co-location by Data modeling #1 is then unobstructed. If the user states real divergence, Data modeling #3 fires on real divergence and the tables split.

## Per-entity attribute walkthrough (drives item size)

Item size is the second-largest driver of the cost estimate after RPS, and it's the place the estimate silently drifts worst. A Query declared as `20 items × 1,536 B` but really returning `20 × 512 B` triples the modeled cost against reality. Mechanics #2 says unknown RPS is a design gap; the same discipline applies to item size — an ungrounded guess for `estimated_item_size_bytes` is a design gap, not a safe default.

For each entity, before settling on a number, **walk the attribute list with the user**. Asking first is the preferred path; proceeding from inferred attributes is the fallback. Either way, the user has to see and sign off on the per-attribute breakdown before it becomes an input to the cost estimate — a silent fill-in is what makes item sizes drift 2–10×.

1. Propose an attribute list grounded in the domain. For a Waypoint, that's `waypoint_id`, `courier_id`, `lat`, `lng`, `recorded_at`. For a Contract, it's `firm_id`, `contract_id`, `title`, `status`, `body`, `created_by`, `created_at`, `updated_at`.
2. Per attribute, estimate bytes using these starting points:
   - IDs and short strings (ULIDs, UUIDs, slugs, enum values): **~40 B** each. The generic `S=100` heuristic in `cost-model-schema.md` is conservative for the free-tier storage path; for per-item size estimation, use realistic values.
   - Titles, display names, short descriptions: **100–300 B**.
   - Long-form content (contract body, message body, serialized JSON aggregates): ask the user explicitly. Do not guess 4 KB or 50 KB without confirmation.
   - Numeric attributes: **~8 B**.
   - Timestamps as ISO strings: **~25 B**. As epoch numbers: **~8 B**. (Mechanics #11.)
   - Boolean: **~1 B**. Map/List: **~200 B** per instance as a rough default, but ask if the user is storing a big blob inside a Map.
3. Ask the corrections the user will know and you won't: "Does this item carry any denormalized parent data per Mechanics #10?" "Is there a free-text field whose length varies widely?" "Are you storing the full document or a summary?" Update the estimates from the answers.
4. Sum the per-attribute estimates to derive the entity's `estimated_item_size_bytes`. For a Query that projects a subset (INCLUDE / KEYS_ONLY, or application-side projection), use a smaller number for the access-pattern's `estimated_item_size_bytes` — the bytes billed by DynamoDB are bytes actually read from the projected view, not the full item.
5. If the user is uncertain on a specific attribute, label that attribute as an assumption in the artifact (same discipline as unknown RPS). Do not silently pick a number.
6. **Surface the full list in your response — always, regardless of whether this is an interactive conversation or a one-shot prompt.** Emit a compact markdown table per entity with columns `attribute | type | bytes | source (user or guess)`. This is a reply-shape requirement, not a dialog gate. In one-shot settings where there will be no follow-up turn, the table still goes in the response so the user sees exactly what you assumed — the call-out is how they catch a 3× overshoot on a body field before it contaminates every cost number downstream. Label every uncertain estimate "guess" explicitly; do not smuggle a guess in as a user-supplied number. Explicitly invite correction: "These are my guesses where noted — please correct any that are wrong." Even when the user said "just pick reasonable values and go," emit the table.

Calibration: for the reference Contracts-app example in `cost-model-schema.md`, `Contract` is ~2 KB (not 50 KB — the 50 KB value is the worst-case body size, not the typical), and `Clause` is ~512 B. If a declared `estimated_item_size_bytes` is more than 2× the sum of the named attributes and the user hasn't explained the gap, you're guessing — revisit.

A run that skips this walkthrough can drift by 2–10× on individual patterns. The live-validation step (below) will surface that drift, but you shouldn't need live validation to get the cost estimate in the right order of magnitude.
