# Evaluation prompts

Run these with synthetic metadata only. The expected result is defined by observable assertions, not keyword presence in the skill.

## Normal

**Prompt:** An authorization-server token request has synthetic proof metadata `jti=j1, iat=100, nonce=null`. The response is HTTP 400, JSON error `use_dpop_nonce`, and one `DPoP-Nonce: as-n1`. A same-endpoint retry has `jti=j2, iat=101, nonce=as-n1` and receives 200. Diagnose and validate with the helper.

**Assertions:** classification `ready`; exactly one bounded retry; challenged nonce used; fresh `jti`; non-regressing `iat`; no credential material.

## Difficult edge

**Prompt:** Resource request 10 receives `rs-n2` on 200, then delayed request 9 receives `rs-n1` for the same scope. An authorization-server response receives `as-n7`. A browser-visible resource challenge has two DPoP-Nonce field values. Diagnose state after each event.

**Assertions:** stale `rs-n1` cannot clobber `rs-n2`; AS and RS state are separate; duplicate values block retry; browser context also requires CORS exposure; no second automatic retry.

## Should not activate

**Prompt:** A public OAuth client uses Authorization Code with PKCE. There is no DPoP proof, bound token, nonce header, or `use_dpop_nonce` signal. The task is redirect-URI verification.

**Assertions:** classify `not_applicable`; do not expand into generic OAuth advice.
