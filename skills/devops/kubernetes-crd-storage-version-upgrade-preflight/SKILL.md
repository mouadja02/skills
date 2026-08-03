---
name: kubernetes-crd-storage-version-upgrade-preflight
description: "Use when changing a Kubernetes CRD storage/served version, conversion webhook, stored objects, or retiring an old CRD API version requires a lossless migration and rollback gate."
version: "1.0.0"
license: MIT
---

# Kubernetes CRD Storage-Version Upgrade Preflight

Treat a CRD version change as a persisted-data migration and conversion state machine, not a YAML edit. Start read-only. The bundled checker classifies a redacted evidence packet offline; it never contacts a cluster or mutates a CRD.

## When to Use

- A CRD changes which `spec.versions[]` entry has `storage: true`.
- An old served CRD version will be disabled or removed.
- A conversion webhook, schema change, or stored-object rewrite must be proven safe.
- `status.storedVersions`, conversion availability, or field loss blocks an upgrade.

## When Not to Use

- The resource is a built-in Kubernetes API rather than a CustomResourceDefinition.
- The task is only installing an unchanged CRD or debugging ordinary controller reconciliation.
- The user asks to patch production CRDs, rewrite objects, or delete versions without review and backup.
- No representative objects or disposable test boundary exist; inventory only and stop before mutation.

## Prerequisites

- Read access to the CRD, representative redacted objects, API discovery, webhook Service/Endpoints, and relevant events.
- Exact Kubernetes version and feature-gate state. The `StorageVersionMigration` API is version-dependent; never assume it is enabled.
- An owner-approved API/etcd backup and a disposable cluster matching production conversion behavior.
- Ownership and rollback contacts for the CRD, controller, webhook, and clients.
- Python 3.10+ for the optional offline checker.

## Quick Reference

1. Freeze the CRD, object-count, client, webhook, and backup inventory.
2. Prove every served-version round trip preserves intended fields, defaults, nulls, and unknown/pruned-field behavior.
3. Prove conversion remains available under restart and controlled outage conditions.
4. Change storage only on a disposable boundary, rewrite all stored objects with a supported method, and recount.
5. Confirm the old version is absent from `status.storedVersions` before making it unserved; retain conversion rollback support until verification ends.
6. Classify the evidence:

```bash
python3 scripts/check_crd_upgrade.py --input preflight.json --output report.json
```

Exit `0` means `pass` or `not_applicable`; `1` means evidenced blockers; `2` means malformed/unreadable input or report-write failure. Every result sets `mutation_permitted: false`.

## Evidence Packet

Use `schema_version: 1`, `kind: kubernetes_crd_storage_upgrade_preflight`, and `target_type: kubernetes_crd_upgrade`. Required sections are:

- `cluster`: pinned version, disposable-boundary flag, and verified backup;
- `crd`: current/desired storage versions, served/stored inventories, conversion strategy, and webhook checks;
- `migration`: selected method, feature availability, before/after counts, and rewrite completion;
- `round_trip_fixtures`: unique synthetic fixtures covering every served version and unknown/pruned fields;
- `retirement`: old-version served/stored/client state and retained conversion support;
- `rollback`: documented rollback and rehearsed restore.

The checker rejects unknown fields, duplicate keys or fixture IDs, loose booleans, invalid shapes, and non-standard JSON numbers such as `NaN`. Do not include kubeconfigs, tokens, Secrets, private keys, raw production objects, customer data, or full logs.

## Procedure

### 1. Freeze ownership and the persisted-data boundary

Record CRD name/UID/generation, manager and delivery mechanism, exact Kubernetes version, current and proposed `spec.versions`, the single `storage: true` version, `status.storedVersions`, conversion strategy, webhook deployment owner, and object counts by namespace. Inventory clients, controllers, admission policies, exports, backups, and GitOps/Helm jobs that read or reapply the CRD.

Do not let a second manager silently take CRD ownership during the migration. Capture an API/etcd backup supported by the cluster owner and prove restore on a disposable boundary.

**Completion:** one timestamped inventory maps every mutation surface, owner, count, and rollback artifact.

### 2. Diff schemas as data transformations

For every served-version pair, compare field names, types, requiredness, defaults, enums, list/map semantics, nullable behavior, pruning, and validation rules. Classify each change as identity, renamed, defaulted, widened, narrowed, dropped, or computed. A webhook is required when representations need non-structural transformation; `None` conversion does not rename fields.

Create small synthetic objects for ordinary, sparse, maximal, default/null, renamed-field, and unknown-field cases. Exclude secrets and tenant data.

**Completion:** every non-identity field change has an explicit forward and reverse expectation.

### 3. Prove lossless served-version round trips

On the disposable cluster, submit each valid fixture through the API server as version A, read it as B, then read it back as A. Compare normalized semantic values—not YAML formatting or server-generated metadata. Repeat in both directions for every served version. Test invalid objects separately and require the intended schema/conversion rejection; parse or transport failures are test failures, not evidence of rejection.

Record defaulting and pruning explicitly. If a field intentionally cannot round-trip, document the irreversible migration and obtain owner approval; do not classify it as lossless.

**Completion:** all intended values survive A→B→A and B→A→B, with unknown/pruned behavior observed.

### 4. Validate webhook availability and trust

