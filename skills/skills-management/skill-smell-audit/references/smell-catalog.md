# Skill Smell Catalog

The 26 smells from Hong, Imani & Ahmed, *From Anatomy to Smells: An Empirical Study of SKILL.md in
Agent Skills* (arXiv:2607.01456, July 2026). Each smell is the violation of an authoring best practice
the authors collected from 29 sources, including Anthropic's and Microsoft's skill guidance and the
agentskills.io specification. Prevalence is the share of 228 real-world skills that showed the smell.
Detection: **S** = `scripts/static_smells.py` checks it; **R** = needs a reader (you).

Definitions are paraphrased. The "Ask" column is the question to answer while reading; the "Fix"
column is the smallest edit that removes the smell.

## Description and naming

| Smell | Det. | Prev. | Ask | Fix |
| --- | --- | --- | --- | --- |
| Confusing Skill Description (CSD) | R (S proxy) | 32% | Does the description say what the skill does, when to use it, and the keywords a user would type? | Rewrite as a router rule: "Use when <situations, tools, error strings> — <what it does>." |
| Non Third Person Description (NTPD) | R (S proxy) | 3% | Is it written as "I can…" or "You should…"? | Third person or imperative trigger: "Use when…", "Generates…". |
| XML Included Description (XID) | S | 0% | Does the description contain `<tags>`? | Remove them; tags in an always-loaded field can inject instructions. |
| Lengthy Skill Description (LSD) | S | ≈0% | Over 1,024 characters? | Cut synonyms that name the same branch; keep one trigger per distinct case. |
| Lengthy Skill Name (LSN) | S | 0% | Over 64 characters? | Shorten; keep it kebab-case and matching the folder. |
| Unclear Skill Name (USN) | R | 17% | Does the name say what the skill does (`pdf-form-filler`) rather than a brand or pun? | Rename to verb-noun or domain-task form; keep an alias in the description if users know the old name. |

## Workflow structure

| Smell | Det. | Prev. | Ask | Fix |
| --- | --- | --- | --- | --- |
| The Stepless Workflow (TSW) | R | 32% | Is the procedure one block of prose? | Break it into numbered steps, one action each. |
| Series of Commands (SOC) | R | 62% | Is it a rigid command list that fails when the environment differs? | State the goal of each step, then the default command; say what to do if it fails. |
| Execute Without a Plan (EWP) | R | 78% | Does a complex or destructive task start without a planning or confirmation stage? | Add a plan step that lists intended changes before making them. |
| No Validation Step (NVS) | R | 69% | Does the skill produce output without checking it? | Add a validate → fix → re-validate loop with a concrete check (test, linter, schema, re-read). |
| No Progress Tracking (NPT) | R | 71% | Can a long multi-step run lose its place? | Add a checklist the agent copies and ticks, or a state file. |
| Rationalization Loophole (RL) | R | 94% | Can the agent talk itself out of a required step ("small change, skip tests")? | Name the tempting shortcuts and forbid them: a short "Do not skip" list or rationalization table. |
| Never Asks Human (NAH) | R | 77% | Is there no point where the agent must stop for a decision only the user can make? | Add explicit "ask the user when…" conditions. Skip for skills meant to run unattended — say so instead. |
| Missing Decision Tree (MDT) | R | 69% | When there are several approaches, does the skill say how to choose? | Add a short decision table: situation → approach. |
| The Option Buffet (TOB) | R | 8% | Does it list alternatives with no default? | Name the default and when to deviate. |

## Content and disclosure

| Smell | Det. | Prev. | Ask | Fix |
| --- | --- | --- | --- | --- |
| Undelegated Detail (UD) | R (S proxy) | 46% | Is low-level reference (API tables, long examples) inline in SKILL.md? | Move it to `references/` behind a pointer that says when to read it. |
| Lengthy Skill Body (LSB) | S | ≈0% | Body over 5,000 words? (Anthropic's guidance aims for under 500 lines.) | Split by branch: keep the steps, disclose the reference. |
| Missing Utility Script (MUS) | R | 66% | Is there a deterministic, repeated task the agent re-derives every run (parsing, validating, converting)? | Ship a script under `scripts/` and tell the agent to run it rather than read it. |
| Missing Template (MT) | R | 25% | Must the output follow a format (report, commit, JSON) that the skill never shows? | Add a template block or a `templates/` file. |
| Missing Example (ME) | R (S proxy) | 34% | Is there no worked input → output example? | Add one short, realistic example. |
| Missing Usage Rules (MUR) | R | 44% | Does it never say when *not* to use it, or what it requires? | Add "Do not use for…" and prerequisites. |

## Robustness

| Smell | Det. | Prev. | Ask | Fix |
| --- | --- | --- | --- | --- |
| No Guardrails (NG) | R | 67% | Can it be applied to tasks it cannot or should not do (destructive actions, wrong platform)? | Add refusal/stop conditions and scope limits. |
| Buried Gotchas (BG) | R | 81% | Are critical warnings mid-paragraph instead of under a visible heading? | Collect them under `## Gotchas` near the top or at the step they affect. |
| Missing Caveats (MC) | R | 71% | Are common failures and their fixes absent? | Add a failure → cause → fix table for the errors users actually hit. |
| Time Sensitive Skill (TSS) | R (S proxy) | 3% | Does it say "latest", "as of 2025", or name versions that will age? | Pin versions explicitly or point at the source of truth; move dated notes to an "Old patterns" section. |
| Backslash Path (BP) | S | 1% | Are paths written `scripts\run.py`? | Forward slashes everywhere; they work on every OS. |

## Quality signals that predict downstream success

SkillEval (Han et al., arXiv:2608.06891) scores seven document properties. Five of them — B1 to D1 below —
each correlated with pass-rate uplift on SkillsBench at about r = 0.78, and revising the weakest ones
raised mean pass rate from 18.6% to 48.1% (38.3% for revision without the scores). Use them as the
rubric for the summary score in the report.

| Signal | Score 2 when… |
| --- | --- |
| A1 Format Validity | Frontmatter is valid YAML with `name` and `description`. |
| A2 Trigger Clarity | The description states what, when, and trigger conditions tied to concrete scenarios. |
| B1 Content Consistency | The body delivers every capability the description claims. |
| B2 Technical Specificity | Concrete tools, commands, parameters, units, constraints, and file paths appear. |
| C1 Workflow Integrity | Input → processing → output stages are explicit and ordered. |
| C2 I/O Explicitness | Inputs and outputs are defined with formats, fields, or schemas. |
| D1 Failure Awareness | Failures, edge cases, diagnostic signals, and recovery steps are covered. |

Score 1 when the property is partly present, 0 when absent.

## What revisions tend to help

Wang et al. (*Agent Skill Evolution*, arXiv:2610.04832) studied 2,608 first-to-last revision pairs. Adding
an automatically checkable rule raised the rate at which agents took the required action by 0.23 on
average, and most of the gain came from rules that **name a specific command or file path the old
skill did not mention**. When the body is loaded on demand, about half of that gain survived. Prefer
fixes that add a concrete, checkable instruction over fixes that add prose.

## Security is a separate pass

Liu et al. (*Agent Skills in the Wild*, arXiv:2601.10338) found at least one vulnerability pattern in
26.1% of 31,132 marketplace skills, led by data exfiltration (13.3%) and privilege escalation (11.8%);
skills that bundle scripts were 2.12 times as likely to be vulnerable. Smell auditing does not cover
this. Run the `skill-scanner` skill on any skill you did not write before installing it.
