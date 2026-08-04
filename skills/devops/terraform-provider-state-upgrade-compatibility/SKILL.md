---
name: terraform-provider-state-upgrade-compatibility
description: Use when a Terraform provider maintainer changes a resource state schema and must prove historical state decoding, upgrader coverage, released-version migration, and a no-op plan before release.
version: "1.0.0"
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [terraform, provider-development, state-migration, compatibility, testing]
---

# Terraform Provider State Upgrade Compatibility

## When to Use

- A provider resource increments its persisted schema version or removes, renames, or reshapes an attribute.
- An upgrade fails before planning with an unsupported attribute, schema-version mismatch, or state decoding error.
- A maintainer needs regression evidence from one or more released provider versions to the candidate build.
- A release gate must distinguish fixture decoding, upgrader execution, and post-upgrade plan behavior.

Do **not** activate for routine Terraform module migration, backend movement, state locking, import, or emergency repair of a user's live state. This workflow tests provider code. It does not authorize hand-editing production state.

## Prerequisites

- The provider source and its native Go test toolchain.
- The exact plugin API and version in use: Plugin Framework and Plugin SDK expose different upgrader shapes.
- Secret-free state fixtures captured or reconstructed from every supported historical resource schema.
- A disposable acceptance-test account when unit tests cannot prove remote behavior.
- A documented state backup and restore rehearsal before any test uses a real state file.

## Quick Reference

| Gate | Required evidence |
| --- | --- |
| Lineage | Current version, every supported prior version, and the API's actual upgrade strategy |
| Historical decode | Exact old schema decodes the old fixture before conversion |
| Conversion | Every required old-version path reaches the current schema |
| Semantics | Raw and typed values agree; null, unknown, removed, and renamed fields are exercised |
| Stability | Re-running conversion is idempotent and the upgraded state has no unintended plan |
| Release path | A pinned released provider creates state; the candidate upgrades it |
| Recovery | Backup and restore are rehearsed outside production |

Run the bundled packet checker after the native tests produce evidence:

```bash
python3 scripts/check_state_upgrade_evidence.py evidence.json
```

Exit `0` means `pass` or `not_applicable`, `1` means the packet is valid but the release gate failed, and `2` means malformed input or an I/O failure. Always inspect `status`; `not_applicable` is not a release pass.

## Procedure

### 1. Freeze the compatibility boundary

Record the resource name, current schema version, earliest supported provider release, plugin API/version, and upgrade strategy:

- `sequential`: each adjacent version has an evidenced transition;
- `direct_to_current`: every supported historical version has a direct path to the current version.

Determine this from the provider's installed API contract and implementation, not from naming assumptions. HashiCorp's Plugin Framework documentation requires a prior schema for state upgrading and warns that a resource without upgrade support can fail when Terraform encounters an older schema [1]. Recent Cloudflare, Elastic, and AWS provider reports demonstrate missing registration, historical-shape decoding, and version-path failures across independent providers [2][3][4].

**Completion:** a version matrix names every required path; no version is silently declared unsupported.

### 2. Preserve exact historical schemas and fixtures

For each old version:

1. recover the schema definition from the released source or artifact;
2. create a minimal secret-free fixture in that exact shape;
3. add cases for absent, null, unknown, renamed, removed, nested collection, and defaulted values that existed in that version;
4. assert the historical decoder accepts the fixture before invoking an upgrader.

Do not approximate an old schema by subtracting fields from the current schema. Do not use a current typed model to deserialize old raw state before the historical-schema assertion; that can erase the failure being tested.

**Completion:** each fixture identifies its source provider version and schema version, and fails when decoded with the wrong historical shape.

### 3. Test every path with the provider's native harness

Use the native Framework or SDK test interface already imported by the provider. For each required path, assert separately:

1. upgrader registration exists at the expected key/version;
2. old raw state decodes under the exact historical schema;
3. conversion completes without diagnostics;
4. the output reports the current schema version;
5. raw JSON and typed state represent the same values;
6. removed fields are absent and renamed fields retain their intended values;
7. null and unknown values are preserved or deliberately transformed according to the resource contract;
8. a second conversion is either rejected as already current or produces byte/semantic-equivalent current state.

Never call a later upgrader on state that has not passed the preceding transition when the API is sequential. Never invent adjacent transitions when the API upgrades each prior version directly to current.

**Completion:** one failing transition identifies one version boundary rather than only producing an end-to-end decode error.

### 4. Prove plan behavior separately

A successful conversion does not prove semantic compatibility. Feed the upgraded state into the closest supported plan check and assert:

- no unintended replacement;
- no removed attribute reappears;
- no perpetual diff is introduced by defaults, collection ordering, or null/unknown conversion;
- any expected change is explicitly reviewed and documented.

