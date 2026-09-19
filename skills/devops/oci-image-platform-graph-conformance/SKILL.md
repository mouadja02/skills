---
name: oci-image-platform-graph-conformance
description: "Use when multi-platform OCI images select the wrong architecture, descriptor platforms disagree with child configs, or copy/push/pull operations silently strip image-index variants."
version: "1.0.0"
license: MIT
---

# OCI Image Platform Graph Conformance

Preflight OCI image-index platform selection and graph preservation with redacted JSON observations. The bundled analyzer is offline and never contacts a registry or mutates an image.

## When to Use

- A pull reports “no matching manifest” although the expected architecture was built.
- An index descriptor says `amd64` while the referenced image config says `arm64`.
- A push, copy, or pull turns a multi-platform index into one platform.
- Duplicate matches, ARM variants, nested indexes, or non-image descriptors make platform selection ambiguous.

## When Not to Use

- A single image manifest needs layer, filesystem, vulnerability, or runtime validation.
- Signatures, SBOMs, or attestations disappeared while the platform graph stayed intact; use `oci-referrers-portability-conformance`.
- The task is to publish or repair production images automatically. This workflow is read-only by default.

## Prerequisites

- OCI image-index JSON plus referenced child image-config platform fields, captured by immutable digest.
- A declared consumer matcher profile. The helper provides only conservative `exact` matching; runtime compatibility rules are implementation-defined.
- Before and after snapshots for copy/push/pull preservation checks.
- Python 3.10+ for the optional analyzer.

## Quick Reference

1. Resolve tags to immutable index digests; record tool and registry versions.
2. Capture index descriptors and each image child config without layers or credentials.
3. Declare the requested platform and matcher policy.
4. Run:

```bash
python3 scripts/check_oci_platform_graph.py --input audit.json --output report.json
```

Exit `0` means `pass`, `review`, or `not_applicable`; `1` means a conformance finding; `2` means malformed/unreadable input, unsupported profile, or output failure.

## Observation Schema

```json
{
  "schema_version": 1,
  "kind": "oci_image_platform_graph_audit",
  "profile": "oci-image-spec-1.1.1",
  "matcher": "exact",
  "request": {"os": "linux", "architecture": "arm64", "variant": "v8"},
  "before": {
    "index": {
      "schemaVersion": 2,
      "mediaType": "application/vnd.oci.image.index.v1+json",
      "manifests": [{
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "digest": "sha256:<64 lowercase hex>",
        "size": 7143,
        "platform": {"os": "linux", "architecture": "arm64", "variant": "v8"}
      }]
    },
    "children": {
      "sha256:<same digest>": {
        "schemaVersion": 2,
        "config": {"os": "linux", "architecture": "arm64", "variant": "v8"}
      }
    }
  },
  "after": {
    "index": {"schemaVersion": 2, "manifests": []},
    "children": {}
  }
}
```

`after` is optional. Include only index metadata and platform fields—never registry authorization, image layers, environment variables, or private image names.

## Procedure

### 1. Freeze identities and policy

Record the requested build platform, final image target, host/build platform, index digest, producer/consumer versions, and exact operation. Keep `FROM --platform`, build target, descriptor platform, and child config separate: they are not interchangeable.

Choose matcher behavior before analysis. OCI specifies descriptor fields and says the first matching entry should be used when multiple entries match, but detailed host compatibility is implementation-defined. The helper’s `exact` profile compares every supplied request field literally; it does not claim universal runtime behavior.

**Complete when:** immutable identities and one explicit matcher profile are recorded.

### 2. Capture the complete graph

Fetch the top-level object by digest. For every descriptor, capture media type, digest, size, position, and optional platform. For image manifests, fetch the referenced manifest and config by digest and record only config `os`, `architecture`, `variant`, `os.version`, and `os.features`. Preserve nested indexes and unknown media types as graph nodes rather than rejecting them.

A missing `platform` is not automatically invalid for an artifact or unknown media type. It is a finding for an observed platform-specific image manifest because selection cannot be verified.

**Complete when:** every image descriptor has either a child config observation or an explicit missing-content finding.

### 3. Validate descriptor-to-config agreement

Run the analyzer. Require descriptor and child config platform tuples to agree. Treat descriptor metadata—not `uname`, host architecture, filename, or tag text—as the consumer’s index-selection input. A mismatch is a publication failure even when emulation happens to run the selected image.

