---
name: skillevaluator-operations
description: >-
  Use when validating, comparing, or release-gating agent skills with NVIDIA SkillEvaluator — choose a static, overlap, harness, or live A/B tier; forecast dependencies and cost; run with explicit isolation and permission gates; and report exact evidence without overstating skipped tiers.
version: "1.1.0"
license: Apache-2.0
source: "https://github.com/NVIDIA/SkillEvaluator/tree/v1.0.1/skills/skillevaluator"
attribution: "NVIDIA/SkillEvaluator by NVIDIA Corporation"
compatibility: "Python 3.12-3.14; skillevaluator 1.0.1 (`harness-check` requires >=1.0.0). Tier 3 additionally requires a supported agent, provider access, and an isolated runtime."
---

> **Attribution:** Adapted from [NVIDIA/SkillEvaluator](https://github.com/NVIDIA/SkillEvaluator/tree/v1.0.1/skills/skillevaluator) by NVIDIA Corporation, licensed Apache-2.0. Modified for this collection.

# SkillEvaluator Operations

Choose the smallest evaluation tier that proves the requested claim, run it only when its dependencies and side effects are understood, and distinguish measured evidence from missing coverage. This workflow targets SkillEvaluator `1.0.1`; check `skillevaluator <command> --help` before relying on a flag with another release. `harness-check`, the Tier 3 `--backend` selector, and the CI bundle arrived in the 1.0 series, so `0.9.0` cannot run the harness step at all — upgrade instead of substituting a guessed command.

## When to Use

- Validate a `SKILL.md` for structure, quality, security, PII, licensing, or script integrity.
- Check whether a skill loads across Claude Code, Codex, Copilot CLI, Hermes, OpenClaw, and OpenCode.
- Find repeated guidance or semantic overlap within a skill catalog.
- Compare agent behavior with and without a skill, including pass@k and Skill Lift.
- Add evidence-producing skill gates to CI or interpret SkillEvaluator reports and exit codes.

Do not activate for ordinary application-code review, generic LLM benchmarking, or writing the target skill's domain content. Use `skill-smell-audit` for a dependency-free authoring review and `eval-driven-dev` for Python LLM applications.

## Prerequisites

1. Confirm the exact target path and requested claim.
2. Require Python `>=3.12,<3.15` (the package declares the same bound) and pin the CLI for reproducibility:
   ```bash
   uv tool install 'skillevaluator==1.0.1'
   skillevaluator --version
   ```
   Installation is a networked write: inspect the package/release and obtain approval when the environment requires it. The `1.0.1` PyPI wheel and sdist publish no provenance attestation (verified 2026-11-21); record that limitation. Do not assume a version-specific flag or subcommand exists — confirm it from the installed `--help` or the package's own command registry.
3. Never print, echo, commit, or place provider keys in evaluation configuration. Keys stay in the host environment.
4. Treat the target skill and its scripts as untrusted. Read scripts before any runtime evaluation; use synthetic inputs and no production credentials.
5. Read [references/tier-selection.md](references/tier-selection.md) before selecting a tier. Read [references/reporting-and-ci.md](references/reporting-and-ci.md) before publishing a verdict or CI gate.

## Workflow

### 1. Freeze the claim and evidence contract

Write down:

- target skill path and source revision;
- claim to prove: loadability, static safety, overlap, or behavioral lift;
- target harnesses/models and pass threshold;
- allowed network, scanner download, provider spend, and sandbox;
- expected report formats and output directory;
- explicitly unproven tiers.

Do not run `validate` merely because it is comprehensive. It may invoke scanners, embeddings, provider calls, and live agents that the user did not request.

### 2. Inspect readiness without side effects

Confirm `SKILL.md` exists and frontmatter `name` matches its folder. Then inspect local availability:

```bash
skillevaluator --version
skillevaluator quality-check --help
skillevaluator harness-check --help
```

`health-check` and `doctor` can download pinned scanners or probe models depending on flags. Forecast those actions first and obtain approval for downloads, provider calls, Docker provisioning, or other writes.

On a release below `1.0.0`, `harness-check --help` does not resolve a command and the Tier 1 report has no harness section. That is a version gap, not a usage error: upgrade the CLI rather than mapping the check onto `quality-check`.

### 3. Run the cheapest sufficient tier

**Keyless quality only:**

```bash
skillevaluator quality-check <skill-dir> -r cli -r json -o <report-dir>
```

This produces a deterministic quality score, not complete publication evidence.

**Cross-harness loader prediction:**

```bash
skillevaluator harness-check <skill-dir> --harness codex,hermes -v
skillevaluator harness-check <skill-dir> --harness claude-code,codex,copilot-cli,hermes,openclaw,opencode --json
```

This uses the versioned profiles shipped with the wheel (Claude Code, Codex, Copilot CLI, Hermes, OpenClaw, OpenCode). It is static and advisory under the default policy: it predicts discovery-path, frontmatter, size, and invocation problems; it does not prove live activation or task improvement.

**Full static Tier 1 without LLM checks:**

```bash
skillevaluator tier1 <skill-dir> --no-llm -r cli,json,markdown,sarif,junit -o <report-dir>
```

Tier 1 still needs its scanners. If a scanner is missing or cannot run, report `INCOMPLETE`; `--no-llm` does not make scanner coverage optional.

**Overlap / Tier 2:**

```bash
skillevaluator similarity-check <skills-dir> --save-catalog <catalog.json>
skillevaluator tier2 <skill-dir> --catalog <catalog.json> -r cli,json -o <report-dir>
```

This requires embeddings/provider access. Record the compared catalog revision and thresholds.

**Live A/B / Tier 3:** follow the isolation and trial plan in the reference. A smoke run with `--max-cases 1` is readiness evidence only, never publication evidence.

### 4. Validate the evaluation dataset before live runs

Require reviewed positive, difficult/implicit, and negative cases. Validate mechanically:

```bash
skillevaluator tier3 validate <skill-dir> --strict --json
```

Freeze prompts, assertions, agent/model versions, attempts, concurrency, timeout, and pass threshold before the baseline. Do not add assertions after seeing results.

### 5. Forecast Tier 3 cost and isolation

Compute and report:

```text
agent runs = cases × attempts × agents × 2
```

The factor `2` is baseline plus with-skill. Add judge/provider calls separately. Obtain approval for the exact plan, provider use, and sandbox. Default to Docker; local mode is experimental and appropriate only for trusted skills under reviewed Bubblewrap/Seatbelt containment.

Name the execution backend explicitly. `1.0.1` accepts `--backend harbor` (default) or `--backend nemo-gym` once NeMo Gym is configured; the backends differ in agent harness, grading, and sandbox, so record which one produced a run and never compare results collected under different backends.

### 6. Execute and preserve evidence

Run one scenario at a time when containment is not independently proven. Verify child processes exited and fingerprint the project after each scenario. Example:

```bash
skillevaluator tier3 evaluate <skill-dir> \
  -a codex --env-mode docker --n-attempts 3 \
  --results-dir <results-dir> --harbor-keep-jobs
```

Add `--backend nemo-gym` only when that backend is already installed and reviewed; keep the default `harbor` otherwise.

Never use `--skip-baseline` for a lift claim. Use `--skip-with-skill` only for a clearly labelled calibration baseline.

### 7. Interpret reports, not console impressions

Capture the exact command, exit code, CLI version, report path, and source revision. Read JSON fields and publication semantics from the reporting reference. A successful process does not prove every tier passed; an advisory or skipped tier remains unproven.

### 8. Produce a truthful decision

Report:

- exact commands and exit codes;
- per-tier status, score, grade, and top findings from reports;
- baseline, with-skill, lift, attempts, and case coverage for Tier 3;
- output paths and checksums when artifacts are handed off;
- skipped/incomplete tiers and why;
- release decision: pass, fail, incomplete, or advisory-only;
- rerun command pinned to the same target revision and configuration.

## Verification Scenarios

1. **Normal:** For a synthetic skill, choose keyless quality plus harness checks; report their exact exit codes and explain why this does not prove safety or lift.
2. **Difficult:** Given positive, implicit, and negative cases, forecast Tier 3 trials, require provider/sandbox approval, run at most an approved isolated smoke, and label smoke evidence separately from release evidence.
3. **Should not activate:** For ordinary application code review or a generic model benchmark, route elsewhere and do not install or invoke SkillEvaluator.

## Completion Gate

- The chosen command matches the claim and installed version.
- Every dependency, download, provider call, and sandbox side effect was forecast and approved where required.
- Reports were parsed from preserved artifacts; no score or status was inferred.
- Tier 3 used frozen cases and an isolated baseline/with-skill comparison, or is explicitly `not run`.
- The final verdict names all unproven tiers and can be reproduced from the recorded revision and commands.