Terraform Plugin Testing tracks a gap in observing plan behavior during schema migration [5]. If the installed harness cannot perform a no-op plan assertion, report `unsupported`; do not convert the limitation into a pass. Add the smallest available acceptance test or block the release until equivalent evidence exists.

### 5. Test a released-provider transition

In an isolated directory and disposable account:

1. pin the oldest supported or specifically affected released provider;
2. apply the smallest resource configuration and save a protected backup of its state;
3. switch only the provider binary/version to the candidate build;
4. run refresh/plan and capture redacted diagnostics;
5. require migration success and the reviewed plan outcome;
6. restore or destroy through the owning Terraform workflow.

Do not commit `.terraform/`, state, plans, credentials, or provider binaries. Never mutate remote objects merely to make an upgrader test pass.

**Completion:** the evidence names exact source and target provider versions and proves the state originated from the source release.

### 6. Emit and validate the evidence packet

The checker expects `task_kind: provider_state_upgrade_preflight`, a bounded `current_schema_version`, `upgrade_strategy`, ordered transitions, released-provider evidence, and `backup_restore_rehearsed: true`. Each transition records booleans only after its corresponding native assertion ran; the packet is an evidence index, not a substitute for the tests.

```json
{
  "task_kind": "provider_state_upgrade_preflight",
  "resource": "example_widget",
  "current_schema_version": 2,
  "upgrade_strategy": "sequential",
  "transitions": [{"from": 0, "to": 1, "historical_schema_exact": true}],
  "released_provider": {"source_version": "1.4.0", "target_version": "2.0.0"},
  "backup_restore_rehearsed": true
}
```

Use `tests/fixtures/normal.json` as the complete field reference. The checker rejects duplicate or missing paths, false/non-boolean evidence, non-standard JSON constants, unsupported plans, and output-write failures.

## Verification

Run from the installed skill directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/check_state_upgrade_evidence.py tests/fixtures/normal.json
python3 scripts/check_state_upgrade_evidence.py tests/fixtures/edge.json  # expected exit 1
```

Release only when:

- the provider's native unit and acceptance tests pass;
- every required transition is covered for the declared strategy;
- the released-provider path is evidenced;
- the checker returns `status: pass`;
- the restore rehearsal is documented and no secret-bearing artifacts remain.

## Failure Recovery and Pitfalls

- **Decode fails before the upgrader:** verify the fixture's stored version and exact historical schema; do not widen the current schema to accept stale fields.
- **A version key is missing:** add an intentional tested path or explicitly drop support in a separately reviewed compatibility decision; never renumber state to bypass conversion.
- **Plan changes after conversion:** preserve the fixture and diagnostics, stop release, and isolate defaulting, collection normalization, or semantic field mapping.
- **Released-provider setup fails:** classify setup failure separately from migration failure. A failed fixture creation is not evidence that migration is invalid.
- **Live state is already broken:** stop this workflow. Back up state, follow the provider/Terraform recovery process, and obtain explicit owner approval before any state operation.
- **Sensitive fixture content:** replace it with structurally equivalent synthetic values and rotate any exposed credential. Do not add redacted production state if its structure still discloses identities.

## Evaluation Prompts

1. **Normal:** “A resource moves from schema 0 to 2 with two adjacent upgraders. Check exact historical decoding, null/unknown behavior, idempotence, released-provider migration, and no-op plans.”
2. **Difficult edge:** “The provider declares version 3, registers 0→2 and 2→3, approximates schema 0 with the current model, cannot inspect a migration plan, and has not rehearsed restore. Produce a fail-closed finding list.”
3. **Should not activate:** “Please hand-edit this live Terraform state to recover a user's deleted object.”

## Sources and Recommendation Boundary

**Sourced facts:** HashiCorp's state-upgrade contract and the linked issue states, titles, and reported failure modes [1]–[5].

**Recommendations:** the matrix, fixture taxonomy, raw/typed comparison, idempotence gate, evidence packet, backup rehearsal, and release decision procedure are original operational guidance synthesized for this skill.

1. [HashiCorp — State upgrade](https://developer.hashicorp.com/terraform/plugin/framework/resources/state-upgrade) (accessed 2026-08-04)
2. [Cloudflare provider issue #7090 — missing state upgrader](https://github.com/cloudflare/terraform-provider-cloudflare/issues/7090) (accessed 2026-08-04)
3. [Elastic Stack provider issue #4161 — historical state decode failure](https://github.com/elastic/terraform-provider-elasticstack/issues/4161) (accessed 2026-08-04)
4. [Terraform AWS provider issue #48004 — migration path failure](https://github.com/hashicorp/terraform-provider-aws/issues/48004) (accessed 2026-08-04)
5. [Terraform Plugin Testing issue #426 — migration plan checking proposal](https://github.com/hashicorp/terraform-plugin-testing/issues/426) (accessed 2026-08-04)
