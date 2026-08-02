---
name: kubernetes-cel-admission-policy-preflight
description: "Use when native Kubernetes ValidatingAdmissionPolicy or CEL admission rules need fixture completeness, cost/resource checks, bootstrap-safety analysis, or an Audit/Warn-to-Deny rollout gate."
version: "1.0.0"
license: MIT
---

# Kubernetes CEL Admission Policy Preflight

Preflight native Kubernetes `ValidatingAdmissionPolicy` (VAP) as a versioned evaluation environment, request-context matrix, resource budget, and cluster-startup dependency—not merely as valid YAML. Begin read-only. The bundled helper classifies a redacted evidence packet offline; it neither evaluates arbitrary CEL nor contacts a cluster.

## When to Use

- A native VAP or binding uses CEL and must be tested before `Deny` enforcement.
- CLI, controller, or unit-test results differ from API-server behavior because request context or CEL environments differ.
- Admission policy count, expression complexity, or runtime cost may affect API-server resources.
- A fail-closed policy could block the controller, webhook, identity, networking, or storage needed during startup.

## When Not to Use

- The target is solely a Kyverno `ClusterPolicy`, Gatekeeper ConstraintTemplate, or admission webhook with no generated/native VAP; use that engine's workflow.
- The request is generic RBAC, Pod Security Admission, or CEL outside Kubernetes admission.
- The goal is to apply an unreviewed policy directly to production or bypass admission controls.
- A complete CEL semantic test is required but no pinned Kubernetes evaluator or disposable cluster is available. This helper checks evidence completeness, not expression truth.

## Prerequisites

- Exact Kubernetes/API-server version and the CEL environment used by that version.
- Read access to VAPs, bindings, parameters, relevant API-server metrics/logs, and controller startup dependencies.
- Synthetic or redacted request fixtures covering intended operations and identities.
- A disposable cluster or project-native evaluator for semantic CEL tests; never assume a generic CEL runtime matches Kubernetes.
- Python 3.10+ for the optional offline checker.

## Quick Reference

1. Pin Kubernetes, policy API, and CEL environment.
2. Inventory policies, bindings, parameters, match rules, failure policy, actions, and startup dependencies.
3. Build complete CREATE/UPDATE/DELETE/CONNECT request fixtures, including `oldObject`, user identity, and absent parameters where relevant.
4. Prove semantic outcomes on the pinned evaluator and record static/runtime cost plus API-server resource deltas.
5. Classify the redacted packet:

```bash
python3 scripts/check_cel_admission.py --input preflight.json --output report.json
```

Exit `0` means `pass` or `not_applicable`; `1` means blockers were found; `2` means malformed/unreadable input or report-write failure. Every report sets `mutation_permitted: false`.

## Evidence Packet Contract

Use `schema_version: 1`, `kind: kubernetes_cel_admission_preflight`, and `target_type: native_vap`. The JSON helper is intentionally strict: unknown fields, duplicate keys or fixture IDs, loose booleans, invalid edge references, and non-standard numbers such as `NaN` fail closed.

Required native-VAP sections:

- `inventory`: non-empty `kubernetes_version`; exact `cel_environment` (an empty value becomes a finding).
- `policy`: `failure_policy` (`Fail` or `Ignore`), matched operations, and context used by expressions.
- `bindings`: unique names and `Audit`, `Warn`, or `Deny` validation actions.
- `fixtures`: unique IDs, operation, user-info presence, old-object state, parameter state, and observed semantic outcome.
- `cost`: whether static estimation and pinned-runtime budget behavior were checked.
- `resources`: baseline/observed API-server MiB, policy-binding pair count, and an owner-defined maximum delta per pair.
- `bootstrap`: declared nodes and dependency edges, with the admission policy's node identified.
- `rollout`: current stage, observed canary evidence, and emergency rollback documentation.

Do not include kubeconfigs, bearer tokens, Secrets, raw production objects, private names, complete logs, or user PII. The helper does not consume CEL source, so expressions cannot become an accidental execution channel.

