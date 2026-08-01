# Evaluation Prompts

Use the same redacted observation inputs for baseline and skill-assisted runs. A response passes only when the helper output and the agent's recommendation satisfy the assertions.

## Normal

**Prompt:** “Before upgrading our Gateway controller, assess `normal.json`. Is BackendTLSPolicy behavior portable enough for a canary?”

Assertions: classify `pass`; preserve `mutation_permitted: false`; identify an existing same-namespace Service, true Accepted/ResolvedRefs, valid success, mismatched-host/untrusted-CA 5xx, and ConfigMap rotation reconciliation.

## Difficult edge

**Prompt:** “The policy is Accepted, but URI SAN, system roots, a deep chain, and a native policy interact in `edge.json`. Can we promote?”

Assertions: classify `fail`; report SAN feature not advertised, untrusted CA accepted, hostname mismatch accepted, URI SAN match/mismatch failures, chain-depth failure, and unresolved policy precedence; do not recommend weakening verification.

## Should not activate

**Prompt:** “Inventory frontend listener certificate expiry from `not-applicable.json`; no upstream TLS policy exists.”

Assertions: classify `not_applicable`; do not invent BackendTLSPolicy findings or suggest cluster mutation.
