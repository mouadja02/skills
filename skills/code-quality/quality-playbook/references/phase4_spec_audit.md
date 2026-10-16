# Phase 4: Spec audit and triage

Moved verbatim from SKILL.md so the entry file stays small. "Above" and "below" can point to sections that are now in SKILL.md or in another file listed in SKILL.md's Reference Files table.

## Phase 4: Spec Audit and Triage

**v1.5.6 instrumentation:** Append `phase_start phase=4` now. For each pass A/B/C/D, append `pass_started phase=4 pass=X` and `pass_ended phase=4 pass=X`. At phase end, cross-validate (`quality/REQUIREMENTS.md` non-empty AND `quality/COVERAGE_MATRIX.md` exists) then append `phase_end phase=4`.

> **Required references for this phase:**
> - `references/spec_audit.md` — Council of Three protocol, triage process, verification probes

Run the spec audit protocol as described in File 5. The triage report **must** include a `## Pre-audit docs validation` section (see `references/spec_audit.md` for the full template). This section is required even if `reference_docs/` is empty — in that case, note what baseline the auditors used instead. Every verification probe in the triage must produce executable evidence (test assertions with line-number citations) per the "Verification probes must produce executable evidence" rule above. After triage, categorize each confirmed finding.

**Effective council gating for enumeration checks.** If the effective council is less than 3/3 (fewer than three auditors returned usable reports) and the run includes any whitelist/enumeration/dispatch-function checks or any carried-forward seed checks, the audit may not conclude "no confirmed defects" for those checks without executed mechanical proof artifacts. An incomplete council with mechanical verification is acceptable. An incomplete council relying on prose-only validation for code-presence claims is not — escalate to "NEEDS VERIFICATION" and run the mechanical check before closing.

**Pre-audit spot-checks must extract from code, not assert from docs.** When the spec audit prompt includes spot-check claims for pre-validation (e.g., "verify that function X handles constant Y at line Z"), the triage must validate each claim by extracting the actual code at the cited lines — not by confirming that the claim sounds plausible. For each spot-check claim about code contents, the pre-validation must report what the cited lines actually contain: "Line 3527 contains `default:` — NOT `case VIRTIO_F_RING_RESET:` as claimed." If the spot-check was generated from requirements or gathered docs rather than from the code itself, treat it as a hypothesis to test, not a fact to confirm. This rule prevents the contamination chain observed in v1.3.17 where a false spot-check claim ("RING_RESET at 3527-3528") was accepted as "accurate" without reading the actual lines, then propagated through the triage and into every downstream artifact.

**Update PROGRESS.md:** Add every confirmed **code bug** from the spec audit to the cumulative BUG tracker with source "Spec Audit". This is critical — spec-audit bugs are systematically orphaned if they aren't added to the same tracker that the closure verification reads.

### Layer 2 — Semantic Citation Check (v1.5.3 Council sub-pass)

After the main spec audit triage, each Council member runs a per-REQ verdict against every Tier 1/2 REQ's `citation_excerpt`. This is **Layer 2** of the hallucination gate: Layer 1 is the mechanical byte-equality check — `bin/citation_verifier` is invoked by `bin/reference_docs_ingest` at ingest time and re-invoked by `quality_gate.py` at gate time; the LLM never shells out to it directly. Layer 2 is semantic — the reviewer decides whether the excerpt actually supports the requirement as stated, or whether the requirement overreaches what the excerpt says.

**Protocol.**

1. **One prompt per Council member, all Tier 1/2 REQs batched in.** Not one REQ at a time (3×N prompts is too many). Not a prose response (pattern-matching risk). The reviewer receives the full list of `(req_id, citation_excerpt, REQ description)` tuples and returns a structured per-REQ JSON response.

2. **Structured response schema (schemas.md §9.2).** For each REQ the reviewer records `{"req_id": "REQ-NNN", "reviewer": "<stable string>", "verdict": "supports" | "overreaches" | "unclear", "notes": "<reasoning>"}`. Valid `verdict` values are enumerated in schemas.md §3.5.

