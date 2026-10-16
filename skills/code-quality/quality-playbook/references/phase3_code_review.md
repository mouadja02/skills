# Phase 3: Code review and regression tests

Moved verbatim from SKILL.md so the entry file stays small. "Above" and "below" can point to sections that are now in SKILL.md or in another file listed in SKILL.md's Reference Files table.

## Phase 3: Code Review and Regression Tests

**v1.5.6 instrumentation:** Append `phase_start phase=3` to `quality/run_state.jsonl` now. At phase end, cross-validate (`quality/RUN_CODE_REVIEW.md` exists; one writeup per identified bug) then append `phase_end phase=3`.

> **Required references for this phase:**
> - `quality/REQUIREMENTS.md` — target list for the code review
> - `references/review_protocols.md` — three-pass protocol and regression test conventions

Run the code review protocol (all three passes) as described in File 3. After producing findings, write regression tests for every confirmed BUG per the closure mandate in `references/review_protocols.md`.

**Update PROGRESS.md:** Add every confirmed BUG to the cumulative BUG tracker with source "Code Review", the file:line reference, description, severity, and closure status (regression test function name or exemption reason). Mark Phase 3 (Code review + regression tests) complete.

**End-of-phase message (mandatory — print this after Phase 3 completes, then STOP):**

```
# Phase 3 Complete — Code Review

The three-pass code review is done. [Summarize: N bugs confirmed, N regression test
patches generated, N fix patches generated. List the bug IDs and one-line summaries.]

To continue to Phase 4 (Spec audit — Council of Three), say:

    Run quality playbook phase 4.

Or say "keep going" to continue automatically.
```

**After printing this message, STOP. Do not proceed to Phase 4 unless the user explicitly asks.**
