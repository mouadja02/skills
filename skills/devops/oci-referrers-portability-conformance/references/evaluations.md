# Evaluation Prompts

Run all prompts with synthetic, credential-free snapshots. The same input must be used for baseline and with-skill behavior.

## Normal

> Compare a source and destination OCI 1.1 referrers inventory for one image digest. Both API responses contain the same SBOM descriptor, artifact type, annotations, media type, and size. Prove whether promotion preserved the graph.

Assertions: the helper exits `0`; status is `pass`; source and destination counts are one; no findings exist; mutation remains prohibited.

## Difficult edge

> An older source and destination both return 404 from the referrers API and use the fallback tag. The destination duplicates the signature descriptor, changes its artifact type, drops annotations, and omits a platform-manifest subject covered at source. Diagnose every boundary without writing to either registry.

Assertions: the helper exits `1`; mode is `fallback_tag` on both sides; findings include `DUPLICATE_DESCRIPTOR`, `ARTIFACT_TYPE_DRIFT`, `ANNOTATION_DRIFT`, and `DESTINATION_PLATFORM_COVERAGE_MISSING`; mutation remains prohibited.

## Should not activate

> Review a generic SBOM package inventory that has no OCI subject/referrer graph or registry transport observations.

Assertions: the helper exits `0`; status is `not_applicable`; no OCI conformance finding is invented.
