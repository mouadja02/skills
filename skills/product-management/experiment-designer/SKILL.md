---
name: experiment-designer
description: Use when planning, designing, or interpreting any A/B test, split test, multivariate test, or controlled experiment — for products, features, marketing pages, signup flows, pricing, or copy variants. Covers hypothesis writing, sample-size estimation, ICE prioritization, traffic allocation, statistical-significance analysis, guardrail metrics, and the peeking problem. Triggers on: "A/B test", "split test", "experiment", "test this change", "variant copy", "multivariate test", "hypothesis", "conversion experiment", "statistical significance", "minimum detectable effect", "sample size".
---

# Experiment Designer

Design, prioritize, and evaluate controlled experiments — both **product experiments** (features, flows, ML changes) and **marketing experiments** (landing pages, copy, pricing, CTAs) — with clear hypotheses and defensible decisions.

This skill is the canonical home for A/B-test methodology in this collection. Marketing-specific framing (proactive CRO triggers, ad-copy patterns) is handled below; deeper CRO surface-level work lives in `page-cro`, `signup-flow-cro`, and `onboarding-cro`.

## When to use

- A/B and multivariate experiment **planning**
- **Hypothesis** writing and success criteria
- **Sample size** and minimum-detectable-effect (MDE) calculation
- Experiment **prioritization** (ICE, RICE-style scoring)
- **Statistical interpretation** of test results for business decisions
- Optimizing signup, onboarding, pricing, landing page, ad copy, or feature changes

## Core principles

1. **Start with a hypothesis** — not "let's see what happens". Specific prediction, based on data or reasoning.
2. **Test one thing** — single variable per test; otherwise you cannot isolate cause.
3. **Statistical rigor** — pre-determine sample size, do not peek and stop early, commit to the methodology.
4. **Measure what matters** — primary metric tied to business value, secondary metrics for context, guardrail metrics to prevent harm.

---

## Hypothesis framework

### If/Then/Because format (product context)

- **If** we change `[intervention]`
- **Then** `[metric]` will change by `[expected direction/magnitude]`
- **Because** `[behavioral mechanism]`

### Marketing/CRO format

```
Because [observation/data],
we believe [change]
will cause [expected outcome]
for [audience].
We'll know this is true when [metrics].
```

**Weak**: "Changing the button color might increase clicks."

**Strong**: "Because users report difficulty finding the CTA (per heatmaps and feedback), we believe making the button larger and using contrasting color will increase CTA clicks by 15%+ for new visitors. We'll measure click-through rate from page view to signup start."

### Hypothesis quality checklist

- [ ] Contains explicit intervention and audience
- [ ] Specifies measurable metric change
- [ ] States plausible causal reason
- [ ] Includes expected minimum effect (MDE)
- [ ] Defines failure condition

---

## Test types

| Type | Description | Traffic needed |
| --- | --- | --- |
| **A/B** | Two versions, single change | Moderate |
| **A/B/n** | Multiple variants, single change | Higher |
| **MVT** (multivariate) | Multiple changes in combinations | Very high |
| **Split URL** | Different URLs for variants | Moderate |

---

## Metric selection

### Primary metric

- Single decision metric, directly tied to hypothesis.
- This is what you call the test on.

### Secondary metrics

- Diagnostic — explain *why/how* the change worked.
- Never the basis for go/no-go on their own.

### Guardrail metrics

- Things that **shouldn't get worse** — quality, safety, downstream funnel steps, support tickets, refund rate.
- Stop the test if these go significantly negative.

### Example: pricing-page test

- **Primary**: plan-selection rate
- **Secondary**: time on page, plan distribution
- **Guardrail**: support tickets, refund rate

---

## Sample size

### Quick reference table

| Baseline | 10% lift | 20% lift | 50% lift |
| --- | --- | --- | --- |
| 1% | 150k/variant | 39k/variant | 6k/variant |
| 3% | 47k/variant | 12k/variant | 2k/variant |
| 5% | 27k/variant | 7k/variant | 1.2k/variant |
| 10% | 12k/variant | 3k/variant | 550/variant |

### Tooling

```bash
# Demo mode
python3 scripts/sample_size_calculator.py

# Compute sample size for a 5% baseline targeting 20% relative lift
python3 scripts/sample_size_calculator.py --baseline 0.05 --mde 0.20

# Add daily traffic to estimate test duration
python3 scripts/sample_size_calculator.py --baseline 0.05 --mde 0.20 --daily-traffic 500

# JSON output for automation
python3 scripts/sample_size_calculator.py --baseline 0.05 --mde 0.20 --json
```

The calculator is 100% stdlib (no scipy / numpy required). For a deeper sample-size guide with edge cases see [`references/sample-size-guide.md`](./references/sample-size-guide.md).

External calculators worth knowing:

