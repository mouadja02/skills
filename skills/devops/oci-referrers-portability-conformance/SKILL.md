---
name: oci-referrers-portability-conformance
description: "Use when OCI 1.1 signatures, attestations, or SBOM referrers disappear, duplicate, or drift across registries, proxies, replication, copy tools, fallback tags, or multi-platform images."
version: "1.0.0"
license: MIT
---

# OCI Referrers Portability Conformance

Inventory an OCI subject/referrer graph before and after a transport boundary, then compare descriptor identity and per-platform coverage without mutating a registry. The bundled helper analyzes redacted observations offline; it does not make network calls or copy artifacts.

## When to Use

- OCI 1.1 signatures, attestations, or SBOMs disappear after copy, replication, or proxy-cache access.
- A registry returns 404 from `/referrers/<digest>` and clients disagree about fallback tags.
- Referrer descriptors duplicate or lose `artifactType` and annotations.
- Multi-platform image indexes pass checks while platform-manifest referrers remain undiscovered.

## When Not to Use

- The task is generic image push/pull setup with no subject/referrer graph.
- The user only needs vulnerability matching inside an SBOM; use an SBOM analysis workflow.
- A production registry should be written to automatically. This workflow is read-only first and requires explicit staging authorization for mutation probes.
- The artifact uses only vendor tag conventions with no OCI subject relationship; document that separate storage model instead of labeling it OCI 1.1 conformance.

## Prerequisites

- Exact registry, proxy, replication, copy-tool, signing-tool, and OCI client versions.
- A synthetic or non-production subject digest and authorization for read-only manifest/referrer requests.
- Redacted raw status, response header, and descriptor observations from every hop.
- Python 3.10+ for the optional offline comparator.

## Quick Reference

1. Pin OCI Distribution Specification v1.1.1 and every component version.
2. Resolve the image index digest and all platform-manifest digests.
3. Probe the referrers API; on exactly 404, inspect the digest-derived fallback tag.
4. Capture descriptor digest, media type, size, `artifactType`, and annotations without payloads or credentials.
5. Repeat at each boundary and run:

```bash
python3 scripts/check_referrers.py --input observations/referrers.json --output report.json
```

Exit `0` means `pass`, `review`, or `not_applicable`; `1` means conformance failure; `2` means malformed/unreadable input, unknown profile, or report-write failure. The report always sets `mutation_permitted: false`.

## Observation Schema

```json
{
  "schema_version": 1,
  "kind": "oci_referrers_audit",
  "profile": "oci-distribution-1.1.1",
  "subject": "sha256:<64 hex characters>",
  "platform_subjects": ["sha256:<platform manifest digest>"],
  "source": {
    "api_status": 200,
    "content_type": "application/vnd.oci.image.index.v1+json",
    "referrers": [{
      "mediaType": "application/vnd.oci.image.manifest.v1+json",
      "digest": "sha256:<referrer digest>",
      "size": 1234,
      "artifactType": "application/vnd.example.sbom.v1",
      "annotations": {"org.example.format": "spdx"}
    }],
    "platform_coverage": ["sha256:<platform manifest digest>"]
  },
  "destination": {
    "api_status": 404,
    "fallback_status": 200,
    "content_type": "application/vnd.oci.image.index.v1+json",
    "referrers": [],
    "platform_coverage": []
  }
}
```

`referrers` contains the effective image-index descriptors returned by the API or fallback tag. Do not include manifests, signatures, attestations, SBOM contents, authorization headers, cookies, registry credentials, or private repository names. A digest is content identity, not a secret, but use synthetic digests in shared fixtures.

## Procedure

### 1. Freeze the topology and versions

Draw the exact path: client → proxy/cache → source registry → copy or replication service → destination registry → verifier. Record image media type, index digest, platform-manifest digests, repository namespace at each side, and component versions. Do not compare mutable tags; resolve each tag to a digest first.

**Completion:** every observation names one immutable subject digest, one repository boundary, and one version tuple.

### 2. Inventory the complete source graph

For the image index and every platform-manifest digest, request `GET /v2/<name>/referrers/<digest>`. Record status, `Content-Type`, pagination `Link` headers, filter headers when used, and all descriptors across pages. Fetch descriptor manifests by digest only when authorized, solely to confirm their `subject`; do not download artifact payloads by default.

Treat image-index and platform subjects as separate graph nodes. `oras discover` or a signing-tool tree view that reports only the top-level index is not proof of platform coverage.

**Completion:** every declared subject node has an explicit observed result, including an empty list.

### 3. Classify API versus fallback behavior

OCI Distribution 1.1.1 defines a 200 image-index response for supported referrers requests. A 404 is the compatibility boundary that requires the digest-derived fallback tag `<algorithm>-<encoded digest, limited to 64 characters>`. Do not treat 401, 403, 5xx, timeout, invalid JSON, or a wrong media type as “unsupported”; diagnose authentication, transport, or server failure instead.

For a fallback result, require a valid OCI image index. Capture the same descriptor fields expected from the API. If writers share a fallback tag, record whether they use conditional requests; concurrent read-modify-write can lose entries.

**Completion:** each endpoint is classified as API, fallback-tag, or failure without guessing from product/version claims.

### 4. Validate descriptor semantics

For every returned descriptor verify:

