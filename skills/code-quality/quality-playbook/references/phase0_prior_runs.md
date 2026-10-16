# Phase 0: Prior run analysis

Moved verbatim from SKILL.md so the entry file stays small. "Above" and "below" can point to sections that are now in SKILL.md or in another file listed in SKILL.md's Reference Files table.

## Phase 0: Prior Run Analysis (Automatic)

**This phase runs only if `quality/previous_runs/` exists and contains prior quality artifacts.** If there are no prior runs, skip to Phase 1. If `quality/previous_runs/` exists but is empty or contains no conformant quality artifacts (no subdirectories with `quality/BUGS.md` under them), skip Phase 0a and fall through to Phase 0b. (Legacy archives at `quality/runs/` from pre-v1.5.4 remain readable for backward compatibility — see "v1.5.4 mechanics" in `references/runner_mode.md` — but the canonical archive root is `quality/previous_runs/`.)

When prior runs exist, the playbook enters **continuation mode**. This enables iterative bug discovery: each run inherits confirmed findings from prior runs, verifies them mechanically, and explores for additional bugs. The iteration converges when a run finds zero net-new bugs.

**Step 0a: Build the seed list.** Read `quality/previous_runs/*/quality/BUGS.md` from all prior runs. For each confirmed bug, extract: bug ID, file:line, summary, and the regression test assertion. Deduplicate by file:line (the same bug found in multiple runs counts once). Write the merged seed list to `quality/SEED_CHECKS.md` with this format:

```markdown
## Seed Checks (from N prior runs)

| Seed | Origin Run | File:Line | Summary | Assertion |
|------|-----------|-----------|---------|-----------|
| SEED-001 | run-1 | virtio_ring.c:3509-3529 | RING_RESET dropped | `"case VIRTIO_F_RING_RESET:" in func` |
```

**Step 0b: Execute seed checks mechanically.** For each seed, run the assertion against the current source tree. Record PASS (bug was fixed since last run) or FAIL (bug still present). A failing seed is a confirmed carry-forward bug — it must appear in this run's BUGS.md regardless of whether any auditor independently finds it. A passing seed means the bug was fixed — note it in PROGRESS.md as "SEED-NNN: resolved since prior run."

**Step 0c: Identify prior-run scope.** Read `quality/previous_runs/*/quality/PROGRESS.md` for scope declarations. Note which subsystems were covered in prior runs. During Phase 1 exploration, prioritize areas NOT covered by prior runs to maximize the chance of finding new bugs. If all subsystems were covered in prior runs, explore the same scope but with different emphasis (e.g., different scrutiny areas, different entry points).

**Step 0d: Inject seeds into downstream phases.** The seed list becomes input to:
- **Phase 3 (code review):** Add to the code review prompt: "Prior runs confirmed these bugs — verify they are still present and look for additional findings in the same subsystems."
- **Phase 4 (spec audit):** Add to `RUN_SPEC_AUDIT.md`: "Known open issues from prior runs: [seed list]. Expect auditors to find these. If an auditor does NOT flag a known seed bug, that is a coverage gap in their review, not evidence the bug was fixed."

**Why this exists:** Non-deterministic scope exploration means different runs notice different bugs. In cross-version testing, 4/8 repos had bugs found in some versions but not others — not because the bugs were fixed, but because the model explored different parts of the codebase. Iterating with seed injection solves this: confirmed bugs carry forward mechanically (no re-discovery needed), and each new run can focus exploration on uncovered territory.

### Phase 0b: Sibling-Run Seed Discovery (Automatic)

**This step runs only if `quality/previous_runs/` does not exist OR `quality/previous_runs/` exists but contains no conformant quality artifacts** (i.e., Phase 0a has nothing to work with) **and** the project directory is versioned (e.g., `httpx-1.3.23/` sits alongside `httpx-1.3.21/`). If `quality/previous_runs/` exists with conformant artifacts, Phase 0a already handles seed injection — skip this step.

**If `quality/previous_runs/` exists but is empty or contains only non-conformant subdirectories**, emit a warning: "Phase 0b: `quality/previous_runs/` exists but contains no conformant artifacts — consulting sibling versioned directories for seeds." Then proceed with the sibling discovery below.

When no `quality/previous_runs/` directory exists but sibling versioned directories do, look for prior quality artifacts in those siblings:

1. **Discover siblings.** List directories matching the pattern `<project-name>-<version>/quality/BUGS.md` relative to the parent directory. Exclude the current directory. Sort by version descending (most recent first).
2. **Import confirmed bugs as seeds.** For each sibling with a `quality/BUGS.md`, extract confirmed bugs using the same format as Step 0a. Write them to `quality/SEED_CHECKS.md` with origin noted as the sibling directory name.
3. **Execute seed checks mechanically** (same as Step 0b in Phase 0a). For each imported seed, run the assertion against the current source tree and record PASS/FAIL.
4. **Inject into downstream phases** (same as Step 0d in Phase 0a).

**Why this exists:** In v1.3.23 benchmarking, httpx produced a zero-bug result despite httpx-1.3.21 having found the `Headers.__setitem__` non-ASCII encoding bug. The model simply explored different code paths and never examined the Headers area. Sibling-run seeding ensures that bugs confirmed in prior versioned runs carry forward even without an explicit `quality/previous_runs/` archive. This is a different failure class than mechanical tampering — it addresses **exploration non-determinism**, not evidence corruption.
