#!/usr/bin/env python3
"""Offline, metadata-only DPoP nonce transcript validator."""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

PROFILE = "oauth-dpop-nonce-v1"
FORBIDDEN_KEYS = {
    "access_token", "authorization", "client_secret", "cookie", "dpop_proof",
    "id_token", "private_key", "refresh_token", "token", "jwt",
}
ALLOWED_TOP = {"profile", "events"}
ALLOWED_EVENT = {
    "role", "origin", "endpoint", "request_id", "operation_id", "retry_index",
    "retry_of", "proof_present", "request_nonce", "jti", "iat", "status",
    "oauth_error", "www_authenticate_error", "dpop_nonce_headers",
    "browser_context", "cors_exposed_headers",
}


class InputError(ValueError):
    pass


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise InputError(f"duplicate JSON member: {key}")
        out[key] = value
    return out


def load_input(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise InputError(f"cannot read UTF-8 input: {exc}") from exc
    try:
        return json.loads(
            text,
            object_pairs_hook=_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                InputError(f"non-standard JSON constant: {value}")
            ),
        )
    except InputError:
        raise
    except json.JSONDecodeError as exc:
        raise InputError(f"malformed JSON: {exc.msg}") from exc


def _scan(value, path="$", depth=0):
    if depth > 20:
        raise InputError("input nesting exceeds 20 levels")
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise InputError(f"{path}: object key is not a string")
            if key.lower() in FORBIDDEN_KEYS:
                raise InputError(f"{path}: forbidden credential-bearing key: {key}")
            _scan(item, f"{path}.{key}", depth + 1)
    elif isinstance(value, list):
        if len(value) > 1000:
            raise InputError(f"{path}: array exceeds 1000 entries")
        for index, item in enumerate(value):
            _scan(item, f"{path}[{index}]", depth + 1)
    elif isinstance(value, float) and not math.isfinite(value):
        raise InputError(f"{path}: non-finite number")
    elif isinstance(value, str) and len(value) > 4096:
        raise InputError(f"{path}: string exceeds 4096 characters")


def _exact_keys(obj, allowed, path):
    unknown = set(obj) - allowed
    if unknown:
        raise InputError(f"{path}: unsupported members: {', '.join(sorted(unknown))}")


def _text(value, path, *, optional=False, limit=256):
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value or len(value) > limit:
        raise InputError(f"{path}: expected non-empty string up to {limit} characters")
    if any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value):
        raise InputError(f"{path}: control character is forbidden")
    return value


def _integer(value, path, minimum=0):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise InputError(f"{path}: expected integer >= {minimum}")
    return value


def _origin(value, path):
    value = cast(str, _text(value, path))
    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
        raise InputError(f"{path}: expected credential-free https origin")
    if parts.path or parts.query or parts.fragment:
        raise InputError(f"{path}: origin must not contain path, query, or fragment")
    return value.lower()


def _headers(value, path):
    if not isinstance(value, list) or len(value) > 4:
        raise InputError(f"{path}: expected an array with at most four values")
    result = []
    for index, item in enumerate(value):
        item = cast(str, _text(item, f"{path}[{index}]"))
        if any(ord(ch) > 0x7E for ch in item) or "," in item or " " in item:
            raise InputError(f"{path}[{index}]: ambiguous or non-ASCII nonce value")
        result.append(item)
    return result


