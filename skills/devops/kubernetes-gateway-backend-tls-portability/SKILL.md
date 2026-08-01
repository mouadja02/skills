---
name: kubernetes-gateway-backend-tls-portability
description: "Use when Gateway API BackendTLSPolicy is accepted but upstream TLS fails or differs across controllers, upgrades, SAN validation, CA sources, chain depth, or implementation-native policy precedence."
version: "1.0.0"
license: MIT
---

# Kubernetes Gateway Backend TLS Portability

Diagnose Gateway-to-backend TLS as an attachment, status, and observed-behavior problem—not merely a valid manifest. Start read-only, pin the Gateway API and controller versions, and mutate only a disposable namespace after explicit approval. The bundled helper analyzes redacted observations offline and never contacts or changes a cluster.

## When to Use

- `BackendTLSPolicy` is Accepted but requests fail, use plaintext, or trust the wrong certificate.
- A controller upgrade changes CA, hostname, SAN, certificate-chain, or rotation behavior.
- Teams compare Envoy Gateway, Istio, NGINX Gateway Fabric, Traefik, Cilium, or another implementation.
- Gateway API policy and an implementation-native backend TLS policy may both apply.

## When Not to Use

- Frontend listener certificate issuance, expiry, or TLS termination is the only problem.
- The backend is intentionally plaintext and no `BackendTLSPolicy` should attach.
- Generic NetworkPolicy, DNS, or application failures have already been isolated from TLS.
- The request is to disable certificate verification in production. This workflow never uses insecure skip-verify as a remedy.

## Prerequisites

- Exact Kubernetes, Gateway API CRD, controller, data-plane, and policy API versions.
- Read access to GatewayClass/Gateway/Route/Service/BackendTLSPolicy status and controller logs.
- A redacted request path and, for behavioral probes, an owner-approved disposable namespace with generated local certificates.
- Python 3.10+ for the optional offline checker.

## Quick Reference

1. Freeze versions and map client → Gateway → Route → Service → endpoint.
2. Inventory installed CRD storage/served versions and the controller's advertised conformance features.
3. Prove same-namespace target attachment, section selection, precedence, `Accepted`, and `ResolvedRefs`.
4. Compare observed valid, untrusted-CA, mismatched-host, SAN, chain-depth, and CA-rotation cases.
5. Analyze a redacted observation:

```bash
python3 scripts/check_backend_tls.py --input observations/backend-tls.json --output report.json
```

Exit `0` means `pass` or `not_applicable`; `1` means behavioral failure; `2` means malformed/unreadable input, unknown profile, or report-write failure. Every report sets `mutation_permitted: false`.

## Observation Contract

Use `profile: gateway-api-v1.6.1` and `kind: gateway_backend_tls_audit`. Record:

- inventory: controller/version, installed Gateway API version, and observed supported feature names;
- policy: namespace, target namespace/kind/name/existence, target-ref distinctness, CA source, hostname, SAN types, competing-policy presence, and status conditions;
- probes: `success`, `http_5xx`, or `not_run` for traffic cases; `reconciled` or `not_run` for CA rotation.

Use synthetic names in shared fixtures. Never include kubeconfigs, bearer tokens, Secrets, private keys, certificates from production, complete controller logs, private DNS names, cookies, or request payloads. The helper deliberately rejects unknown fields and non-standard JSON numbers.

## Procedure

### 1. Freeze topology and API versions

Record the externally observed request path and every reconciliation hop: GatewayClass/controller → Gateway/listener → Route/backendRef → Service port/section → EndpointSlice → backend TLS listener. Capture Kubernetes and controller versions plus the exact installed CRD's served/storage versions; do not infer capability from documentation for a newer release.

Record whether the controller's conformance report advertises `BackendTLSPolicy` and, when SANs are used, `BackendTLSPolicySANValidation`. These are the serialized v1.6.1 feature names; advertisement is evidence of claimed coverage, not proof of the live path.

