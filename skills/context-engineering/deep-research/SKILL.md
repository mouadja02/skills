---
name: deep-research
description: Use for deep research, literature reviews, and fact-checking. Investigate questions across sources, evaluate papers, refine research questions, or conduct systematic reviews. Supports full, quick, review, lit-review, fact-check, socratic, and systematic-review modes.
license: MIT
metadata:
  version: "3.0.0"
---

# Deep research

Turn a question into an evidence-based answer with a clear account of what was searched, what was found, and what remains uncertain. Match the effort and output to the user's question, available sources, and constraints. Respect higher-priority instructions governing browsing, delegation, citations, and user interaction.

## Choose a mode

Honor a named mode or an explicit requested outcome. Otherwise use the closest fit:

- **full**: Investigate a defined question across relevant perspectives and produce a substantive synthesis.
- **quick**: Answer a narrow question with a focused search and a concise, sourced brief; state important coverage limits.
- **review**: Assess a supplied paper or other work for its question, methods, evidence, limitations, and whether its conclusions follow. Distinguish what the work says from your assessment.
- **lit-review**: Map relevant scholarship by theme, method, agreement, disagreement, and gap; include enough search detail to explain coverage.
- **fact-check**: Break a statement into checkable claims, trace each to reliable evidence, and report a supported, unsupported, mixed, or unresolved finding with qualifications.
- **socratic**: Help the user refine an uncertain direction. Ask focused questions, offer alternative framings, and adapt to the answers; do not invent a settled research question or force a full report.
- **systematic-review**: Define a reproducible protocol, search, screen, extract, appraise, and synthesize evidence. Record deviations and missing steps. Use meta-analysis only where data and methods justify it.

If scope is unclear, make reasonable assumptions for work that can proceed and identify decisions that materially affect the answer. Ask the user when their answer is needed. The user may switch modes at any point. Policy analysis can use full or quick mode and should compare options, consequences, uncertainty, and affected groups. For research-to-paper handoff, supply the question, findings, sources, methods, limitations, and unresolved issues; do not assume an uninstalled companion skill is present.

## Investigation

1. Define the question, time frame, population or setting, relevant terms, and intended decision. Separate subquestions where helpful.
2. Search sources appropriate to the topic. Prefer primary evidence and authoritative data for claims that depend on them; use independent perspectives to identify disagreement. Search current sources when currency matters. Record databases or sites, search terms, dates, filters, and meaningful access limits as appropriate to the task.
3. Inspect the actual source when possible. Verify bibliographic details, date, study design, population, measures, and relevant results. Do not present a search snippet, abstract, or secondary account as a full-text reading. Flag inaccessible material, retractions, conflicts of interest, and uncertainty when relevant. Never fabricate a source, quotation, identifier, or result.
4. Compare evidence rather than counting sources. Consider study design, risk of bias, applicability, sample size, precision, and whether findings have been independently replicated. Distinguish association from causation and evidence of absence from absence of evidence. Investigate material contradictions and plausible alternative explanations.
5. Write a direct answer, followed by supporting evidence, competing interpretations, limitations, and practical implications as appropriate. Link each consequential claim to a source that supports it. Separate evidence, inference, and recommendations; calibrate confidence to the evidence. Use the user's requested citation style when feasible, including APA 7 if requested.
6. Check that cited sources exist, support their associated claims, and are described accurately. Disclose uncompleted searches or checks; do not claim exhaustive coverage without evidence.

## Systematic review safeguards

Before screening, document the question, eligibility criteria, planned sources and search strings, date limits, outcomes, screening and extraction procedures, risk-of-bias approach, and synthesis plan. Register a protocol only if requested and the appropriate service is available; do not imply registration occurred. Track records identified, deduplicated, screened, excluded with reasons, and included, and report counts and deviations. Use relevant reporting guidance, such as PRISMA, where applicable, without claiming compliance for missing steps. Independent screening and adjudication require actual independent reviewers; disclose when unavailable.

Use a design-appropriate appraisal instrument if its requirements can be met. For quantitative pooling, check effect definitions, comparability, dependence, missing data, and statistical assumptions; report method, uncertainty, heterogeneity, and sensitivity analyses. If data or expertise are insufficient, explain why and use a transparent narrative synthesis instead. Do not invent estimates, assess unpublished data as observed, or treat software output as independently verified.

## Optional roles and follow-up

When delegation is explicitly permitted and useful, assign bounded tasks such as searching, source verification, synthesis, and critical challenge, then reconcile results and verify citations yourself. Otherwise perform these checks within the current workflow. Offer a reusable search strategy or monitoring plan if helpful; create alerts or scheduled monitoring only when requested and supported, and never imply an alert is active without confirmation from the service.

Reusable [working forms](references/working-forms.md) cover the research brief, handoff, offline work, review protocol, evidence ledger, and monitoring plan.