def normalize_event(raw, index):
    path = f"$.events[{index}]"
    if not isinstance(raw, dict):
        raise InputError(f"{path}: expected object")
    _exact_keys(raw, ALLOWED_EVENT, path)
    required = {
        "role", "origin", "endpoint", "request_id", "operation_id", "retry_index",
        "proof_present", "status", "dpop_nonce_headers",
    }
    missing = required - set(raw)
    if missing:
        raise InputError(f"{path}: missing members: {', '.join(sorted(missing))}")
    role = raw["role"]
    if role not in {"authorization_server", "resource_server"}:
        raise InputError(f"{path}.role: unsupported role")
    endpoint = cast(str, _text(raw["endpoint"], f"{path}.endpoint"))
    if not endpoint.startswith("/") or "?" in endpoint or "#" in endpoint:
        raise InputError(f"{path}.endpoint: expected path beginning with / without query/fragment")
    retry_index = _integer(raw["retry_index"], f"{path}.retry_index")
    if retry_index not in {0, 1}:
        raise InputError(f"{path}.retry_index: only 0 or 1 is allowed")
    proof_present = raw["proof_present"]
    if not isinstance(proof_present, bool):
        raise InputError(f"{path}.proof_present: expected boolean")
    request_nonce = _text(raw.get("request_nonce"), f"{path}.request_nonce", optional=True)
    jti = _text(raw.get("jti"), f"{path}.jti", optional=True)
    iat = raw.get("iat")
    if proof_present:
        if jti is None or iat is None:
            raise InputError(f"{path}: proof metadata requires jti and iat")
        iat = _integer(iat, f"{path}.iat")
    elif any(value is not None for value in (request_nonce, jti, iat)):
        raise InputError(f"{path}: proof metadata present while proof_present is false")
    retry_of = raw.get("retry_of")
    if retry_index == 1:
        retry_of = _integer(retry_of, f"{path}.retry_of")
    elif retry_of is not None:
        raise InputError(f"{path}.retry_of: only valid when retry_index is 1")
    exposed = raw.get("cors_exposed_headers", [])
    if not isinstance(exposed, list) or any(not isinstance(x, str) for x in exposed):
        raise InputError(f"{path}.cors_exposed_headers: expected string array")
    browser = raw.get("browser_context", False)
    if not isinstance(browser, bool):
        raise InputError(f"{path}.browser_context: expected boolean")
    event = {
        "role": role,
        "origin": _origin(raw["origin"], f"{path}.origin"),
        "endpoint": endpoint,
        "request_id": _integer(raw["request_id"], f"{path}.request_id"),
        "operation_id": _text(raw["operation_id"], f"{path}.operation_id"),
        "retry_index": retry_index,
        "retry_of": retry_of,
        "proof_present": proof_present,
        "request_nonce": request_nonce,
        "jti": jti,
        "iat": iat,
        "status": _integer(raw["status"], f"{path}.status", 100),
        "oauth_error": _text(raw.get("oauth_error"), f"{path}.oauth_error", optional=True),
        "www_authenticate_error": _text(raw.get("www_authenticate_error"), f"{path}.www_authenticate_error", optional=True),
        "dpop_nonce_headers": _headers(raw["dpop_nonce_headers"], f"{path}.dpop_nonce_headers"),
        "browser_context": browser,
        "cors_exposed_headers": [x.lower() for x in exposed],
    }
    if event["status"] > 599:
        raise InputError(f"{path}.status: expected HTTP status 100..599")
    return event


