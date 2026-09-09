#!/usr/bin/env python3
"""Offline structural + fail-closed validator for the JOSE "crit" header.

Deterministic and standard-library-only. Validates the "crit" (Critical)
Header Parameter of a JWS/JWT protected header against RFC 7515 section 4.1.11
and RFC 7797 section 6. It does NOT verify signatures or decode claims.

Exit codes:
  0 -> classification is "ready" or "not_applicable"
  1 -> classification is "blocked" (a protocol violation was evidenced)
  2 -> input handling failed (proves no protocol result)
"""
from __future__ import annotations

import base64
import json
import sys

# Header Parameter names defined by RFC 7515 (JWS) and RFC 7516 (JWE).
# RFC 7515 s4.1.11: producers MUST NOT list names defined by the JWS spec or
# JWA in "crit". "b64" is intentionally absent: it is an RFC 7797 extension,
# not a base JOSE header name, so it is legitimately listable in "crit".
STANDARD_JOSE_HEADER_NAMES = {
    "alg", "jku", "jwk", "kid", "x5u", "x5c", "x5t", "x5t#S256",
    "typ", "cty", "crit",
    "enc", "zip", "epk", "apu", "apv", "iv", "tag", "p2s", "p2c",
}


def _b64url_decode(segment: str) -> bytes:
    pad = "=" * (-len(segment) % 4)
    return base64.urlsafe_b64decode(segment + pad)


def decode_compact_header(token: str) -> dict:
    """Return the decoded protected header of a compact JWS string."""
    parts = token.strip().split(".")
    if not parts or parts[0] == "":
        raise ValueError("compact JWS must contain a header segment")
    header = json.loads(_b64url_decode(parts[0]).decode("utf-8"))
    if not isinstance(header, dict):
        raise ValueError("JWS protected header must decode to a JSON object")
    return header


def validate(header: dict, supported_extensions=None) -> dict:
    """Validate a decoded JOSE protected header.

    supported_extensions: optional list of header-parameter names the recipient
    understands. None or [] means no extensions are understood (fail closed).
    """
    findings = []
    violations = []
    supported = set(supported_extensions) if supported_extensions else set()

    if "crit" not in header:
        return {
            "classification": "not_applicable",
            "crit_entries": None,
            "findings": findings,
            "violations": violations,
        }

    crit = header.get("crit")
    if not isinstance(crit, list):
        violations.append({
            "id": "crit_not_array",
            "detail": "crit is not a JSON array",
        })
        return {
            "classification": "blocked",
            "crit_entries": None,
            "findings": findings,
            "violations": violations,
        }

    crit_entries = list(crit)
    if len(crit_entries) == 0:
        findings.append({
            "id": "crit_empty",
            "detail": "crit present but empty; no extensions declared",
        })

    seen = set()
    for name in crit_entries:
        if not isinstance(name, str):
            violations.append({
                "id": "crit_non_string_entry",
                "detail": "crit entry %r is not a string" % (name,),
            })
            continue
        if name in seen:
            violations.append({
                "id": "crit_duplicate",
                "detail": "duplicate crit entry %r" % (name,),
            })
        seen.add(name)
        if name in STANDARD_JOSE_HEADER_NAMES:
            violations.append({
                "id": "crit_standard_name",
                "detail": "crit names standard JOSE header %r" % (name,),
            })
        if name not in header:
            violations.append({
                "id": "crit_dangling",
                "detail": "crit names %r which is absent from the header" % (name,),
            })
        if name not in STANDARD_JOSE_HEADER_NAMES and name not in supported:
            violations.append({
                "id": "crit_unsupported",
                "detail": "unknown critical extension %r not understood" % (name,),
            })

    # RFC 7797 s6: b64=false requires "b64" in crit so non-conforming peers reject.
    if "b64" in header:
        if header["b64"] is False:
            if "b64" not in crit_entries:
                violations.append({
                    "id": "b64_false_missing_crit",
                    "detail": "b64=false but crit does not list 'b64'",
                })
            findings.append({
                "id": "jwt_b64_false",
                "detail": "RFC 7797 s7: JWTs MUST NOT use b64=false",
            })

    classification = "blocked" if violations else "ready"
    return {
        "classification": classification,
        "crit_entries": crit_entries,
        "findings": findings,
        "violations": violations,
    }


def main(argv):
    if len(argv) != 2:
        sys.stderr.write(
            json.dumps({"ok": False, "error": "usage: validate_jose_crit.py <input.json>"})
            + "\n"
        )
        return 2
    try:
        with open(argv[1], "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception as exc:
        sys.stderr.write(
            json.dumps({"ok": False, "error": "input read/parse: %s: %s" % (type(exc).__name__, exc)})
            + "\n"
        )
        return 2
    try:
        if "header" in data:
            header = data["header"]
        elif "token" in data:
            header = decode_compact_header(data["token"])
        else:
            raise ValueError("input must contain 'header' or 'token'")
        if not isinstance(header, dict):
            raise ValueError("header must be a JSON object")
        supported = data.get("supported_extensions")
        if supported is not None and not isinstance(supported, list):
            raise ValueError("supported_extensions must be a list of strings")
        result = validate(header, supported)
    except Exception as exc:
        sys.stderr.write(
            json.dumps({"ok": False, "error": "validation setup: %s: %s" % (type(exc).__name__, exc)})
            + "\n"
        )
        return 2

    out = {"ok": True, **result}
    sys.stdout.write(json.dumps(out, separators=(",", ":")) + "\n")
    sys.stdout.flush()
    return 1 if result["classification"] == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
