# Cost estimation

Moved verbatim from SKILL.md so the entry file stays small. Axiom citations refer to the `axioms-*.md` files in this folder.

## Cost estimation

Designing and discussing the data model is the default, no-AWS path, and a user is often there to explore options — keys, GSIs, single- vs multi-table, projection tradeoffs — without yet wanting a dollar figure. **Do not run the calculator reflexively on every design turn.** Produce the monthly cost estimate when either is true: **(a)** the user asks what it costs (or for the cost report), or **(b)** the design is being finalized — they signal they're settling on it, taking it to a review, or otherwise want the numbers committed. Until then, stay in design discussion.

Skip the estimate entirely when no full design was produced — a single-query sizing, a hot-partition debugging thread, a pointed mechanics question. In those cases there is nothing to estimate.

When you *do* produce the estimate, three steps are not optional: (a) write `dynamodb_data_model.json`, (b) invoke `${SKILL_DIR}/scripts/calculate_costs.py`, (c) reference the generated `cost_report.md` in your summary. **Computing numbers inline without running the calculator is never a substitute** — not even for a "rough" or "realistic" figure, and not even to reconcile a headline number against a stated daily volume (for that, set `avg_rps` and let the calculator produce the expected-volume scenario — see below). The calculator enforces the pricing module that stays calibrated against live billing; doing the arithmetic by hand means the numbers drift silently and the user ships a quote they cannot defend.

The calculator is at `${SKILL_DIR}/scripts/calculate_costs.py`. The JSON schema it consumes is documented at `${SKILL_DIR}/references/cost-model-schema.md` — read that file the first time you produce a cost estimate.

The workflow:

1. **Serialize the design to `dynamodb_data_model.json`.** The calculator does not reinvent the design — it reads what you already produced. The access-pattern list you built (per Mechanics #2, #18) is a near-literal translation into the JSON's `access_patterns` array; the schema you built (per Data modeling #3, #7, Mechanics #4, #7) translates into `tables` and `gsis`. If a field the calculator wants is missing (most commonly `peak_rps` on a pattern), that is a gap in the design itself — close it by asking the user or by making a defensible assumption and labeling it as one, not by writing `0`.

   **When the user states an average or daily volume, set `avg_rps` on the pattern — do not hand-compute a "realistic" figure.** The headline is peak-sustained (every pattern at `peak_rps`, 24/7); a user who hears a large peak-sustained monthly figure for a 15K-orders/day workload needs the expected number too. Setting `avg_rps` (e.g. 15,000 orders/day ÷ 86,400 s ≈ 0.17 rps average, vs a 600 rps Black-Friday peak) makes the calculator emit a second **Expected Monthly Cost** headline at that average rate. This is the *only* sanctioned way to produce a realistic-volume number — reconciling the peak headline against a daily volume with mental arithmetic is exactly the inline-arithmetic the rule above forbids.

2. **Run the calculator.** Write the JSON to a workspace path of your choosing and invoke:

   ```bash
   python3 ${SKILL_DIR}/scripts/calculate_costs.py --model /path/to/dynamodb_data_model.json --output /path/to/cost_report.md
   ```

   The JSON is an intermediate artifact. You do not need to present it to the user unless they ask.

3. **Surface the cost report.** Hand back `cost_report.md` — either inline (if short) or as a file pointer. Highlight the top drivers the report surfaces (the "cost patterns sorted descending" table), and call out the assumptions you baked in (RPS numbers you estimated, retention you assumed, consistency choices). The disclaimer at the top of the report is part of the artifact — do not strip it.

4. **Use the cost report to challenge the design, not just to report the number.** A cost estimate is diagnostic. If one pattern dominates the bill — the classic case is a high-frequency write like a GPS ping — that is a modeling signal, not just a line item: revisit the aggregate choice (Mechanics #1), the projection shape (Mechanics #7), whether a sparse-GSI-on-transition would cut amplification (Mechanics #6), or whether the pattern belongs outside DynamoDB entirely (Integration #8). Propose the alternative and re-run the calculator on the revised model. This is the main value of having the calculator bundled: the feedback loop from "here's the design" → "here's the bill" → "here's the cheaper design" becomes a turn or two, not a separate exercise.

The calculator models request and storage cost only. It does not model Streams read/write costs, PITR, backup, DAX, or data transfer. If those line items are likely material for the workload, call that out alongside the estimate so the user knows what the number excludes. **Storage is priced at the full public rate — the 25 GB free tier is not assumed** (it is account-wide and often already used), so never tell the user "storage is free." Set a write pattern's `retention_days` to size its stored data; the calculator honors it. The storage figure is a **bounded-retention snapshot** at that `retention_days` — for a table with **no TTL / "kept forever" data**, real storage keeps growing past the snapshot, so do **not** reframe a steady-state storage number as "after N years": either state the retention window the number assumes, or note that a no-TTL table accumulates without bound.

**Name the artifacts in your final response. Do not let the tool calls disappear into prose.** The user reads your natural-language output, not your shell history. After you run `calculate_costs.py`, your response must name (a) the JSON file you wrote (`dynamodb_data_model.json`), (b) the script you invoked (`${SKILL_DIR}/scripts/calculate_costs.py`), and (c) the report file it produced (`cost_report.md`). A response that shows cost numbers but does not name the artifact files reads as if you computed them by hand — the workflow evidence has to be in the prose, not just the tool trace.