- [Evan Miller's](https://www.evanmiller.org/ab-testing/sample-size.html)
- [Optimizely's](https://www.optimizely.com/sample-size-calculator/)

---

## Prioritization (ICE)

When you have more candidate experiments than capacity:

```
ICE Score = (Impact × Confidence × Ease) / 10
```

- **Impact**: potential upside if it wins (1–10).
- **Confidence**: evidence quality the hypothesis is right (1–10).
- **Ease**: cost / speed / complexity to ship the variant (1–10).

Run highest-ICE first.

---

## Traffic allocation

| Approach | Split | When to use |
| --- | --- | --- |
| **Standard** | 50/50 | Default for A/B |
| **Conservative** | 90/10, 80/20 | Limit risk of a bad variant |
| **Ramping** | Start small, increase | Technical-risk mitigation |

- Keep variant assignment **consistent** across visits for the same user.
- Ensure exposure is balanced across time of day / week.

---

## Designing variants (marketing context)

### What to vary

| Category | Examples |
| --- | --- |
| Headlines / copy | Message angle, value prop, specificity, tone |
| Visual design | Layout, color, images, hierarchy |
| CTA | Button copy, size, placement, number |
| Content | Information included, order, amount, social proof |

### Best practices

- **Single, meaningful change** per test arm.
- **Bold enough** to detect — too-small differences are statistically invisible.
- **True to the hypothesis** — the variant is the hypothesis, not random tweaks.

---

## Implementation

### Client-side

- JavaScript modifies the page after load.
- Quick to implement; can cause flicker.
- Tools: PostHog, Optimizely, VWO.

### Server-side

- Variant determined before render.
- No flicker, requires dev work.
- Tools: PostHog, LaunchDarkly, Split.

---

## Running the test

### Pre-launch checklist

- [ ] Hypothesis documented
- [ ] Primary, secondary, guardrail metrics defined
- [ ] Sample size calculated; duration committed
- [ ] Variants implemented correctly
- [ ] Tracking verified end-to-end
- [ ] QA completed on all variants

### During the test

**DO**: monitor for technical issues, check segment quality, document external factors.

**DON'T**: peek at results and stop early, change variants mid-test, add traffic from new sources.

### The peeking problem

Looking at results before reaching sample size and stopping early **inflates false positives**. Pre-commit to the sample size and trust the process. If you must look, use sequential analysis with a formal correction (e.g., always-valid p-values).

---

## Analyzing results

### Statistical significance

- 95% confidence ⇔ p-value < 0.05.
- Means there's a < 5% chance the result is noise — **not** a guarantee of truth.
- Statistical significance is **not** business significance.

### Analysis checklist

1. Reached sample size? If not, the result is preliminary.
2. Statistically significant? Check confidence intervals, not just p-values.
3. Effect size meaningful? Compare point estimate to MDE and to business impact.
4. Secondary metrics consistent? Do they support the primary?
5. Guardrail concerns? Anything got materially worse?
6. Segment differences? Mobile vs. desktop, new vs. returning, geo, plan.

### Interpreting results

| Result | Conclusion |
| --- | --- |
| Significant winner | Implement variant |
| Significant loser | Keep control, learn why |
| No significant difference | Need more traffic or a bolder test |
| Mixed signals | Dig deeper, segment, possibly re-run |

### Statistical interpretation guardrails

- p-value < α → evidence against the null, not guaranteed truth.
- Confidence interval crossing zero → uncertain directional claim.
- Wide intervals → low precision even when significant.
- Use **practical significance** thresholds tied to business impact.

---

## Common pitfalls

### Test design

- Underpowered tests → false negatives; the variant might have worked but you can't tell.
- Testing too many things at once → can't isolate cause.
- No clear hypothesis → no learning even if the variant wins.

### Execution

- Stopping early on random spikes.
- Changing things mid-test (tracking, copy, eligibility).
- Sample-ratio mismatch and instrumentation drift.
- Running too many simultaneous tests on overlapping audiences without isolation.

### Analysis

- Declaring success from p-value without effect-size context.
- Cherry-picking segments after the fact.
- Over-interpreting inconclusive results.
- Ignoring novelty effects on early data.

---

## Documentation

Document every test:

- Hypothesis
- Variants (with screenshots)
- Results (sample, metrics, significance, CI)
- **Decision and learnings** — even if the variant lost.

Templates: [`references/test-templates.md`](./references/test-templates.md).

---

## Output artifacts

| Artifact | Format | Description |
| --- | --- | --- |
| **Experiment brief** | Markdown | Hypothesis, variants, metrics, sample size, duration, owner |
| **Sample-size input** | Table | Baseline rate, MDE, confidence, power |
| **Pre-launch QA checklist** | Checklist | Implementation, tracking, variant rendering verification |
| **Results report** | Markdown | Statistical significance, effect size, segment breakdown, decision |
| **Test backlog** | Prioritized list | Ranked experiments by ICE / expected impact |

---

## Proactive triggers (marketing context)

Proactively offer A/B test design when:

1. **Conversion rate mentioned** — user shares a conversion rate and asks how to improve it; suggest designing a test rather than guessing.
2. **Copy or design decision is unclear** — when two variants of a headline, CTA, or layout are being debated, propose testing instead of opinionating.
3. **Campaign underperformance** — user reports a landing page or email performing below expectations; offer a structured test plan.
4. **Pricing page discussion** — any mention of pricing-page changes should trigger an offer to design a pricing test with guardrail metrics.
5. **Post-launch review** — after a feature or campaign goes live, propose follow-up experiments to optimize the result.

---

## References

- [`references/experiment-playbook.md`](./references/experiment-playbook.md) — end-to-end experiment workflow.
- [`references/statistics-reference.md`](./references/statistics-reference.md) — significance, power, MDE, p-value pitfalls.
- [`references/sample-size-guide.md`](./references/sample-size-guide.md) — extended sample-size tables and duration calculations.
- [`references/test-templates.md`](./references/test-templates.md) — Markdown templates for briefs, QA, and results reports.

## Related skills

- [`page-cro`](../../marketing-and-growth/page-cro/) — *what* to test on a marketing page (use first to generate hypotheses).
- [`signup-flow-cro`](../../marketing-and-growth/signup-flow-cro/) — signup-specific test patterns.
- [`onboarding-cro`](../../marketing-and-growth/onboarding-cro/) — activation/onboarding experiments.
- [`product-discovery`](../product-discovery/) — qualitative validation *before* you have a hypothesis worth testing.
- [`marketing-context`](../../marketing-and-growth/marketing-context/) — load this for ICP/positioning framing before designing marketing tests.
