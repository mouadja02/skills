---
name: "senior-data-scientist"
description: >-
  Use when designing binary A/B tests, fitting leakage-safe tabular feature transforms, evaluating
  binary probability predictions, or reviewing causal and statistical assumptions for data-science
  decisions.
version: "1.1.0"
license: MIT
source: "https://github.com/alirezarezvani/claude-skills"
attribution: "alirezarezvani/claude-skills by Alireza Rezvani"
---

> **Attribution:** Sourced from [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) by [Alireza Rezvani](https://github.com/alirezarezvani), licensed MIT. Modified for this collection.

# Senior Data Scientist

Produce reviewable experiment, feature-engineering, and model-evaluation artifacts instead of relying on notebook-only output. The bundled runners use only the Python standard library and fail closed on malformed or unsafe inputs.

## When to Use

- Size a fixed-horizon binary A/B test from a baseline rate and relative minimum detectable effect.
- Fit numeric and categorical transforms on a training partition without learning from holdout rows.
- Evaluate binary probability predictions with threshold metrics, ROC AUC, average precision, and Brier score.
- Review experiment or causal-inference assumptions before communicating a business conclusion.

Do not use these helpers for sequential testing, clustered randomization, survival outcomes, multiclass evaluation, or causal identification without adapting the statistical design.

## Prerequisites

- Python 3.10 or newer.
- UTF-8 JSON inputs containing no secrets or production identifiers.
- A pre-registered metric, analysis unit, exclusion policy, and stopping rule for experiments.

## How to Run

Run commands from this skill directory. Outputs are written atomically. Existing output files are preserved unless `--force` is explicitly passed.

```bash
python3 scripts/experiment_designer.py \
  --input experiment-spec.json --output experiment-design.json
python3 scripts/feature_engineering_pipeline.py \
  --input feature-spec.json --output transformed-features.json
python3 scripts/model_evaluation_suite.py \
  --input predictions.json --output evaluation.json
python3 tests/test_workflows.py
```

A successful command exits `0`, writes valid JSON, and prints a compact completion record. Validation or existing-output failures exit `2` and do not publish a partial output.

## Quick Reference

### Experiment input

```json
{
  "baseline_rate": 0.10,
  "relative_mde": 0.10,
  "alpha": 0.05,
  "power": 0.80
}
```

The result reports per-variant and total sample sizes for an equal-allocation, two-sided, two-proportion z-test. `relative_mde` is relative lift: `0.10` moves a `0.10` baseline to `0.11`.

### Feature input

```json
{
  "records": [
    {"age": 20, "country": "FR", "observed_at": "2026-01-05T00:00:00Z"},
    {"age": 30, "country": "US", "observed_at": "2026-01-06T00:00:00Z"},
    {"age": null, "country": "FR", "observed_at": "2026-01-07T00:00:00Z"}
  ],
  "split_index": 2,
  "numeric": ["age"],
  "categorical": ["country"],
  "datetime": ["observed_at"]
}
```

Rows before `split_index` are the training partition. Medians, scaling parameters, modes, and categorical vocabularies are fitted only there. Holdout-only categories map to an explicit `__unknown` indicator. Datetimes produce cyclical day-of-week and month features.

### Model input

```json
{
  "y_true": [0, 0, 1, 1],
  "y_score": [0.10, 0.40, 0.35, 0.80],
  "threshold": 0.50
}
```

Both classes must be present. The result includes a confusion matrix, accuracy, precision, recall, F1, ROC AUC with tied-score handling, average precision, and Brier score.

## Procedure

1. **Freeze the decision.** Write the decision, primary metric, unit of analysis, target population, exclusions, and stopping rule before examining outcomes.
2. **Validate provenance.** Confirm timestamps, assignment keys, labels, and joins. Reject duplicate units, post-treatment features, and unexplained missingness.
3. **Design before observing.** For a binary fixed-horizon experiment, run `experiment_designer.py` and review every stated assumption. Add expected attrition outside the statistical minimum.
4. **Split before fitting transforms.** Establish a temporal or group-aware partition first. Pass that boundary as `split_index`; never fit imputers, vocabularies, scalers, target encoders, lag windows, or feature selection on holdout outcomes.
5. **Keep target-dependent work inside resampling.** If using scikit-learn later, place learned preprocessing and feature selection inside the pipeline evaluated by each fold. Grouped or temporal data requires matching splitters, not shuffled random folds.
6. **Evaluate probabilities and decisions separately.** Run `model_evaluation_suite.py`, then compare threshold metrics, ranking metrics, and calibration. Report prevalence and uncertainty; do not select a model from ROC AUC alone.
7. **Check identification for causal claims.** Randomization supports causal interpretation only when assignment and interference assumptions hold. Difference-in-differences additionally needs defensible parallel trends, correct timing, and uncertainty clustered at the assignment unit when appropriate.
8. **Write the decision record.** Include the frozen question, data window, exclusions, assumptions, effect size with interval, sensitivity checks, failure modes, and the exact artifact hashes used for review.

## Pitfalls

- **Peeking:** repeated fixed-horizon significance checks inflate false positives. Use a pre-specified sequential design if interim decisions are required.
- **Sample-ratio mismatch:** compare observed allocation with the randomization contract using a formal goodness-of-fit test; a fixed percentage imbalance rule is not universal.
- **Leakage:** computing rolling, lag, imputation, encoding, scaling, or selection parameters before the split can leak future or holdout information.
- **Cross-validation drift:** modern scikit-learn scorers should use named scorers or `response_method="predict_proba"`; avoid stale `needs_proba` examples.
- **Causal overreach:** propensity matching does not repair unmeasured confounding, and a regression coefficient is not automatically an average treatment effect.
- **Silent overwrite:** do not pass `--force` until the prior artifact is archived or its replacement is intentional and reviewable.

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_workflows.py
```

Require all six tests to execute. Then inspect each output as JSON and verify:

- experiment totals equal twice the per-variant size and assumptions match the intended design;
- feature parameters exclude holdout-only values and unknown categories are explicit;
- prediction lengths match, probabilities are finite and bounded, and both classes are present;
- invalid inputs create no output; and
- an existing output remains byte-for-byte unchanged without `--force`.

The helpers produce deterministic synthetic-analysis artifacts; they do not replace domain review, production data validation, confidence intervals for every metric, or a full statistical package.

## Reference Documentation

- [Statistical methods](references/statistical_methods_advanced.md)
- [Experiment design frameworks](references/experiment_design_frameworks.md)
- [Feature engineering patterns](references/feature_engineering_patterns.md)
