# Run-state instrumentation

Moved verbatim from SKILL.md so the entry file stays small. Read it once at run start, together with `references/run_state_schema.md`. "Above" and "below" can point to sections that are now in SKILL.md or in another file listed in SKILL.md's Reference Files table.

## Run-state instrumentation (v1.5.6 — write events as you go)

Two files in `quality/` track this run's state across the filesystem so the run is observable in flight, resumable across crashes, and auditable afterward. Maintain both throughout the run.

- **`quality/run_state.jsonl`** — append-only machine-readable event log. One JSON object per line. The orchestrator and any monitor reads this file to know exactly where the run is.
- **`quality/PROGRESS.md`** — human-readable status file, atomically rewritten on every event.

**Authoritative schema:** `references/run_state_schema.md`. Read it once at run start; it defines the full event taxonomy, required fields, cross-validation rules, and PROGRESS.md format.

### Initialization (before any phase work, including Phase 0)

If `quality/run_state.jsonl` does not exist:
1. Create `quality/` if absent.
2. Append the `_index` event to `quality/run_state.jsonl`. Required fields: `event=_index`, `ts` (ISO 8601 UTC with `Z`), `schema_version="1.5.6"`, `event_types` (array listing all event types this run will use — at minimum `_index`, `run_start`, `phase_start`, `pattern_walked`, `pass_started`, `pass_ended`, `finding_logged`, `artifact_written`, `gate_check`, `phase_end`, `error`, `run_end`), `benchmark` (target name), `lever_state` (e.g. `"baseline"` for normal runs), `started_at`.
3. Append the `run_start` event. Required fields: `event=run_start`, `ts`, `runner` (one of `claude`/`codex`/`copilot`/`cursor`), `playbook_version` (read from SKILL.md frontmatter `version` field), `target_path`.
4. Write `quality/PROGRESS.md` per the format spec in `references/run_state_schema.md`. Include header (Started / Benchmark / Lever / Runner / Playbook version), empty phase checklist with all six phases, empty Recent events / Artifacts produced sections.

If `quality/run_state.jsonl` already exists at run start: this is a **resumed run**. See "Resume semantics" below.

### Per-phase events

At every phase boundary (1 through 6), write events:

- **At phase start:** append `{"event":"phase_start","ts":"<now>","phase":N}` to `quality/run_state.jsonl`. Update `quality/PROGRESS.md`: mark phase N as in-progress with current timestamp.
- **At phase end:** *first* cross-validate the phase's expected artifacts (table below). If validation fails, append `{"event":"error","ts":"<now>","phase":N,"message":"<what's missing>","recoverable":true}` and re-run the phase. If validation passes, append `{"event":"phase_end","ts":"<now>","phase":N,"key_counts":{...},"artifacts_produced":[...]}`. Update PROGRESS.md: check off phase N with summary stats.

**Phase 1 sub-events (in addition to phase_start/phase_end):**
- After walking each of the seven exploration patterns: append `{"event":"pattern_walked","ts":"<now>","phase":1,"pattern":N,"findings_count":K}`. (One event per pattern, even if zero findings.)
- When `quality/EXPLORATION.md` is written: append `{"event":"artifact_written","ts":"<now>","relative_path":"quality/EXPLORATION.md","byte_size":<size>,"line_count":<lines>}`.

**Phase 4 sub-events:**
- At each pass start (A through D): `{"event":"pass_started","ts":"<now>","phase":4,"pass":"A"}`.
- At each pass end: `{"event":"pass_ended","ts":"<now>","phase":4,"pass":"A","output_artifact":"<path>"}`.

**Phase 5 / Phase 6 sub-events:**
- At each gate-check completion: `{"event":"gate_check","ts":"<now>","gate_name":"<name>","verdict":"pass|fail|warn|skip","reason":"<short>"}`.

**Run end:**
- After Phase 6 `phase_end`: append `{"event":"run_end","ts":"<now>","status":"success","total_findings":<N>,"final_verdict":"<gate verdict>"}`. Status is `aborted` for `recoverable:false` failures, `failed` for unrecoverable runtime errors.

