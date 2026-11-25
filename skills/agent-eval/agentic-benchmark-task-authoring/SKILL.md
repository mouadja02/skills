---
name: agentic-benchmark-task-authoring
description: Author isolated, verifier-hardened agent benchmark tasks.
version: "1.0.0"
author: Mouad Jaouhari, Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [evaluation, benchmark, agent, verifier, reproducibility]
    category: agent-eval
    related_skills: [harness-benchmarking, eval-driven-dev, agent-trajectory-diagnostics]
---

# Agentic Benchmark Task Authoring Skill

Turn a recurring operational workflow into an **isolated, executable agent task** that separates those who can do the work from those who can shortcut it. The deliverable is a task package plus control evidence — not a prompt, not a rubric, and not a description of a benchmark.

## When to Use

- A recurring workflow has an observable artifact (file, diff, table, report) and you need a repeatable way to measure whether an agent can produce it.
- An existing benchmark cannot represent your environment, data contract, or failure mode without a custom task.
- A task already exists but a no-op, shortcut, or near-miss agent scores as high as the reference solution.
- You must hand a task to another team, a model evaluation, or a public leaderboard with reproducible evidence.

Do **not** activate for subjective quality grading with no executable artifact (tone, helpfulness, style) — use a rubric or judge workflow such as `eval-driven-dev`. Do not activate for a one-off prompt comparison, ordinary application unit tests, or running an existing benchmark. Task authoring is only justified when a *new isolated task with a verifiable output* is the deliverable.

## Prerequisites

- A concrete workflow: inputs, the artifact the work produces, and the environment it runs in.
- A task runner that supports the package format (Harbor 0.25.x or any runner implementing the same directory contract), plus a sandbox backend such as Docker.
- `python3` 3.11+ for [`scripts/verify_task_package.py`](scripts/verify_task_package.py) (uses `tomllib`).
- Redistribution rights for every fixture. Default to synthetic data; never publish customer or licensed records.

## How to Run

1. Read [`references/task-package-contract.md`](references/task-package-contract.md) for the directory layout, `task.toml` fields, and the verifier trust boundary.
2. Read [`references/control-and-rollout-matrix.md`](references/control-and-rollout-matrix.md) for the five control classes and rollout evidence.
3. Copy [`templates/task.toml`](templates/task.toml), [`templates/instruction.md`](templates/instruction.md), and [`templates/test.sh`](templates/test.sh) into the new task directory and adapt them.
4. Follow the procedure below, then run the validator:
   `python3 scripts/verify_task_package.py <task-dir> --rollouts <rollouts.json> --json`
5. Publish only when the validator reports zero blocking findings and every control behaves as declared.

## Quick Reference

| Situation | Decision |
|---|---|
| Output is a file the verifier can read | Authoring is viable; declare it in `artifacts` |
| Output is subjective prose quality | Do not author a task; use a rubric or judge workflow |
| Verifier runs in the agent container | Harden: set `verifier.environment_mode = "separate"` |
| Verifier needs network | Allowlist exact hosts in `[verifier.environment]`; never leave the `public` default |
| Oracle and no-op both score 1 | Verifier is existence-only; assert content and structure |
| Instruction names `tests/` or `solution/` paths | Leakage: rewrite the instruction around the observable contract |
| Identical inputs give different rewards | Flaky verifier; fix determinism before publishing |
| One rollout per control | Insufficient; require repeated rollouts with identical outcomes |

## Procedure

1. **State the claim.** Write one sentence: the capability measured, the artifact produced, and the non-goals. If the artifact is not machine-inspectable, stop.
2. **Freeze the environment.** Pin base image tags and dependency versions in `environment/Dockerfile`. Set `environment.network_mode` to `no-network` unless the workflow genuinely needs a pinned host; then use `allowlist` with exact hosts.
3. **Write the instruction as a contract.** Describe inputs, the exact output path, and the output schema. Never mention `tests/`, `solution/`, reward paths, or expected values. The instruction must be solvable from the environment plus public documentation.
4. **Write the reference solution.** `solution/solve.sh` must be non-interactive, idempotent, and executable. It defines solvability: if the oracle scores below 1, the task is broken, not hard.
5. **Declare the artifact contract.** With a separate verifier, every agent-produced path the grader reads must be listed in top-level `artifacts`. Declaring them is what makes the verifier able to see the output at all.
6. **Write a content verifier.** `tests/test.sh` must reject absent, empty, malformed, and semantically wrong output, default the reward to 0, and write exactly one reward channel: `/logs/verifier/reward.txt` or `/logs/verifier/reward.json`. Treat transfer and parse failures as non-passing.
7. **Harden the trust boundary.** Set `verifier.environment_mode = "separate"` (or provide `[verifier.environment]`), keep verifier network `no-network` or allowlisted, and keep the graders out of the agent image so the agent cannot read or edit them.
8. **Build all five controls.** Oracle (reward 1), no-op (0), near-miss (0), shortcut (0), alternative-valid (1). The shortcut control is the one that proves value: a response that satisfies the letter of the instruction without the work must fail.
9. **Run repeated rollouts and record them.** At least three rollouts per control with identical outcomes; write a rollout manifest containing runner, model, and harness versions, seeds, budgets, and trace locations.
10. **Validate and publish.** Run the validator, inspect the JSON report, attach the evaluation card from [`templates/evaluation-card.json`](templates/evaluation-card.json), and publish only with zero blocking findings.

## Pitfalls

- **Existence-only verifiers.** `test -f /app/out/report.json` passes for an empty file. Content assertions are the whole game.
- **Missing artifact declarations.** A separate verifier starts from a fresh sandbox; undeclared outputs are invisible and every run scores 0 even when the agent succeeded.
- **`public` verifier network.** This is the `environment.network_mode` default. A grader with network access can be manipulated through fetched content and makes runs irreproducible.
- **Leaking the grader into the instruction.** Naming `tests/test_outputs.py` tells the agent where the answers live. Describe the observable contract instead.
- **Copying the reference output into the environment.** If the expected artifact ships in the agent image, the task measures copying, not capability.
- **Judging difficulty by oracle success.** An oracle that passes proves solvability, not discrimination; only the negative controls measure that.
- **Declaring `environment_mode = "shared"` alongside `[verifier.environment]`.** That is a configuration error, not a preference.
- **Publishing single-rollout results.** One passing trial hides flakiness; require repeated identical outcomes.

## Verification

- `python3 scripts/verify_task_package.py <task-dir>` exits 0 and reports zero blocking findings.
- `--rollouts` re-check confirms oracle 1 and no-op/near-miss/shortcut 0 across at least three trials each, with no flaky class.
- The oracle rollouts score exactly 1 and a deliberately broken solution scores 0.
- `instruction.md` contains no `tests/`, `solution/`, reward-path, or expected-value reference.
- The evaluation card records runner versions, model identifiers, seeds, budgets, and observed rewards.
