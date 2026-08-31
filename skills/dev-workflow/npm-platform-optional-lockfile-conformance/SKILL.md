---
name: npm-platform-optional-lockfile-conformance
description: Use when an npm package-lock omits or misstates OS/CPU/libc-specific optional packages, npm ci fails only on another platform, or a native binary is absent after lockfile regeneration.
version: "1.0.0"
license: MIT
platforms: [linux, macos, windows]
---

# npm Platform Optional Lockfile Conformance

## When to Use

- A committed `package-lock.json` works on its producer host but fails on another OS, architecture, or libc.
- A native package family (for example platform-specific binary packages) is incomplete, stale, or has contradictory `os`/`cpu`/`libc` selectors.
- A lockfile was regenerated while `node_modules` existed and cross-platform optional entries may have disappeared.
- Release, offline, or installer packaging must prove coverage for a declared platform matrix.

Do **not** activate merely because a project uses npm or has ordinary optional dependencies. This workflow does not audit package vulnerabilities, choose native binaries, or replace clean target-platform installation tests.

## Prerequisites

- Python 3.9+ for the offline auditor.
- `package.json` and lockfile v2 or v3 data copied into a redacted audit input.
- An explicit list of the native package family members and intended selectors, taken from reviewed package metadata or project policy.
- The release target matrix. Do not infer it from the current host.

## Quick Reference

```bash
python3 scripts/audit_optional_lockfile.py audit-input.json --pretty
# 0 = conformant/not applicable, 1 = findings, 2 = invalid input, 74 = output failure
python3 tests/test_audit_optional_lockfile.py
```

The helper is offline and read-only. It never runs npm, resolves registry metadata, edits a lockfile, or installs packages.

## Procedure

### 1. Establish the evidence boundary

Record the npm version, lockfile version, producer OS/CPU/libc, whether `node_modules` existed during regeneration, and intended release targets. A successful `npm ci` on one host proves only that host's selected graph; it does not prove other targets.

Treat a current-host-only lockfile as **inconclusive** until the declared family and target matrix are checked. Do not manually invent lock entries.

### 2. Build an explicit audit input

Create a JSON document:

```json
{
  "package_json": {
    "optionalDependencies": {
      "@acme/native-linux-x64-gnu": "2.0.0",
      "@acme/native-darwin-arm64": "2.0.0"
    }
  },
  "lockfile": {
    "lockfileVersion": 3,
    "packages": {
      "": {},
      "node_modules/@acme/native-linux-x64-gnu": {
        "version": "2.0.0",
        "optional": true,
        "os": ["linux"],
        "cpu": ["x64"],
        "libc": ["glibc"]
      }
    }
  },
  "families": [{
    "name": "acme-native",
    "members": [
      {"package": "@acme/native-linux-x64-gnu", "os": ["linux"], "cpu": ["x64"], "libc": ["glibc"]},
      {"package": "@acme/native-darwin-arm64", "os": ["darwin"], "cpu": ["arm64"]}
    ]
  }],
  "targets": [
    {"os": "linux", "cpu": "x64", "libc": "glibc"},
    {"os": "darwin", "cpu": "arm64"}
  ]
}
```

`families` is a reviewed expectation, not package-name guessing. Keep unrelated workspace optionals outside a family unless they are part of the same release invariant.

### 3. Run the offline audit

```bash
python3 scripts/audit_optional_lockfile.py audit-input.json --pretty > audit-result.json
status=$?
```

Interpret stable finding codes:

| Code | Meaning |
| --- | --- |
| `MISSING_LOCK_ENTRY` | A declared family member is absent from `lockfile.packages`. |
| `VERSION_MISMATCH` | An exact root optional version differs from the locked version. |
| `SELECTOR_MISMATCH` | Locked `os`, `cpu`, or `libc` metadata differs from the reviewed member contract. |
| `NOT_OPTIONAL` | A family member is not marked optional in the lockfile. |
| `TARGET_UNCOVERED` | No valid declared family member matches a release target. |

An exit status of 1 means the input parsed and findings exist. Status 2 means no conformance conclusion is valid; fix the audit input first.

### 4. Recover safely

1. Preserve the suspect lockfile and diff.
2. Use a disposable clean checkout with no `node_modules`.
3. Regenerate with the project-pinned npm version.
4. Re-run the offline audit.
5. Run `npm ci` in clean native or trusted emulated CI jobs for every target.
6. Review the complete lockfile diff before accepting it.

Never delete a user's working `node_modules`, rewrite production lockfiles, or fetch packages merely to make this helper pass. Registry metadata can change; pin the package and npm versions used for supplemental live tests.

### 5. Verify completion

Completion requires all of the following:

- the auditor returns 0 with `classification: "conformant"` for the declared family and target matrix;
- every intended family member has the expected exact version and selectors;
- clean target jobs install and load the expected native package;
- the lockfile diff contains no unrelated dependency churn;
- installer/offline packaging includes the selected target artifact.

The deterministic audit validates declared metadata coverage, not npm resolver correctness or runtime binary compatibility.

## Pitfalls and Safety

- **Do not infer a complete family from names.** Supply reviewed members explicitly.
- **Do not equate absence with a defect for unrelated optionals.** Scope findings to declared families.
- **Do not treat selectors as universal.** `libc` may be absent where it is not relevant; compare against the member contract.
- **Do not use the current host as the target matrix.** Cross-platform claims require explicit targets.
- **Do not hand-edit generated lockfile entries.** Regenerate cleanly, then inspect the diff.
- **Fail closed on malformed/non-finite JSON.** Parse or I/O failures are not expected-invalid passes.

## Evaluation Prompts

1. **Normal:** Review a lockfile regenerated on Linux with the Linux family member present and the declared macOS member absent; classify the evidence and propose safe recovery.
2. **Difficult edge:** Audit Linux glibc, Linux musl, macOS, and Windows family members containing one missing entry, one stale version, and one selector mismatch while ignoring an unrelated workspace optional.
3. **Should not activate:** A platform-neutral project has no optional dependencies, selectors, native family, or cross-platform failure; explain that this workflow is not applicable.

## Sourced Facts vs Recommendations

Official npm documentation defines lockfile structure and the `os`, `cpu`, and `optionalDependencies` fields. The issue records below demonstrate failures seen in independent projects. The explicit family contract, target matrix, fail-closed policy, clean-regeneration sequence, and stable finding codes are this skill's recommendations.

## Sources

- [npm package-lock.json documentation](https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json)
- [npm package.json `os`, `cpu`, and `optionalDependencies`](https://docs.npmjs.com/cli/v11/configuring-npm/package-json)
- [npm/cli issue 4828](https://github.com/npm/cli/issues/4828)
- [Bitwarden clients issue 13350](https://github.com/bitwarden/clients/issues/13350)
- [Tailwind CSS issue 20324](https://github.com/tailwindlabs/tailwindcss/issues/20324)
- [Hermes Agent issue 53089](https://github.com/NousResearch/hermes-agent/issues/53089)

See [references/evidence.md](references/evidence.md) for scope, status, and licensing notes.
