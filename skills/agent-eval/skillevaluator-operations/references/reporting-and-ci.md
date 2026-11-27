# Reporting and CI

## Evidence record

For every run preserve:

- SkillEvaluator version and package source/hash when available;
- target path, source repository, and exact revision;
- exact command and exit code;
- selected tiers/checks, thresholds, models, agents, attempts, and sandbox;
- report paths and checksums;
- start/end time and incomplete/skipped reasons;
- approval reference for downloads, provider calls, live runs, and external writes.

## Interpret JSON conservatively

From `skillevaluator-output-<timestamp>.json` or a Tier 1 report, read rather than infer:

| Field | Interpretation |
| --- | --- |
| `overall_passed`, `overall_status` | command gate result: passed, failed, or incomplete |
| `publication_status` | publication decision: pass, neutral, fail, or incomplete |
| `quality_summary[].overall_score`, `.grade` | quality score and grade |
| `severity_counts` | critical/high/medium/low finding totals |
| `finding_groups[]` | deduplicated findings with `finding_id` |
| `tier3.run_id` | live-run identity |
| `<agent>/statistics.json` paired lift fields | advisory paired-case estimate, 95% bootstrap interval, and precision; absent when arm attempt counts are unequal |
| pass@k / pass^k | probability of at least one pass / probability every attempt passes; report both when `k > 1` |

`overall_passed: true` can coexist with advisory or skipped coverage. Claim publishable only when the required policy is satisfied and `publication_status` is `pass`.

## Final report template

```markdown
# Skill evaluation — <target@revision>

## Decision
- Status: PASS | FAIL | INCOMPLETE | ADVISORY ONLY
- Claim tested: <exact claim>
- SkillEvaluator: <version>

## Evidence
| Tier/check | Command | Exit | Report | Result |
| --- | --- | ---: | --- | --- |
| Quality | `...` | 0 | `...json` | 84.5/B |
| Harness | `...` | 0 | console/JSON | 6/6 load |
| Tier 3 | not run | — | — | unproven |

## Behavioral comparison
- Cases/attempts/agents: <counts>
- Baseline: <reported value or not run>
- With skill: <reported value or not run>
- Lift: <reported value or not established>
- Paired lift interval/precision: <reported values, inconclusive if interval crosses zero, or unavailable with reason>
- pass@k / pass^k: <reported values or not run>

## Findings
- <severity, finding ID, file, fix>

## Limitations
- <skipped tier, unavailable dependency, smoke-only scope, or model/harness not sampled>

## Reproduce
<exact pinned commands>
```

## CI progression

Start advisory, then gate only after a stable baseline:

1. Run Tier 1 reports without blocking.
2. Fix or explicitly waive reviewed findings.
3. Gate deterministic Tier 1 at a pinned CLI version and policy.
4. Add Tier 2 with a masked provider secret and pinned catalog.
5. Add Tier 3 as an advisory isolated job.
6. Make Tier 3 blocking only after variance, cost, and false-failure rates are understood.

Keyless Tier 1 pattern:

```bash
skillevaluator validate <skills-dir> --profile default --tiers 1 -c \
  -r json,markdown,sarif,junit -o reports --min-score 70
```

CI must pin the package version, Python version, policy file, target paths, and report retention. Keep provider keys in CI secrets and never expose untrusted fork workflows to privileged secrets.

## Failure semantics

- Unknown command/flag: stop, record installed version, and consult `--help`; do not substitute a guessed command.
- Missing scanner: `INCOMPLETE`, not pass.
- Provider unavailable: model-backed tier `not run` or `incomplete`, not zero.
- Sandbox or agent startup failure: no measured Tier 3 run.
- Timeout: preserve partial artifacts, prove processes exited, and mark affected cases not run.
- Smoke run: readiness evidence only.
- Report parse failure: do not replace structured values with console impressions.
- CI workflow creation, PRs, comments, and report publication are external writes and retain their normal approval gates.