### Cross-validation rules at phase_end

Verify the corresponding artifacts before writing each `phase_end` event:

| Phase | Required |
|---|---|
| 1 | `quality/EXPLORATION.md` and `quality/PROGRESS.md` satisfy the 13-check Phase 2 entry gate in `references/phase2_generate.md` (six required headings: `## Open Exploration Findings`, `## Quality Risks`, `## Pattern Applicability Matrix`, `## Pattern Deep Dive — *` ×3+, `## Candidate Bugs for Phase 2`, `## Gate Self-Check`; PROGRESS Phase 1 line marked `[x]`; ≥8 findings with file:line citations; ≥3 multi-location findings; 3-4 FULL pattern matrix rows; ≥2 multi-function pattern deep dives; candidate-bug source mix ≥2 from exploration/risks AND ≥1 from pattern deep dive). `bin/run_state_lib.validate_phase_artifacts(quality_dir, phase=1)` enforces the full gate. |
| 2 | All nine Generate-contract artifacts exist non-empty under `quality/`: `REQUIREMENTS.md`, `QUALITY.md`, `CONTRACTS.md`, `COVERAGE_MATRIX.md`, `COMPLETENESS_REPORT.md`, `RUN_CODE_REVIEW.md`, `RUN_INTEGRATION_TESTS.md`, `RUN_SPEC_AUDIT.md`, `RUN_TDD_TESTS.md`. Plus at least one non-empty `quality/test_functional.<ext>` (extension varies by language). |
| 3 | `quality/RUN_CODE_REVIEW.md` exists |
| 4 | `quality/REQUIREMENTS.md` non-empty AND `quality/COVERAGE_MATRIX.md` exists. If the four-pass skill-derivation pipeline ran (i.e., `quality/phase3/` exists), then `quality/phase3/pass_a_drafts.jsonl`, `quality/phase3/pass_b_citations.jsonl`, `quality/phase3/pass_c_formal.jsonl`, and the Pass D inbox under `quality/phase3/` must all exist and be non-empty. |
| 5 | `quality/results/quality-gate.log` exists, non-empty |
| 6 | `quality/BUGS.md` non-empty with `^##\s+BUG-` sections AND `quality/INDEX.md` updated with `gate_verdict` field |

If a check fails, append the `error` event (recoverable=true) and re-run the phase. Do **not** write `phase_end` against missing artifacts — that's the failure mode v1.5.6 is built to catch.

`bin/run_state_lib.validate_phase_artifacts(quality_dir, phase)` performs these checks programmatically — call it from inside the playbook session if available.

### Resume semantics

If `quality/run_state.jsonl` already exists when the playbook starts (a previous session crashed or paused mid-run):

1. Read all events. Use `bin/run_state_lib.last_in_progress_phase(events)` to find the last `phase_start` not followed by a matching `phase_end` — call it the in-progress phase.
2. Run the cross-validation rules above for that phase.
   - **Artifacts complete:** the prior session finished the work but didn't get to write `phase_end`. Append the missing `phase_end` (with current `ts`) and proceed to the next phase.
   - **Artifacts incomplete:** re-run that phase from scratch.
3. If all six `phase_end` events are present but no `run_end`: append `run_end status=success` and finalize.
4. If no `quality/run_state.jsonl` exists: fresh run. Initialize per the section above.

The policy: **trust artifacts more than events.** If events claim phase 4 done but `REQUIREMENTS.md` doesn't exist, re-run phase 4. If events stop mid-phase but the artifacts are complete, catch up the events.

### PROGRESS.md atomic rewrite

PROGRESS.md is rewritten on every event (not appended). The contents reflect the current run-state.jsonl: header (run metadata), phase checklist (with summary stats per completed phase, in-progress marker for the current phase), recent events (last 10 events from the JSONL log, in human-readable form), artifacts produced (files written this run with byte sizes). See `references/run_state_schema.md` for the exact format template.

`bin/run_state_lib.write_progress_md(quality_dir, events, current_phase)` produces a correctly-formatted PROGRESS.md from the event list — call it after each event to keep the file in sync.
