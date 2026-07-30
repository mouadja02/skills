# Evaluation Prompts

Run all prompts against redacted, synthetic fixtures. A pass requires the helper's observable output, not words found in `SKILL.md`.

## Normal

**Prompt:** “Validate this OTLP-normalized GenAI chat span before we promote the collector change. Content capture is disabled; input tokens include cache-read tokens.”

```bash
python3 scripts/validate_genai.py --input normal.json
```

**Assertions:** exit 0; `status=pass`; no error findings; profile is reported.

## Difficult edge

**Prompt:** “Our upgrade emits the old provider attribute and legacy inference event, records prompt content without an opt-in, and reports fewer total input tokens than cache subtotals. Produce a migration gate; do not rewrite the telemetry.”

```bash
python3 scripts/validate_genai.py --input edge.json
```

**Assertions:** exit 1; codes include `legacy_attribute`, `legacy_event`, `content_without_opt_in`, and `input_token_total_too_small`; no input file is modified.

## Should not activate

**Prompt:** “Tune this PostgreSQL query span; it has only `db.*` attributes.”

```bash
python3 scripts/validate_genai.py --input should-not-activate.json
```

**Assertions:** exit 0; `status=not_applicable`; no GenAI migration advice is emitted. Use a database tracing skill instead.
