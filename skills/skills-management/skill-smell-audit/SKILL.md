---
name: skill-smell-audit
description: >-
  Use when reviewing, linting, or improving a SKILL.md or a whole skills library for authoring quality —
  a skill that under-triggers, gets skipped mid-workflow, or behaves differently run to run, or before
  publishing or importing skills. Runs a deterministic checker, then reads for the 26 skill smells from
  Hong et al. (2026) and SkillEval's quality signals, and reports ranked fixes.
version: "1.0.0"
license: MIT
source: "https://arxiv.org/abs/2607.01456; https://arxiv.org/abs/2608.06891; https://arxiv.org/abs/2610.04832"
attribution: "Written for this collection from Hong, Imani & Ahmed (2026), Han et al. (2026), and Wang et al. (2026)"
---

# Skill Smell Audit

A skill smell is a violation of a SKILL.md authoring best practice. In a study of 228 real skills,
all but one had at least one smell and the average was 10.5 (arXiv:2607.01456). Skills with clearer
triggers, explicit workflows, defined inputs and outputs, and failure handling make agents measurably
more successful (arXiv:2608.06891). This skill finds the smells and fixes the ones that matter.

## When to Use

- A skill does not trigger when it should, triggers when it should not, or is followed inconsistently.
- Before publishing a skill, merging a skill PR, or importing third-party skills into a library.
- Periodic hygiene on a skills library: rank which skills most need work.
- After an agent skipped a required step ("tests were optional") and the skill allowed it.

Do not use it to judge whether a skill is *safe* — use `skill-scanner` for prompt injection, exfiltration,
and malicious scripts. To write a new skill from scratch, use `writing-skills` or `skill-creator`, then
audit the draft with this skill.

## Inputs and outputs

- **Input:** a `SKILL.md` path, a skill folder, or a directory of skills.
- **Output:** a Markdown report in the template below, plus proposed diffs. Edit files only when the user
  asked for fixes, and never rewrite a third-party skill's content beyond what the finding needs.

## Workflow

Copy this checklist and tick it off as you go:

```
Skill smell audit:
- [ ] 1. Scope agreed (which skills, report only or fix)
- [ ] 2. Static check run, errors listed
- [ ] 3. Each skill read against the catalog
- [ ] 4. Signals scored
- [ ] 5. Report written
- [ ] 6. Fixes applied and re-checked (only if asked)
```

### 1. Agree the scope

For one skill, start. For a library, ask whether the user wants every skill read or a ranked shortlist
first; reading hundreds of skills is expensive. Default to the shortlist: static check everything, then
read the skills with errors, the ten most-used, and the ten largest.

### 2. Run the deterministic checker

```bash
python3 scripts/static_smells.py <path> --json > smells.json
```

Paths are relative to this skill's folder; the script uses only the Python standard library. It checks
the smells that need no judgment (name and description limits, XML in descriptions, body length,
backslash paths, broken links, bundled files mentioned but missing, reserved words in names) and flags
cheap proxies for others (no trigger in the description, first-person wording, dated phrasing, no
example). Exit status 1 means at least one `error`: the skill may fail to load or install. Fix those
first, whatever else the audit finds.

### 3. Read each skill against the catalog

Open [references/smell-catalog.md](references/smell-catalog.md) and answer each "Ask" question for the
skill. Record a smell only with evidence: quote the line, or name the section that is missing.
Confirm or dismiss every proxy the script raised; proxies are hints, not findings.

Judge applicability before recording:

| Situation | Not a smell |
| --- | --- |
| Pure reference skill (style guide, vocabulary) | Missing Utility Script, No Progress Tracking |
| Skill built to run unattended (CI, scheduled jobs) | Never Asks Human — but it must say it runs unattended |
| One-step skill | Stepless Workflow, Execute Without a Plan |
| Skill that only formats prose | Missing Template only if a format is required |

### 4. Score the quality signals

Score each of A2, B1, B2, C1, C2, D1 from the catalog's SkillEval table as 0, 1, or 2 (A1 is the
script's loading result). The total out of 12 orders a library for repair. Weak C1, C2, and D1 scores are
the ones most tied to downstream task success.

### 5. Write the report

Use this template:

```markdown
# Skill smell audit — <scope>

| Skill | Errors | Smells | Signals (/12) | Top fix |
| --- | ---: | ---: | ---: | --- |
| <install path> | <n> | <n> | <n> | <one line> |

## <install path>

**Loading errors:** <none, or list>

| Smell | Evidence | Fix |
| --- | --- | --- |
| RL Rationalization Loophole | Step 4 says "run tests if time allows" | Make tests mandatory; add "Do not skip" list |

**Signals:** A2 <n> · B1 <n> · B2 <n> · C1 <n> · C2 <n> · D1 <n>
```

Rank fixes in this order: loading errors, then trigger clarity (A2/CSD), then workflow and validation
(NVS, RL, BG, MC, D1), then disclosure (UD, LSB). Within a tier, prefer the fix that adds a concrete,
checkable instruction — a named command or file path — over one that adds explanation; those carried
most of the measured gains in arXiv:2610.04832.

### 6. Fix and re-check (only when asked)

1. Make one change per smell, the smallest that removes it.
2. Re-run `scripts/static_smells.py` on the edited skill. It must exit 0.
3. For description changes, test routing: write three requests that should trigger the skill and two
   near-misses that should not, and check each against the new description.
4. Re-score the signals you targeted and note the before/after in the report.

## Gotchas

- **Do not fix smells by adding bulk.** Every line in a loaded skill costs context. A missing caveat is
  one table row, not a section. If a fix pushes the body past 500 lines, move reference material out.
- **The description is always loaded**, the body only on demand. Spend words in the description only on
  distinct triggers; collapse synonyms.
- **Preserve attribution and licenses.** When fixing an imported skill, keep its `source`/`attribution`
  frontmatter and credit line, and note "Modified for this collection" if it is not there.
- **Time-sensitive content** is better pinned than deleted: state the version it applies to, or point at
  the source of truth.
- **Smell counts are not quality.** A short skill with three smells can beat a long one with none. Read
  the signals and the actual failure the user reported before rewriting.

## Related skills

- `skill-scanner` — security review of a skill before install.
- `writing-skills`, `skill-creator`, `writing-for-agents` — authoring and testing skills.
- `skill-cleaner` — removing stale or duplicate skills from a library.

## Sources

- Hong, Imani & Ahmed, *From Anatomy to Smells: An Empirical Study of SKILL.md in Agent Skills*,
  arXiv:2607.01456 (2026) — the smell catalog and prevalence figures.
- Han et al., *SkillEval: Decomposing Agent Skill Quality into Interpretable Signals*, arXiv:2608.06891
  (2026) — the quality signals.
- Wang et al., *Agent Skill Evolution: How Revisions Affect Coding Agents*, arXiv:2610.04832 (2026) —
  which revisions help.
- Liu et al., *Agent Skills in the Wild*, arXiv:2601.10338 (2026) — skill security prevalence.
- Anthropic, [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices).
