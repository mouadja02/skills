---
name: kubernetes-ssa-field-ownership-triage
description: Use when Kubernetes Server-Side Apply reports field-manager conflicts, controllers overwrite fields, or force-conflicts risks pruning/defaulting side effects; diagnose ownership read-only before choosing relinquish, partition, or explicit transfer.
version: "1.0.0"
license: MIT
---

# Kubernetes SSA Field Ownership Triage

## When to Use

- `kubectl apply --server-side` or another SSA client reports a field conflict.
- Argo CD, Terraform, Helm, an operator, or a webhook appears to fight over fields.
- A forced apply removed injected/defaulted values or caused recurring drift.
- A team must decide whether to relinquish, partition, or transfer ownership.

Do **not** use this for client-side three-way-merge errors, immutable-field errors, ordinary Helm template design, or non-Kubernetes state conflicts. Do not treat `managedFields` as a historical audit log.

## Prerequisites

- Read access to the resource and its CRD/schema when applicable.
- `kubectl` matched reasonably closely to the API server.
- The exact apply client, field-manager name, intended manifest, and conflict text.
- Python 3.9+ only if using the optional offline analyzer.
- A backup and explicit human approval before any live ownership transfer.

## Safety Rules

1. Start read-only. Save redacted evidence outside the repository.
2. Never recommend `--force-conflicts` merely to make reconciliation green.
3. Do not edit `metadata.managedFields` directly; it is API-server-managed state.
4. Test with server dry-run, but remember admission/defaulting still participates and dry-run support can vary by webhook.
5. Identify the controller responsible for each manager before changing manifests or manager names.
6. A live force operation is an ownership transfer and may prune fields omitted by the new owner. Require a reviewed payload, backup, rollback, and named approver.

## Quick Reference

```bash
# Preserve the exact live object for offline inspection; redact sensitive data.
kubectl get deployment api -n prod -o json > /tmp/api-live.json

# Inventory manager/path claims without contacting the cluster.
python3 scripts/ssa_ownership.py inventory /tmp/api-live.json

# Parse an apply error captured as plain text.
python3 scripts/ssa_ownership.py conflicts /tmp/apply-error.txt

# Reproduce admission and ownership checks without persisting a change.
kubectl apply --server-side --dry-run=server \
  --field-manager=my-deployer -f intended.yaml -o yaml
```

## Procedure

### 1. Freeze the evidence

Record:

- cluster and Kubernetes version;
- resource GVK, namespace, name, and `resourceVersion`;
- apply client/version and exact `--field-manager` value;
- intended object after rendering, with secrets redacted;
- full conflict message;
- active reconcilers, mutating webhooks, and GitOps/Terraform ownership.

Fetch the live object once. Avoid loops that repeatedly apply while diagnosing: even no-op SSA requests can change managed-field metadata in some Kubernetes versions.

**Completion:** one timestamped live object, one intended object, and one exact error are available for comparison.

### 2. Map managers to owned paths

Inspect `.metadata.managedFields[]` by manager, operation, API version, subresource, and `fieldsV1`. Use the helper for a readable inventory, then verify important paths against the raw object.

```bash
python3 scripts/ssa_ownership.py inventory /tmp/api-live.json --pretty
```

Interpret ownership as a current field set, not proof of who last changed a value. The same manager string may be reused by unrelated clients; operation and workflow identity matter. For CRDs, inspect structural schema and list semantics (`atomic`, `set`, or `map`) because one apparent list item can be owned atomically or by keyed element.

**Completion:** every conflicting path has a current owner, operation, API version, and responsible controller/client—or is explicitly marked unknown.

### 3. Classify the conflict

Use the first matching class:

| Class | Evidence | Preferred direction |
| --- | --- | --- |
| Accidental duplicate manager | Different clients reuse one manager name | Give each workflow a stable unique manager; retest |
| Shared desired field | Two reconcilers intentionally set the same scalar/atomic collection | Establish one source of truth; remove it from the other payload |
| Defaulted field | API defaulting adds a value that another client sends explicitly | Omit the default where safe or make one manager authoritative |
| Webhook-injected field | Mutating webhook owns/adds data after admission | Exclude it from deployer payload; test omission and pruning |
| Controller-owned status/subresource | Conflict concerns status or scale ownership | Use the proper subresource/client contract |
| List semantics mismatch | Ownership is at whole-list rather than keyed-item scope | Fix CRD schema or partition ownership; do not force blindly |
| Stale manager | Former controller still owns fields and no longer runs | Prove decommissioning, then plan explicit transfer |
| Version/schema drift | Manager entries or paths differ across served API versions | Compare conversion and schema behavior before transfer |

Do not infer “stale” from an old managed-field timestamp alone. Prove that no active controller uses that manager.

### 4. Reproduce without mutation

Run the exact rendered payload with the exact manager using server dry-run. Keep force disabled first.