**Complete when:** every image descriptor agrees with its child config or has a localized finding.

### 4. Evaluate selection without inventing compatibility

Apply the declared matcher in index order. Zero matches is a failure. Multiple exact matches produce `AMBIGUOUS_PLATFORM_MATCH`; the report still records the first digest to preserve the OCI first-match rule. Do not collapse an omitted variant and an explicit variant unless the named runtime profile documents that behavior.

Keep observations separate from violations. A platform on an unknown/non-image media type is observable but not universally invalid; an unsupported media type must not itself make the index invalid.

**Complete when:** the selected digest, match count, and ambiguity are machine-checkable.

### 5. Compare before and after graphs

Capture the result of the real copy/push/pull path by immutable digest. Compare every original descriptor’s digest, metadata, relative order, and child observation. Missing nodes, metadata drift, lost child observations, and relative-order changes are failures. Added descriptors are `review` observations until ownership and intent are established.

Do not call a single-platform result equivalent to its source index. Graph shape and descriptor coverage are part of the publication contract even if one platform still runs.

**Complete when:** all original descriptors and child observations survive or the first lossy boundary is identified.

### 6. Recover through staging

Freeze promotion when descriptor/config mismatch or graph loss appears. Correct the producer target declaration or copy policy in disposable staging, republish under a new immutable digest, rerun the comparison, and canary every required platform. Roll back by restoring the prior digest reference; never edit content-addressed objects in place.

**Complete when:** a fresh staging graph passes and each intended consumer selects the expected digest.

## Objective Verification

Pass only when:

- index schema/media type and every descriptor shape are valid;
- image descriptor platforms equal observed child config platforms;
- the declared matcher selects exactly the expected first descriptor;
- before/after descriptor identity, metadata, order, and child coverage are preserved;
- unknown media types and non-platform artifacts are preserved without being mislabeled as invalid;
- no registry or image mutation occurred during offline analysis.

## Safety and Recovery

- Never include registry tokens, Docker configuration, signed URLs, image layers, secrets, or private repository names in fixtures.
- Never infer child config architecture from the host, emulator, tag, or build log.
- Never overwrite a production tag to test a repair. Publish a new staging digest and compare first.
- Treat malformed JSON, missing child observations, unsupported matcher profiles, and write failures as hard failures—not expected-invalid passes.
- If a tool stripped variants, retain the authoritative source digest, stop promotion, fix the transfer mode, and republish to a fresh staging reference.

## Pitfalls

- `FROM --platform` selects a build-stage base; it does not necessarily declare the final build target.
- A runnable image under QEMU does not prove its descriptor platform is correct.
- Two descriptors can both exactly match; index order then affects selection.
- ARM and x86 variants are not universally interchangeable.
- `os.version` and feature compatibility are runtime policy, not a universal OCI violation.
- A tag showing one platform after a pull may represent local tag replacement rather than a preserved multi-platform graph.

## Evaluation Prompts

See [`references/evaluations.md`](references/evaluations.md) for normal, difficult-edge, and should-not-activate cases.

## Sources and Provenance

**Sourced facts:** OCI Image Specification v1.1.1 defines image indexes, descriptor platform fields, optional platform metadata, unknown-media-type tolerance, and first-match ordering. BuildKit, Buildah, Moby, and Podman issues demonstrate descriptor/config disagreement, wrong-platform selection, silent variant stripping, and local replacement behavior.

**Original recommendations:** the normalized observation schema, exact matcher profile, descriptor/config comparison, graph-preservation oracle, staging gate, and recovery sequence are original MIT-licensed workflow design. No source prose or implementation code is copied.

- [OCI Image Index Specification v1.1.1](https://github.com/opencontainers/image-spec/blob/v1.1.1/image-index.md)
- [BuildKit issue 6518: descriptor and child config platform mismatch](https://github.com/moby/buildkit/issues/6518)
- [Buildah issue 6091: wrong platform selected from an index](https://github.com/containers/buildah/issues/6091)
- [Moby issue 48731: push discards platform variants](https://github.com/moby/moby/issues/48731)
- [Podman issue 26621: platform pulls replace local image tags](https://github.com/containers/podman/issues/26621)
