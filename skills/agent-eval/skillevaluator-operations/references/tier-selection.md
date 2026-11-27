# Tier Selection and Live-Evaluation Safety

This reference applies to SkillEvaluator `1.2.1`. Run `skillevaluator <command> --help` for the installed release; older releases may lack current harness, backend, dataset-validation, report, or CI semantics.

## Select by claim

| Claim | Smallest useful command | Extra dependencies | What it does not prove |
| --- | --- | --- | --- |
| Basic authoring quality | `quality-check PATH` | none beyond base CLI | complete static safety or behavioral lift |
| Harness loader compatibility | `harness-check PATH --harness codex,hermes` | none beyond base CLI; needs >=1.0.0 | live activation or task success |
| Static publication gate | `tier1 PATH --no-llm` | scanners; may download them | overlap or behavioral lift |
| LLM rubric/security review | `tier1 PATH` or `rubric-eval PATH` | provider key and `llm` extra | live agent benefit |
| Intra-skill repetition | `tier2 PATH` | embeddings/provider | task improvement |
| Catalog overlap | `similarity-check SKILLS` plus `tier2 --catalog` | embeddings/provider and pinned catalog | behavioral equivalence |
| Baseline-versus-skill behavior | `tier3 evaluate PATH` | provider, agent, `tier3` extra, sandbox (`--backend harbor` default, or `nemo-gym`) | other models/harnesses not sampled |
| Combined pipeline | `validate PATH` | every selected tier dependency | skipped/advisory tiers unless report says otherwise |

## Permission and readiness gates

Ask before:

- installing or upgrading the CLI or extras;
- allowing `health-check`/`doctor` to download SkillSpector or Gitleaks;
- sending skill text, prompts, trajectories, or reports to a provider;
- incurring model or managed-sandbox spend;
- provisioning Docker or using experimental local containment;
- creating CI workflows, commits, PRs, or external report publications.

A provider key in the host environment is not permission to spend it. Do not place keys in skill files, runtime config, reports, shell history, or logs.

## Tier 1 details

A focused keyless quality run:

```bash
skillevaluator quality-check <skill-dir> --min-score 70 \
  -r cli -r json -o <report-dir>
```

A complete static run:

```bash
skillevaluator tier1 <skill-dir> --no-llm \
  -r cli,json,markdown,sarif,junit -o <report-dir>
```

`--no-llm` disables model-backed checks, not scanner requirements. Missing scanners make the result incomplete. `-r cli` alone intentionally writes no files.

## Tier 2 details

Pin the compared collection revision and catalog artifact:

```bash
skillevaluator similarity-check <skills-dir> \
  --threshold 0.75 --save-catalog <catalog.json>
skillevaluator tier2 <skill-dir> --catalog <catalog.json> \
  --threshold 0.80 --similarity-threshold 0.75 \
  -r cli,json -o <report-dir>
```

Do not equate semantic similarity with duplicate operational behavior. Inspect the matched sections and intended jobs.

## Tier 3 dataset gate

A valid evaluation suite includes:

- positive cases that should activate the skill;
- difficult or implicit cases that test the workflow rather than keywords;
- negative cases that should not activate;
- machine-checkable outcomes tied to the skill's claimed value;
- top-level `skill_name` and an `evals` array whose cases use `prompt`;
- `expected_skill` as a non-empty string for activation cases or `null` for negative cases;
- `assertions` and `expected_behavior` as lists of strings when present;
- no assertion that the baseline must read a skill it cannot access;
- frozen prompts and assertions before the first measured baseline.

Validate before spending:

```bash
skillevaluator tier3 validate <skill-dir> --strict --json
```

## Trial forecast

For `C` cases, `A` attempts, and `G` agents:

```text
agent runs = C × A × G × 2
```

The two arms are baseline and with-skill. Add judge calls, retries, setup probes, and provider-specific pricing separately. Example: 6 cases × 3 attempts × 2 agents × 2 arms = 72 agent runs, before judges.

## Isolation gate

Prefer Docker and synthetic repositories. Before a measured run:

1. Inspect bundled target scripts as untrusted code.
2. Remove production credentials and disable unrelated network access.
3. Use a disposable workspace unavailable to the real checkout where possible.
4. Record the agent, model, image/backend, resources, timeout, and concurrency.
5. Run a readiness probe without scoring it as evidence.
6. Execute and verify one scenario at a time unless process/filesystem isolation is proven.
7. After timeout, prove the child and descendants exited.
8. Fingerprint the real checkout after each scenario and stop on unexpected writes.

Local mode (`--env-mode local`) is experimental. Use it only for trusted skills with reviewed Bubblewrap/Seatbelt containment; never use it merely because Docker is unavailable.

## Smoke versus release evidence

A one-case run such as `--max-cases 1` can prove the pipeline starts. It cannot establish representative lift. Label it `smoke only`; do not publish its score as a release verdict.

For release evidence, record all selected cases and attempts, preserve failures and trajectories, and compare both arms under the same pinned configuration. Do not use `--skip-baseline` for a lift claim. With multiple attempts, report both pass@k and pass^k. Read the paired-case lift estimate, 95% bootstrap interval, and precision label from the generated statistics; do not fabricate an interval when `--stop-on-pass` leaves unequal attempt counts.