```bash
kubectl apply --server-side --dry-run=server \
  --field-manager="$MANAGER" -f intended.yaml -o json > /tmp/dry-run.json
```

Test one hypothesis at a time:

1. original payload and manager;
2. payload with disputed fields omitted;
3. stable unique manager, only when manager collision is suspected;
4. disposable namespace/cluster fixture for webhook, defaulting, or list-semantics behavior.

Compare values **and field ownership**, including fields absent from the intended payload. If a webhook does not support dry-run, stop and use a disposable environment rather than testing in production.

**Completion:** the failure boundary is reproducible, and one non-mutating variant removes the conflict without losing required fields—or the uncertainty is documented.

### 5. Choose the least risky ownership transition

Decision order:

1. **Relinquish:** remove fields the client does not intend to own. Confirm the live value remains correct after a disposable apply.
2. **Partition:** split manifests/controllers so each owns disjoint schema fields or keyed list items.
3. **Coordinate:** pause or reconfigure one reconciler and document a single source of truth.
4. **Transfer:** only if the old owner is intentionally displaced. Review the complete payload and omitted-field behavior, then obtain approval for force.

A transfer plan must name the old and new manager, exact paths, pause order, backup, canary object, rollback command, and post-apply ownership assertions. Never force an entire rendered object when only a small, deliberately reviewed field set requires transfer.

### 6. Verify recovery

After an approved canary change:

```bash
kubectl get <kind> <name> -n <namespace> -o json > /tmp/after.json
python3 scripts/ssa_ownership.py inventory /tmp/after.json --pretty
kubectl diff --server-side --field-manager="$MANAGER" -f intended.yaml
```

Require all of these:

- the intended manager owns only the approved paths;
- the displaced manager no longer reclaims them after at least two reconciliation intervals;
- webhook/defaulted fields remain present;
- no unrelated path was pruned or changed;
- a repeated dry-run/apply is conflict-free and convergent;
- rollback remains possible from the saved object or source-of-truth manifest.

## Failure Recovery

- **Dry-run changes behavior:** stop; verify webhook `sideEffects` and dry-run support, then reproduce in a disposable cluster.
- **Manager cannot be identified:** do not force. Correlate controller deployment, audit logs, and manager naming configuration.
- **Force pruned fields:** pause the new reconciler, restore the reviewed prior values through the legitimate owner, and verify admission/controller convergence.
- **Conflict returns:** an active reconciler still claims the field. Revert the transfer and establish a single owner rather than repeating force.
- **CRD list ownership is unexpectedly atomic:** restore the previous CRD/controller version if safe and redesign schema/list ownership before retrying.

## Objective Verification Checklist

- [ ] Exact conflict text and rendered payload preserved.
- [ ] Conflicting paths mapped to managers from raw `managedFields`.
- [ ] Defaulting, webhook mutation, subresources, and list semantics considered.
- [ ] Failure reproduced with server dry-run or a disposable fixture.
- [ ] Recovery transition proven without unrelated pruning.
- [ ] Live force, if any, has explicit approval, backup, canary, and rollback.
- [ ] Repeated reconciliation converges without ownership churn.

## Evaluation Prompts

1. **Normal:** “Argo CD SSA says `conflict with kubectl` on `.spec.replicas`. Diagnose it without changing the Deployment.”
2. **Difficult edge:** “A forced apply to a CRD removed a webhook-injected annotation and two entries from a map-like list. Determine whether defaulting, webhook ownership, or CRD list semantics caused it and design a disposable recovery test.”
3. **Should not activate:** “Create a Helm chart with a Deployment, Service, probes, and secure defaults.”

Expected observable behavior: prompts 1–2 map managers and paths, classify ownership, reproduce without mutation, and gate force behind approval; prompt 3 routes to a Helm/chart workflow instead.

## Sourced Facts and Recommendations

**Sourced facts:** Kubernetes documents SSA field tracking in `managedFields`, conflict behavior, field-manager identity, merge markers/list topology, and force-conflict transfer. The cited issues demonstrate current cross-project failure modes involving no-op metadata updates, forced pruning of injected annotations, operator ownership, and stale provider payload fields.

**Recommendations:** the classification table, evidence packet, decision order, canary rules, and approval gates are original operational guidance synthesized for safe triage.

## Sources

- Kubernetes Server-Side Apply documentation (accessed 2026-07-25): https://kubernetes.io/docs/reference/using-api/server-side-apply/
- Kubernetes no-op SSA managed-fields issue: https://github.com/kubernetes/kubernetes/issues/131175
- Argo CD forced-apply pruning issue: https://github.com/argoproj/argo-cd/issues/28721
- MariaDB Operator ownership-conflict issue: https://github.com/mariadb-operator/mariadb-operator/issues/1738
- Terraform Kubernetes provider stale-annotation issue: https://github.com/hashicorp/terraform-provider-kubernetes/issues/2894

No source prose or code is redistributed. This skill and helper are original MIT-licensed work.
