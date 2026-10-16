# Runner-driven mode, bootstrap runs, and v1.5.4 mechanics

Moved verbatim from SKILL.md so the entry file stays small. "Above" and "below" can point to sections that are now in SKILL.md or in another file listed in SKILL.md's Reference Files table.

### Mode B — runner-driven invocation (CLI-automation)

The operator runs `python3 -m bin.run_playbook` themselves (typically because they want batching, headless CI, or to route per-phase work to a different model). The orchestrator at `bin/run_playbook.py` spawns a CLI agent per phase, feeds it the externalized phase prompt, and aggregates the result.

#### Canonical invocation

The orchestrator is the entry point. Always invoke it as a Python module:

```
python3 -m bin.run_playbook <target>
```

**Never invoke it script-style** (`python bin/run_playbook.py ...`). The runtime guard exits with `EX_USAGE=64` because relative imports require packaged execution.

`<target>` is the path to the project to audit. For a bootstrap run (target IS the QPB repo), pass `.` from the repo root. For any other target, pass the path to that target's repo root.

#### Default behavior (no flags)

Bare invocation triggers a **full run**: all 6 phases (Explore → Generate → Code Review → Spec Audit → Reconciliation → Verify) followed by all 4 iteration strategies (gap → unfiltered → parity → adversarial), executed synchronously in the same session. Any prior `quality/` directory is auto-archived to `quality/previous_runs/<TIMESTAMP>/` before the new run starts.

This is the canonical operator path. Don't ask permission to add flags; the defaults are the answer.

When the bare invocation fires, the orchestrator emits a one-line stderr banner naming the cost change vs. v1.5.3 (~5–10× the legacy "Phase 1 only" default). That banner is informational; let it scroll.

#### Common overrides

Use only when the operator asks for something specific:

| Need | Flag | Effect |
|------|------|--------|
| Run a single phase | `--phase N` (where N ∈ 1..6) | Recovers the v1.5.3 "explore only" pattern with `--phase 1`. |
| Skip iteration strategies | omit `--iterations` and pass `--phase 1,2,3,4,5,6` | Phases run; iterations don't. |
| Specific iteration | `--strategy <name> --next-iteration` | Iterates on an existing `quality/` run with a chosen strategy. |
| Multi-target | pass several positional targets | Each runs independently. |
| Per-phase CLI agent | `--claude` / `--copilot` / `--codex` / `--cursor` | Picks which CLI runner the orchestrator spawns. Default is `--copilot`. v1.5.4 added the `--cursor` runner (cursor-cli 3.1+). |

#### Recovering from a partial / aborted runner-driven run

Council 2026-04-30 P1-4: the operator-hygiene guidance for cleaning up after an aborted run lives in the **Bootstrap mode** section below ("Bootstrap-run operator hygiene") — the recovery is identical in Mode B: `git restore quality/` to discard the partial Phase 1/2 output, then re-invoke. **Do NOT** edit files outside `quality/` to "tidy up" — the source-unchanged invariant trips on the very next run. See the Bootstrap-mode hygiene paragraph for the full mechanic; it applies regardless of whether the abort happened during a self-audit run or against an external target.

### Bootstrap mode (running QPB on itself)

When the operator says "this is a bootstrap run" or "we're running QPB on itself" or "self-audit":

1. Confirm the working directory is the QPB repo root (or `cd` there).
2. Invoke `python3 -m bin.run_playbook .` — same canonical form, target is `.`.
3. The orchestrator handles archival of the existing `quality/` tree to `quality/previous_runs/<TIMESTAMP>/` automatically; you don't need to clean anything manually.

The run proceeds the same way as any other target. The only difference is that the audit subject IS the playbook itself, so the produced artifacts describe QPB's own quality system.

**Bootstrap-run operator hygiene — recovering from a partial / aborted run.** If a prior bootstrap run aborted mid-flight (e.g., the source-unchanged invariant tripped, a phase prompt errored, the operator hit Ctrl-C), the working tree may contain a half-written `quality/` directory plus a `quality/previous_runs/<TIMESTAMP>/.partial` sentinel marking the abandoned archive. Before re-invoking, run `git restore quality/` (and, if you want a clean slate, `git clean -fd quality/`) to drop any uncommitted Phase 1/2 output from the aborted run. The orchestrator will re-archive the now-pristine `quality/` tree and start clean. **Do NOT** edit files outside `quality/` to "tidy up" — anything outside `quality/` is QPB source; touching it for cleanup will trip the source-unchanged invariant on the very next run. The 2026-04-30 bootstrap test surfaced this exact recovery question: the operator had a half-written `quality/` from an aborted Phase 2 and re-running without restoring left stale Phase 1 artifacts that confused the next run's archival.

### v1.5.4 mechanics (pointer-style, not duplicating the design doc)

What's new vs. v1.5.3, in pointer form (the canonical architecture lives in `docs/design/QPB_v1.5.4_Design.md` Part 1):

- **Phase 1 produces `quality/exploration_role_map.json`** — per-file role tagging done AI-driven during exploration. Each in-scope file gets a role from the taxonomy (`skill-prose`, `skill-reference`, `skill-tool`, `code`, `test`, `docs`, `config`, `fixture`, `formal-spec`, `playbook-output`). The role map drives every downstream pipeline-activation decision.
- **`INDEX.md` uses `schema_version: "2.0"`** with a `target_role_breakdown` field carrying the per-role counts and percentages. The v1.5.3 `target_project_type` enum is retired (legacy archives stay readable).
- **Pipelines activate from the role map, not from a project-type label.** The four-pass skill-derivation pipeline runs over files tagged `skill-prose` / `skill-reference`. The code-review pipeline runs over files tagged `code`. The prose-to-code divergence check runs over files tagged `skill-tool`. When the role map shows zero of a role, that pipeline no-ops cleanly. There is no Code/Skill/Hybrid trichotomy — both pipelines run when both surfaces are present (the "always-Hybrid downstream" model).
- **Archive directory is `quality/previous_runs/`** (was `quality/runs/` in v1.5.3); legacy archives at the old path remain readable.
- **End-of-Phase-6 reorganization** moves intermediate artifacts under `quality/workspace/` so the top-level `quality/` directory is dominated by canonical deliverables (REQUIREMENTS.md, BUGS.md, etc.). The gate's path resolver reads from both layouts.

You don't need to re-derive any of this in your prompt-side reasoning; the orchestrator's prompts already encode it. If you encounter a phase prompt that conflicts with the architecture summarized here, follow the phase prompt — it's the canonical source for the per-phase contract.
