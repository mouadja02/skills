---
name: timezone-database-provenance-conformance
description: Use when named-zone wall times cross browsers, mobile runtimes, containers, or servers and stale or divergent tzdb rules could change offsets or persisted UTC instants.
version: "1.0.0"
license: MIT
platforms: [linux, macos, windows]
---

# Time-Zone Database Provenance Conformance

## When to Use

- A named-zone wall time is converted in more than one browser, mobile runtime, container, library, or server.
- A client-computed UTC instant can be persisted by a runtime with different civil-time rules.
- A recent rule change, DST gap, or repeated time produces runtime-dependent offsets.
- A deployment needs evidence that time-zone data sources agree before writes resume.

Do **not** activate for epoch-only values or fixed offsets with no named-zone conversion, nor for simple formatting where no future wall-clock intent crosses a trust boundary.

## Prerequisites

- The original wall time, IANA zone, and explicit fold/disambiguation choice.
- Runtime/provider identity for every conversion boundary.
- Synthetic dates safe to evaluate offline. Do not use production records in fixtures.
- Python 3.9+ only when using the optional offline comparator.

## Quick Reference

| Question | Required evidence |
| --- | --- |
| Which rules ran? | runtime, provider/source path or package, declared tzdb version when exposed |
| Do rules agree? | gap, fold variants, recent-rule boundary, offset and resulting UTC instant |
| Version unavailable? | Record `null`; never infer a release from one matching result |
| May a write proceed? | Only after the selected policy and all transition probes allow it |
| Recovery | Preserve wall + zone + fold, align the intended data source, rerun identical probes |

## Procedure

1. **Classify the value.** Stop with `not_applicable` for epoch/fixed-offset-only data. For named zones, preserve the wall fields, IANA zone, and fold/disambiguation separately from any computed instant.
2. **Inventory every boundary.** Record runtime/version, provider, selected source path or package, and declared tzdb version. Use `unknown`, not a guessed release, when the runtime does not expose one.
3. **Freeze probes before comparing.** Include one known nonexistent wall time (`gap`), both alternatives of one repeated wall time (`fold`), and a date spanning the rule change relevant to the incident (`recent-rule`). Add an ordinary control.
4. **Observe each runtime independently.** For every probe record validity, offset seconds, and UTC instant. Do not let one runtime generate another runtime's expected values.
5. **Compare behavior and provenance separately.** Equal outputs are behavioral evidence, not proof that providers or releases are identical. Divergent validity, offset, or instant is a violation. Unknown provenance is an observation unless project policy explicitly requires a declared version.
6. **Gate persistence.** Block writes whenever required transition coverage is missing, a probe diverges, or a provenance requirement fails. Preserve the user's wall time, zone, and fold for review; do not silently replace them with the server's current conversion.
7. **Recover non-destructively.** Pin or update the application/container dependency through normal deployment controls, or route conversion to the selected authoritative runtime. Never rewrite host tzdata in place. Rerun the exact frozen probes before allowing writes.

### Offline comparator

Prepare a synthetic JSON document with two or more observations:

```json
{
  "schema_version": 1,
  "mode": "named-zone",
  "policy": {"require_declared_version": true},
  "observations": [
    {
      "runtime_id": "browser-a",
      "provider": "Intl",
      "version": null,
      "zone": "America/Vancouver",
      "probes": [
        {"id":"gap","kind":"gap","wall":"2026-03-08T02:30:00","fold":null,"valid":false,"offset_seconds":null,"utc":null}
      ]
    }
  ]
}
```

A complete document must include matching `gap`, `fold`, and `recent-rule` probe IDs in every observation. Run:

```bash
python3 scripts/tzdb_compare.py observations.json
```

Exit `0` means `allow` or `not_applicable`; `1` means policy blocked; `2` means invalid input; `74` means output could not be written. The helper is offline, rejects unknown fields and non-finite JSON, and never loads zone files or changes system state.

## Pitfalls and Safety

- A zone name is not a version. `America/Vancouver` can resolve through different rule sets.
- One matching present-day offset does not cover future transitions, historical corrections, gaps, or folds.
- Do not call a client wrong merely because its source differs; identify the product's selected authority and compare frozen behavior.
- Never auto-update host files, rewrite stored instants, or probe production writes. Use normal package/image rollout and rollback.
- Hashes can identify byte equality but do not reveal a release; log only non-sensitive source metadata.

## Verification

Completion requires all of the following:

- provenance is explicit or honestly `unknown` for every boundary;
- gap, both fold choices, and a relevant rule boundary were observed independently;
- offsets **and** resulting instants were compared;
- an unresolved mismatch demonstrably blocks persistence;
- recovery reruns the unchanged probes and reaches `allow` without mutating host data.

Run packaged tests from the installed skill directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tests/test_tzdb_compare.py
```

## Evaluation Prompts

1. **Normal:** Browser-to-server named-zone persistence where tzdb versions may differ; require provenance, transition probes, and a write gate.
2. **Difficult edge:** Android APEX versus system fallback and a container with no exposed release; require `unknown` provenance plus gap/fold/recent-rule evidence.
3. **Should not activate:** Epoch seconds with fixed `+00:00` and no named-zone wall-clock conversion.

## Sourced Facts and Recommendations

**Sourced facts:** Android can update time-zone rules independently of a full system update; the IANA tz database records historical and predicted civil-time rules; independent Jiff and Event Espresso reports show stale-source and browser/server divergence failures.

**Recommendations:** the exact probe set, `require_declared_version` policy, persistence gate, and non-destructive recovery sequence above are conservative project controls synthesized for this skill.

## Sources

- [Android time-zone rules](https://source.android.com/docs/core/permissions/timezone-rules)
- [IANA Theory and pragmatics of the tz code and data](https://data.iana.org/time-zones/tzdb/theory.html)
- [Jiff issue 582: Android stale tzdata source](https://github.com/BurntSushi/jiff/issues/582)
- [Event Espresso issue 4197: stale browser database changes persisted instants](https://github.com/eventespresso/event-espresso-core/issues/4197)