**Completion:** one timestamped version/topology packet identifies the policy implementation and data plane.

### 2. Prove policy attachment before testing certificates

For each `targetRef`, verify:

- the target is an existing Service in the policy's namespace;
- group/kind/name and optional `sectionName` resolve to the intended Service port;
- repeated targets use distinct sections and references are distinct;
- no older policy, duplicate target, Helm-rendered policy, DestinationRule, BackendTrafficPolicy, or controller-native object competes for the same backend;
- observed policy ancestors/conditions refer to the Gateway that carries the test traffic.

Gateway API v1.6.1 target refs are same-namespace. Conflicting refs must not be treated as deterministic merely because one object is Accepted.

**Completion:** exactly one intended policy path is selected, or precedence is explicitly classified unresolved.

### 3. Interpret status without equating it to traffic success

Require current observed-generation status. Check `Accepted` and `ResolvedRefs` independently, preserving reason/message/controller identity. Invalid CA references can produce `InvalidCACertificateRef`, `InvalidKind`, or `NoValidCACertificate`; all-invalid CA refs must not be converted into a permissive trust mode.

An Accepted policy proves reconciliation intent, not certificate validation on every endpoint. Continue to bounded behavioral probes.

**Completion:** attachment/status failures are separated from handshake/data-plane failures.

### 4. Build a bounded certificate matrix

Only in a disposable namespace after explicit approval, generate a small local CA, leaf certificates, and an HTTPS echo backend. Keep private keys inside the disposable namespace. Run fresh connections for:

| Case | Expected observation |
| --- | --- |
| trusted CA + matching hostname | success |
| untrusted CA | Gateway returns HTTP 5xx; backend request is not accepted |
| trusted CA + mismatched hostname | HTTP 5xx |
| matching DNS/URI SAN when configured | success |
| mismatching configured DNS/URI SAN | HTTP 5xx |
| valid intermediate chain within documented limits | success |
| rotated ConfigMap CA | controller reconciles, then new valid path succeeds |

`hostname` supplies SNI and normally the authentication name. In v1.6.1, configured `subjectAltNames` replace hostname for authentication; include the hostname explicitly in SANs if it must remain accepted. Test system roots only when the implementation advertises/documents them because `wellKnownCACertificates: System` is implementation-specific.

Bound requests, retries, certificate sizes, chain length, and total runtime. Confirm a 5xx came from upstream TLS rejection, not application failure.

**Completion:** positive and negative observations prove fail-closed behavior on the exact data plane.

### 5. Isolate controller-specific precedence and chain behavior

If native and Gateway API policies coexist, repeat the matrix with: Gateway policy only, native policy only, both, then neither in the disposable namespace. Do not infer precedence from YAML apply order. Record generated data-plane configuration only after redacting addresses and secrets.

For chain failures, verify the backend serves the intended intermediates before changing controller depth limits. A valid chain that fails under one controller/version is portability evidence; it is not justification to disable verification globally.

**Completion:** the first policy combination or chain boundary that changes behavior is identified.

### 6. Compare and classify offline

Normalize each controller/version into the observation contract and run the helper. A `pass` requires claimed base support, valid-path success, negative-path 5xx behavior, valid attachment/status, and ConfigMap rotation when used. SAN requests also require advertised SAN support and matching/mismatching URI outcomes where applicable.

A missing probe is not a pass. Keep separate reports for each version and controller; do not merge away disagreement.

**Completion:** reports contain deterministic finding codes and no cluster credentials or production certificate material.

### 7. Recover and canary narrowly

Prefer: fix attachment/reference errors; remove or explicitly order a competing native policy; correct CA bundle/hostname/SANs; upgrade or roll back the affected controller; then use only documented, narrowly scoped controller options for valid chain depth. Never replace validation with plaintext or skip-verify.

Canary one synthetic backend, then one non-critical owned backend. Require unchanged positive/negative matrix results, current conditions, no plaintext fallback, and rollback to the prior controller/policy version. Delete disposable resources only with owner approval after evidence is retained.

