# Evaluation Prompts

## Normal

> WebAuthn registration fails at `https://login.example.test:8443`; configured public URL omits the port, and RP ID is `login.example.test`. Diagnose and create a safe preflight.

Expected: preserve the port in the origin, never put it in RP ID, compare both ceremonies, and produce a synthetic machine-readable gate.

## Difficult edge

> A service moved from `old.example.test` to `auth.example.test` behind two proxies. Old credentials use the old RP ID, all forwarded headers are trusted, and Android supplies an APK facet origin. Plan safe migration and testing.

Expected: require re-enrollment or a measured related-origin path rather than database rewriting; fail closed on proxy ambiguity; keep native origins exact; use synthetic fixtures.

## Should not activate

> An OAuth callback reports state mismatch and the system does not use WebAuthn or passkeys. Should this workflow activate?

Expected: no; investigate OAuth state/session/cookie/redirect continuity.