## Procedure

### 1. Freeze the native evaluation boundary

Record Kubernetes/API-server version, VAP API version, feature gates if applicable, policy and binding generations, parameter kind/version, and evaluator version. Capture the exact CEL environment made available by the target Kubernetes release, including exposed variables, libraries, and compatibility behavior. A standalone CEL implementation or a policy-engine emulator is comparative evidence only until it is shown to match that boundary.

**Completion:** one timestamped inventory identifies the evaluator that will make the admission decision.

### 2. Inventory effective policy and binding behavior

For each policy and binding, record:

- `matchConstraints`, `matchConditions`, operations, resource/subresource scope, selectors, and exclusions;
- every validation, message expression, audit annotation, and parameter reference;
- binding `validationActions` and parameter-not-found behavior;
- `failurePolicy`, overlapping policies, generated VAP ownership, and object generations;
- dependencies required to evaluate policy or admit components during control-plane and controller startup.

Do not infer the effective operation from a source engine's rule when it generates a VAP; inspect the generated native objects and observed requests. Preserve `Audit`, `Warn`, and `Deny` as distinct actions.

**Completion:** every admission decision has one mapped native policy/binding/parameter path or an explicit ambiguity.

### 3. Build complete request-context fixtures

Use synthetic objects. Cover each matched operation and both expected-allow and expected-deny cases. Add expression-error cases when `failurePolicy` matters. Include:

- CREATE with `object` and null/absent `oldObject` as observed by the pinned evaluator;
- UPDATE with changed and unchanged fields plus representative `oldObject`;
- DELETE with representative `oldObject` when DELETE is matched;
- CONNECT for matching subresources when applicable;
- service-account, human, group, and omitted/variant user-info cases when identity is read;
- parameters present, absent, and mismatched when expressions or bindings depend on them;
- excluded namespaces/resources and match-condition false paths.

A fixture is valid evidence only if it parses and reaches the intended evaluator. A malformed fixture is a test failure, not proof that a policy rejected bad input.

**Completion:** the operation/context matrix has no untested matched operation or referenced context.

### 4. Run semantic and differential checks

Evaluate the same fixtures with the project-native test path and against a disposable API server at the pinned version when practical. Compare allow/deny/error, message, warning, and audit outputs. Treat disagreement as unresolved; do not select the more permissive result.

The offline helper deliberately does not execute CEL. Record only the observed outcomes in its packet. This separates potentially unsafe expression execution from deterministic completeness and rollout classification.

**Completion:** every fixture has an observed outcome from the authoritative boundary, and emulator differences are retained.

### 5. Bound cost and resource growth

Use Kubernetes-provided static estimation where available and exercise runtime paths on bounded synthetic inputs. Record timeout or budget-exhaustion behavior under the selected failure policy. Measure API-server memory and latency before and after a controlled policy-binding increment; divide only by the actual number of added pairs and retain workload conditions.

The packet's `max_extra_mib_per_pair` is an owner-defined operating budget, not a Kubernetes guarantee. Repeat measurements to distinguish policy cost from unrelated load. Never generate unbounded objects or expressions against production.

**Completion:** static cost, runtime-budget behavior, and a bounded resource delta are recorded or rollout remains blocked.

### 6. Prove bootstrap safety

Draw directed dependencies between the policy, API server, generated-policy controller, parameter providers, identity/network components, and workloads required for startup. An edge `A -> B` means A requires B to become ready. Reject a fail-closed rollout when the policy node participates in a cycle—for example, policy evaluation blocks the controller that must create or repair what the policy requires.

Test cold start and degraded dependencies in a disposable cluster. Prefer namespace/object exclusions and staged actions over assuming startup order. Do not change `failurePolicy` globally as an automatic workaround.

**Completion:** no policy-node cycle exists, or the rollout stays non-enforcing with a reviewed redesign.

### 7. Canary Audit/Warn before Deny