def analyze(document):
    if not isinstance(document, dict):
        raise InputError("$: expected object")
    _scan(document)
    _exact_keys(document, ALLOWED_TOP, "$")
    if document.get("profile") != PROFILE:
        raise InputError(f"$.profile: expected {PROFILE}")
    raw_events = document.get("events")
    if not isinstance(raw_events, list) or not raw_events or len(raw_events) > 200:
        raise InputError("$.events: expected 1..200 events")
    events = [normalize_event(raw, i) for i, raw in enumerate(raw_events)]
    findings = []
    active = {}
    pending = {}
    seen_ids = set()
    applicable = False

    def finding(code, severity, index, detail):
        findings.append({"code": code, "severity": severity, "event": index, "detail": detail})

    for index, event in enumerate(events):
        rid = event["request_id"]
        if rid in seen_ids:
            raise InputError(f"$.events[{index}].request_id: duplicate request id")
        seen_ids.add(rid)
        scope = f'{event["role"]}|{event["origin"]}|{event["endpoint"]}'
        nonce_values = event["dpop_nonce_headers"]
        challenge = (
            event["oauth_error"] == "use_dpop_nonce"
            or event["www_authenticate_error"] == "use_dpop_nonce"
        )
        applicable = applicable or event["proof_present"] or bool(nonce_values) or challenge

        if event["browser_context"] and nonce_values and "dpop-nonce" not in event["cors_exposed_headers"]:
            finding("nonce_not_cors_exposed", "error", index, "browser code cannot read DPoP-Nonce")
        if len(nonce_values) > 1:
            finding("ambiguous_nonce_header", "error", index, "exactly one DPoP-Nonce value is required")

        if event["retry_index"] == 1:
            prior = pending.pop(event["operation_id"], None)
            if prior is None or event["retry_of"] != prior["request_id"]:
                finding("unexpected_retry", "error", index, "retry has no matching unresolved challenge")
            else:
                if scope != prior["scope"]:
                    finding("retry_scope_changed", "error", index, "retry changed role, origin, or endpoint")
                if event["request_nonce"] != prior["nonce"]:
                    finding("retry_nonce_mismatch", "error", index, "retry proof did not use challenged nonce")
                if not event["proof_present"]:
                    finding("retry_proof_missing", "error", index, "retry requires a newly generated proof")
                elif event["jti"] == prior["jti"]:
                    finding("retry_jti_reused", "error", index, "retry proof reused jti")
                elif event["iat"] < prior["iat"]:
                    finding("retry_iat_regressed", "error", index, "retry proof iat regressed")
                else:
                    finding("bounded_retry_verified", "info", index, "one retry used the challenged nonce with fresh proof identity")

        if challenge:
            expected = (event["role"] == "authorization_server" and event["status"] == 400 and event["oauth_error"] == "use_dpop_nonce") or (
                event["role"] == "resource_server" and event["status"] == 401 and event["www_authenticate_error"] == "use_dpop_nonce"
            )
            if not expected:
                finding("challenge_status_error_mismatch", "error", index, "challenge status/error does not match endpoint role")
            if event["retry_index"] == 1:
                finding("repeated_nonce_challenge", "error", index, "a challenged retry must stop without another automatic retry")
            elif len(nonce_values) == 1:
                pending[event["operation_id"]] = {
                    "request_id": rid, "scope": scope, "nonce": nonce_values[0],
                    "jti": event["jti"], "iat": event["iat"] or 0,
                }
                finding("nonce_challenge", "info", index, "one bounded retry is eligible")
            else:
                finding("challenge_nonce_unusable", "error", index, "challenge did not provide one unambiguous nonce")

        if len(nonce_values) == 1:
            current = active.get(scope)
            if current is None or rid >= current["request_id"]:
                active[scope] = {"nonce": nonce_values[0], "request_id": rid}
                if not challenge:
                    finding("proactive_nonce_update", "info", index, "nonce learned from a non-challenge response")
            else:
                finding("stale_nonce_ignored", "info", index, "older concurrent response did not clobber newer nonce state")

    for operation_id, prior in sorted(pending.items()):
        finding("retry_missing", "error", len(events), f"operation {operation_id} has an unresolved nonce challenge")

    if not applicable:
        classification = "not_applicable"
    elif any(item["severity"] == "error" for item in findings):
        classification = "blocked"
    else:
        classification = "ready"
    return {
        "profile": PROFILE,
        "classification": classification,
        "max_automatic_retries": 1,
        "active_nonces": {key: value["nonce"] for key, value in sorted(active.items())},
        "findings": findings,
    }


def emit_report(report, stream=sys.stdout):
    try:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
    except (OSError, TypeError, ValueError) as exc:
        raise InputError(f"cannot serialize report: {exc}") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    args = parser.parse_args(argv)
    try:
        report = analyze(load_input(args.input))
        emit_report(report)
    except InputError as exc:
        print(json.dumps({"classification": "input_error", "error": str(exc)}), file=sys.stderr)
        return 2
    return 1 if report["classification"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