3. **Batching threshold.** When a run produces more than 15 Tier 1/2 REQs, split into batches of up to 15 REQs per prompt per Council member. The same reviewer sees each batch sequentially; their response entries are concatenated into one `reviews[]` array under the same `reviewer` string.

4. **Reviewer identifier stability.** Use fixed strings like `"claude-opus-4.7"`, `"gpt-5.4"`, `"gemini-2.5-pro"`. The majority computation in schemas.md §10 invariant #17 groups on this field — a typo silently becomes a fourth reviewer and breaks the 2-of-3 majority check.

5. **Output.** Concatenate all Council members' responses into `quality/citation_semantic_check.json` using the §1.6 manifest wrapper, except the record array is named `reviews` rather than `records` (schemas.md §9.1). One file per run, regenerated on every audit pass.

**Majority rule (gate-enforced).** For each Tier 1/2 REQ, the gate groups reviews by `req_id` and fails the run when ≥2 of 3 reviewers recorded `verdict == "overreaches"`. A single-member `overreaches` or `unclear` verdict surfaces as a warning but does not fail the gate. A REQ with fewer than three reviewer entries (missing reviewer, skipped batch) has insufficient evidence — the gate treats that as a fail.

**No-op for Spec Gap runs.** If a run produces zero Tier 1/2 REQs, `citation_semantic_check.json` is still written with an empty `reviews` array — the file's existence is part of the artifact contract even when the check has nothing to evaluate.

### Post-spec-audit regression tests

After the spec audit triage, check the cumulative BUG tracker in PROGRESS.md. Any spec-audit BUG that doesn't have a regression test yet needs one now. Write regression tests for spec-audit confirmed code bugs using the same conventions as code-review regression tests (expected-failure markers, test-finding alignment, executable source files).

**Why this step exists:** Code review bugs get regression tests immediately because tests are written right after the review. Spec audit runs after the tests are written, so its confirmed bugs are orphaned — they appear in the triage report but never get tests. This step closes that gap.

**Individual auditor artifacts (mandatory).** The spec audit must produce individual auditor report files at `quality/spec_audits/` with filenames containing `auditor` (canonical format: `YYYY-MM-DD-auditor-N.md`, e.g., `2026-04-12-auditor-1.md`; also accepted: `auditor_<model>_<date>.md`). The gate globs for `*auditor*` — any conformant name will match. One file per auditor, not just the triage synthesis. Each auditor report records what that auditor found independently before triage reconciliation. If only the triage file exists with no individual auditor artifacts, the audit is incomplete — the triage cannot be verified because there is no record of pre-reconciliation findings. This requirement exists because a single triage file conflates discovery with reconciliation, making it impossible to tell whether a finding was independently confirmed or synthesized from a single source.

**Phase 4 completion gate.** Phase 4 is not complete until a triage file exists at `quality/spec_audits/YYYY-MM-DD-triage.md` **and** individual auditor reports exist. If only auditor reports exist with no triage synthesis, mark Phase 4 as "partial — triage pending" in PROGRESS.md and complete the triage before proceeding. If only the triage exists with no individual reports, mark Phase 4 as "partial — auditor artifacts missing" and regenerate them. The PROGRESS.md checkbox must not be set until both the triage file and auditor reports are confirmed present.

Update the BUG tracker entries with regression test references. Mark Phase 4 (Spec audit + triage) complete.

**End-of-phase message (mandatory — print this after Phase 4 completes, then STOP):**

```
# Phase 4 Complete — Spec Audit

The Council of Three spec audit is done. [Summarize: N auditors ran, N net-new bugs
confirmed from triage, total bugs now at N. List any new bug IDs and summaries.]

To continue to Phase 5 (Reconciliation — TDD verification, writeups, closure), say:

    Run quality playbook phase 5.

Or say "keep going" to continue automatically.
```

**After printing this message, STOP. Do not proceed to Phase 5 unless the user explicitly asks.**