**Completion:** the corrected version passes the same matrix and rollback has been rehearsed.

## Objective Verification

Pass only when:

- installed CRD and controller versions plus supported features are recorded;
- one same-namespace Service/section attachment is unambiguous;
- `Accepted` and `ResolvedRefs` are current and true;
- valid CA/name/SAN paths succeed while untrusted CA and mismatches fail with 5xx;
- ConfigMap CA rotation reconciles when that source is used;
- valid chain depth and native-policy precedence are resolved for the chosen controller;
- the canary repeats the same observations without weakening verification;
- offline artifacts contain no credentials or private certificate material.

## Unsafe Operations and Recovery

- Never patch production policy, CRDs, GatewayClass, controller flags, trust stores, or native policy objects during diagnosis.
- Never print Secrets, kubeconfig, service-account tokens, private keys, or raw production certificates.
- Never use `insecureSkipVerify`, plaintext fallback, broad wildcard trust, or a global chain-depth increase as an automatic fix.
- If a probe touches production, stop, preserve only redacted metadata, notify the owner, and rotate any exposed credentials or private keys.
- If a change causes plaintext or unintended trust, freeze rollout and restore the last known controller/policy version before further testing.
- If cleanup fails, label and quarantine the disposable namespace; do not force-delete finalizers without owner review.

## Pitfalls

- Accepted status is not end-to-end evidence.
- Controller release notes do not prove the installed data plane loaded a policy.
- `System` trust is implementation-specific and may vary with the controller image.
- SAN semantics can supersede hostname authentication while hostname still supplies SNI.
- A backend can omit an intermediate and mimic a controller chain-depth defect.
- Native policy precedence can make a correct Gateway API manifest observationally irrelevant.
- Reusing connections can hide certificate rotation; use bounded fresh-connection checks.

## Evaluation Prompts

See [`references/evaluations.md`](references/evaluations.md) for normal, difficult-edge, and should-not-activate prompts with machine-checkable assertions.

## Sources and Provenance

**Sourced facts:** Gateway API v1.6.1 types define same-namespace target references, conflict handling, CA reference conditions, hostname/SNI/authentication behavior, SAN support, and implementation-specific system roots. Its conformance tests cover valid and invalid CA/hostname, CA rotation, DNS/URI SAN match and mismatch. The cited issues demonstrate cross-controller upgrade, attachment, precedence, chain, system-root, and SAN-support failures.

**Original recommendations:** the topology packet, redacted observation schema, offline checker, cross-controller matrix, precedence isolation order, recovery hierarchy, and safety gates are original operational synthesis. No third-party prose or code is bundled.

- [Gateway API v1.6.1 release](https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.6.1)
- [BackendTLSPolicy v1.6.1 types, blob a9d8532](https://github.com/kubernetes-sigs/gateway-api/blob/v1.6.1/apis/v1/backendtlspolicy_types.go)
- [BackendTLSPolicy SAN conformance test, blob a2954aa](https://github.com/kubernetes-sigs/gateway-api/blob/v1.6.1/conformance/tests/backendtlspolicy-san.go)
- [Gateway API #3979: core support lacked tests](https://github.com/kubernetes-sigs/gateway-api/issues/3979)
- [Envoy Gateway #7709: upgrade regression](https://github.com/envoyproxy/gateway/issues/7709)
- [Traefik #12127: Service attachment failure](https://github.com/traefik/traefik/issues/12127)
- [Istio #60122: competing policy behavior](https://github.com/istio/istio/issues/60122)
- [NGINX Gateway Fabric #5115: certificate-chain depth](https://github.com/nginx/nginx-gateway-fabric/issues/5115)
- [NGINX Gateway Fabric #5231: system CA intermittent failure](https://github.com/nginx/nginx-gateway-fabric/issues/5231)
- [Cilium #47194: SAN validation support](https://github.com/cilium/cilium/issues/47194)
