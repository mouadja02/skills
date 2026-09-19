# Evaluation Prompts

## Normal activation

Analyze a synthetic OCI image index whose `linux/arm64/v8` descriptor points to a child image configuration declaring `linux/amd64`. Produce a machine-checkable offline report.

Assertions: exit `1`; status `fail`; finding `PLATFORM_CONFIG_MISMATCH`; no network or registry mutation.

## Difficult edge

Analyze a before/after graph with two `linux/amd64` descriptors and one `linux/arm64/v8` descriptor. The after graph retains only the first amd64 descriptor. Use the supplied exact matcher.

Assertions: select the first matching digest; report `AMBIGUOUS_PLATFORM_MATCH` and `GRAPH_DESCRIPTOR_REMOVED`; preserve matcher policy separately from OCI conformance.

## Should not activate

Inspect a single OCI image manifest with no image index or transport comparison.

Assertions: status `not_applicable`; no findings; exit `0`; recommend a different workflow if image content itself needs validation.