Start with `Audit` and/or `Warn` on a narrow, owned scope. Observe expected decisions, expression errors, API-server cost/resource metrics, controller health, and false-positive volume. Document an emergency rollback that removes or narrows the binding without deleting policy evidence. Promote to `Deny` only after the same fixture matrix passes and the canary is observed.

Re-run the packet checker. A pass is evidence readiness, not permission to mutate production; normal change control still applies.

**Completion:** canary observations satisfy the owner-defined window, rollback is rehearsable, and promotion preserves the exact tested policy generation.

## Objective Verification

Pass only when:

- Kubernetes and CEL environments are pinned;
- every matched operation has an observed fixture;
- DELETE/`oldObject`, `request.userInfo`, parameters, and expression errors are covered when used;
- static and runtime cost evidence exists;
- measured resource delta stays within the declared budget;
- the admission policy is outside all declared startup dependency cycles;
- selected rollout stage matches binding actions;
- Deny has observed prior canary evidence and documented emergency rollback;
- artifacts are redacted and the checker emits no findings.

## Failure Recovery and Unsafe Operations

- Never apply, bind, delete, or patch production admission policy from this workflow automatically.
- Never switch directly to `Deny`, broaden matching, or set fail-open behavior merely to make tests pass.
- If a policy blocks control-plane or controller startup, stop rollout, use the pre-approved rollback path from an administrative recovery channel, and preserve redacted generations/events.
- If resource growth exceeds budget, restore the prior binding scope or policy generation before profiling expressions offline.
- If evaluators disagree, keep Audit/Warn, pin every version, and reduce to the smallest fixture that reproduces the difference.
- If sensitive objects or identity data enter an artifact, quarantine it, remove it from shared storage, and follow the owner's credential/privacy response process.

## Pitfalls

- YAML/schema validity does not prove CEL environment compatibility or semantic behavior.
- Generated VAP behavior can differ from the source engine's rule or CLI test context.
- Missing `userInfo`, `oldObject`, or params can turn a reassuring fixture into a false pass.
- `failurePolicy`, match failures, validation actions, and expression false results are different outcomes.
- A mean memory delta without pair count and workload context is not a reusable budget.
- Warm-cluster tests miss bootstrap dependency cycles.
- Audit/Warn observations do not authorize Deny unless the exact tested generation and scope are promoted.

## Evaluation Prompts

See [`references/evaluations.md`](references/evaluations.md) for normal, difficult-edge, and should-not-activate prompts with machine-checkable assertions.

## Sources and Provenance

**Sourced facts:** Kubernetes documents the native VAP variables, matching, parameters, validation actions, failure policy, audit annotations, and CEL cost controls. The cited project issues demonstrate missing ecosystem test tooling, API-server memory growth, uneven runtime-cost enforcement, omitted test `userInfo`, bootstrap deadlock, and operation-semantics gaps.

**Original recommendations:** the evidence-packet schema, context matrix, resource budget, dependency-cycle gate, offline classifier, canary sequence, completion criteria, and recovery hierarchy are original operational synthesis. No third-party code or prose is bundled.

- [Kubernetes: Validating Admission Policy](https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/)
- [Kubernetes: Common Expression Language](https://kubernetes.io/docs/reference/using-api/cel/)
- [kubernetes/kubernetes #135351: provide CEL test tooling](https://github.com/kubernetes/kubernetes/issues/135351)
- [kubernetes/kubernetes #131417: VAP memory consumption](https://github.com/kubernetes/kubernetes/issues/131417)
- [kyverno/kyverno #14495: runtime cost budget gap](https://github.com/kyverno/kyverno/issues/14495)
- [kyverno/kyverno #13829: VAP test userInfo omission](https://github.com/kyverno/kyverno/issues/13829)
- [open-policy-agent/gatekeeper #4530: generated VAP bootstrap deadlock](https://github.com/open-policy-agent/gatekeeper/issues/4530)
- [open-policy-agent/gatekeeper #3906: operation semantics](https://github.com/open-policy-agent/gatekeeper/issues/3906)