For `Webhook` conversion, verify Service namespace/name/port, ready endpoints, CABundle trust, serving certificate SAN/expiry, network policy, ownership, timeouts, replica disruption, and controller/webhook startup dependencies. Exercise conversion after a pod restart and during a bounded unavailable-endpoint probe on the disposable cluster. Confirm unrelated API discovery/list operations recover after restoration.

Never weaken TLS, disable hostname verification, broaden network access, or test outage in production to make the probe pass.

**Completion:** conversion succeeds when healthy, fails observably and boundedly when unavailable, and recovers without data loss.

### 5. Change storage and rewrite objects safely

First add and serve the new version with conversion working. Then make exactly one version `storage: true` through the normal reviewed delivery owner. Changing the storage marker affects new writes; it does not by itself rewrite existing objects.

Select a migration mechanism supported by the pinned cluster. If using `StorageVersionMigration`, verify its API/feature gate and controller are actually available. Otherwise use a reviewed controlled rewrite that preserves resource versions, finalizers, ownership, and controller invariants. Never use blind export/delete/recreate or bulk patch production objects from this skill.

Process a bounded canary, watch conversion/API errors and controller health, then proceed under normal change control. Recount before/after and investigate any mismatch.

**Completion:** all objects were rewritten through the API server, counts match, and the desired version is represented in `status.storedVersions`.

### 6. Gate old-version retirement

Before setting the old version `served: false`, prove:

- no stored object remains encoded at the old version and the old value is absent from `status.storedVersions`;
- discovery, audit, metrics, logs, and owner attestations show no remaining client/controller dependency;
- every served-version round trip and representative controller reconciliation still passes;
- conversion support and the prior CRD delivery artifact remain available for rollback.

Only after those checks may a separate reviewed change stop serving the version. Remove it from `spec.versions` and drop conversion support only after an observation window and owner approval.

**Completion:** retirement is a separate evidence-backed change, never coupled to the first storage flip.

### 7. Verify and retain rollback evidence

Re-list all objects, compare counts and semantic fixture hashes, inspect `status.storedVersions`, exercise reads/writes through remaining served versions, restart the controller/webhook on the disposable boundary, and check API-server/conversion errors. Preserve only redacted evidence.

If any check fails, stop writes, restore webhook availability or the prior served/storage configuration through the owning delivery system, retain old conversion code, and follow the rehearsed backup restore decision. Do not manually edit `status.storedVersions` as a substitute for rewriting data.

**Completion:** verification passes after restart and rollback remains executable until the observation window closes.

## Objective Verification

Pass only when the pinned evidence packet reports no findings and independent substrate evidence shows:

- exactly one desired storage version and a complete served/stored inventory;
- count-preserving rewrites through a supported mechanism;
- bidirectional semantic round trips for every served version;
- webhook health, trust, outage, and recovery behavior when applicable;
- old storage absent before old serving is disabled;
- client retirement, backup, restore, and rollback evidence.

A checker `pass` is evidence readiness, not authorization to mutate production.

## Failure Recovery and Unsafe Operations

- Never patch CRD status manually, delete/recreate stored objects, disable TLS checks, or drop old conversion code to force an upgrade.
- Never combine storage flip, bulk rewrite, old-version disablement, and conversion removal into one irreversible change.
- If conversion is unavailable, restore the webhook first; avoid writes that depend on unproven conversion.
- If counts differ or a round trip loses data, stop, preserve the before/after fixtures, restore the prior served/storage path, and diagnose schema/defaulting/pruning.
- If `status.storedVersions` remains stale, prove every object rewrite and controller completion before considering any status repair recommended by upstream Kubernetes guidance.
- If a credential or production object enters an artifact, quarantine it and follow the owner's incident process.

## Pitfalls

- `storage: true` changes future persistence; it does not migrate existing records.
- Served, storage, and stored versions are three different states.
- Successful YAML validation does not test conversion, defaulting, pruning, or webhook availability.
- A healthy webhook Deployment does not prove Service endpoints, CA trust, network reachability, or startup independence.
- Object-count equality alone misses field loss; round-trip equality alone misses deleted objects.
- Built-in API storage migration and CRD migration have different ownership and compatibility constraints.

## Evaluation Prompts

See [`references/evaluations.md`](references/evaluations.md) for normal, difficult-edge, and should-not-activate prompts with machine-checkable assertions.

## Sources and Provenance

**Sourced facts:** Kubernetes documents CRD served/storage selection, webhook conversion, object migration, `status.storedVersions`, and the required ordering for version removal. Its current Storage Version Migration page marks the API as version/feature-gate dependent. Project issues demonstrate stale stored versions, cluster-wide effects of broken conversion, and silent field loss across mismatched schemas.

**Original recommendations:** the evidence-packet schema, bidirectional fixture matrix, webhook outage/recovery probe, count-plus-semantic gate, split retirement change, classifier, and recovery hierarchy are original synthesis. No third-party code or prose is bundled.

- [Kubernetes: Versions in CustomResourceDefinitions](https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definition-versioning/)
- [Kubernetes: Storage Version Migration](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/storage-version-migration/)
- [Linkerd #15471: storedVersions blocks later Helm upgrade](https://github.com/linkerd/linkerd2/issues/15471)
- [Rancher #55624: broken conversion webhook affects cluster API consumers](https://github.com/rancher/rancher/issues/55624)
- [KubeBlocks #10405: field loss across served/storage schemas](https://github.com/apecloud/kubeblocks/issues/10405)