- digest, `mediaType`, and non-negative integer `size` identify the referenced manifest;
- duplicate digests are absent;
- `artifactType` reflects the manifest's `artifactType`, or the config media type where the specification requires that fallback;
- manifest/index annotations are preserved on the descriptor;
- the referenced manifest's `subject.digest` equals the queried subject;
- pagination and any applied `artifactType` filter were fully accounted for.

Never infer descriptor metadata from a filename, tag suffix, UI badge, or payload content.

**Completion:** each descriptor traces to one manifest and one queried subject, with no duplicates or silently omitted pages.

### 5. Compare every transport boundary

Normalize source and destination observations into the schema and run the helper. It compares digest sets, media type/size, artifact type, annotations, fallback behavior, and platform-subject coverage. An extra destination descriptor is `review`, not automatic corruption: establish whether another authorized writer added it. Missing or changed source descriptors fail.

Run comparisons independently for direct registry access, through each proxy/cache, after copy, after replication, and through the verifier's actual client. The first divergent pair localizes the lossy boundary.

**Completion:** one report identifies the earliest divergence and contains no production payloads or credentials.

### 6. Probe writes only in disposable staging

Only with explicit authorization, create a unique staging repository, push a tiny synthetic subject, attach one synthetic artifact, and verify both discovery paths relevant to the endpoint. Exercise concurrent writers only with bounded synthetic descriptors and cleanup approval. Never overwrite a real fallback tag, re-sign production images, or use deletion as a probe.

**Completion:** staging proves the failure boundary and the chosen recovery transition without touching production content.

### 7. Select the narrowest recovery and canary

Prefer, in order: upgrade/fix the lossy component; enable its documented OCI 1.1 mode; configure copy/replication to include referrers; or use a reviewed client fallback compatible with the endpoint. Preserve the original source graph and rerun the full digest/per-platform comparison. Do not “repair” the destination by manually inventing descriptors.

Canary one immutable image graph. Require all expected descriptor digests and metadata at direct and proxied destinations, then verify signatures/attestations with the intended consumer. Keep the old distribution path until parity holds.

**Completion:** the canary passes descriptor, platform coverage, and consumer verification; rollback restores the prior copy path without deleting source artifacts.

## Objective Verification

Pass only when:

- source and destination use the same immutable subject and repository scope;
- supported API responses are 200 with OCI image-index media type, while exactly 404 follows the reviewed fallback path;
- all pages and all index/platform subject nodes were inventoried;
- descriptor digest, media type, size, artifact type, annotations, and subject relationship are preserved;
- duplicates and missing referrers are absent;
- the actual proxy/replication/copy path and final consumer agree with direct registry observations;
- staging proves both the observed failure and corrected transition before production promotion;
- no registry mutation occurs from the offline report.

## Unsafe Operations and Recovery

- Never print or store bearer tokens, Docker config contents, cookies, signed URLs, private keys, signature payloads, attestations, or full SBOMs in fixtures.
- Never interpret authorization failure or malformed output as absent API support.
- Never enable destructive registry deletion, garbage collection, or fallback-tag overwrite to test discovery.
- If an unauthorized write occurred, stop the probe, preserve audit metadata, notify the registry owner, revoke exposed credentials, and restore only from the authoritative source graph.
- If replication dropped referrers, freeze promotion, retain the source digest and artifacts, repair the transport, and recopy into a fresh staging destination before production.
- If concurrent fallback writers lost entries, stop writers, inventory each authoritative manifest by digest, and rebuild only through an owner-approved conditional update process.

## Pitfalls

- A UI showing one signature does not prove API correctness, fallback parity, or platform coverage.
- Copying an image index alone does not necessarily copy referrers of its platform manifests.
- A 404 has defined fallback semantics; other failures do not.
- Deduplicating by artifact type hides multiple legitimate signatures. Descriptor digest is the identity key.
- Fallback tags are client-maintained and can suffer lost updates.
- Filtering without checking `OCI-Filters-Applied` can yield misleading assumptions.

## Evaluation Prompts

See [`references/evaluations.md`](references/evaluations.md) for normal, difficult-edge, and should-not-activate prompts with machine-checkable assertions.

## Sources and Provenance

Sourced facts about 200/404 behavior, response media type, descriptor metadata, fallback tags, duplicate avoidance, conditional writes, and migration inclusion come from OCI Distribution Specification v1.1.1 (`spec.md` blob `26e64b967d9a1e38e508f3f450500b5c0cf21a30`), accessed 2026-07-31. Issue reports are factual demand evidence. The observation schema, comparator, topology ordering, failure localization, staging gate, and recovery hierarchy are original recommendations.

- [OCI Distribution Specification v1.1.1 release](https://github.com/opencontainers/distribution-spec/releases/tag/v1.1.1)
- [OCI Distribution Specification v1.1.1](https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md)
- [Cosign #4641: invalid fallback-tag metadata](https://github.com/sigstore/cosign/issues/4641)
- [Cosign #4335: incomplete OCI 1.1 command coverage](https://github.com/sigstore/cosign/issues/4335)
- [Harbor #23210: OCI 1.1 referrers omitted by replication](https://github.com/goharbor/harbor/issues/23210)
- [Harbor #20808: proxy cache omits referrers API](https://github.com/goharbor/harbor/issues/20808)
- [ORAS #1741: platform-manifest referrers are not shown](https://github.com/oras-project/oras/issues/1741)
- [zot #2506: duplicate referrers](https://github.com/project-zot/zot/issues/2506)
