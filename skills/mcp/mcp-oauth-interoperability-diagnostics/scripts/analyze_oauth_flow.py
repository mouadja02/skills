#!/usr/bin/env python3
"""Offline MCP OAuth evidence classifier. It never performs network requests."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any, TextIO
from urllib.parse import parse_qsl, urlsplit

PROFILE = "mcp-2025-11-25"
FORBIDDEN_KEYS = {
    "authorization", "proxy-authorization", "cookie", "set-cookie",
    "access_token", "refresh_token", "id_token", "client_secret",
    "code", "code_verifier", "pkce_verifier", "session_cookie",
}
SENSITIVE_QUERY_KEYS = {
    "code", "token", "access_token", "refresh_token", "id_token",
    "client_secret", "code_verifier",
}
BEARER_RE = re.compile(r"(?i)(?:^|\s)bearer\s+[A-Za-z0-9._~+/=-]{8,}")
ERROR_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
SCOPE_RE = re.compile(r"^[\x21\x23-\x5b\x5d-\x7e]{1,256}$")


class InputError(ValueError):
    pass


def reject_constant(value: str) -> None:
    raise InputError(f"non-standard JSON constant: {value}")


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(
                handle,
                parse_constant=reject_constant,
                object_pairs_hook=unique_object,
            )
    except InputError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"cannot read strict JSON input: {exc}") from exc


def require_object(value: Any, name: str, *, optional: bool = False) -> dict[str, Any] | None:
    if value is None and optional:
        return None
    if not isinstance(value, dict):
        raise InputError(f"{name} must be an object")
    return value


def require_string(value: Any, name: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value:
        raise InputError(f"{name} must be a non-empty string")
    return value


def string_list(value: Any, name: str, *, optional: bool = False) -> list[str] | None:
    if value is None and optional:
        return None
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise InputError(f"{name} must be an array of non-empty strings")
    if len(value) != len(set(value)):
        raise InputError(f"{name} must not contain duplicates")
    return value


def scope_list(value: Any, name: str) -> list[str]:
    values = string_list(value, name) or []
    if any(not SCOPE_RE.fullmatch(item) for item in values):
        raise InputError(f"{name} contains an invalid scope token")
    return values


def validate_error_name(value: Any, name: str) -> None:
    if value is not None and (not isinstance(value, str) or not ERROR_RE.fullmatch(value)):
        raise InputError(f"{name} must be a short OAuth error name, not error text")


def status_code(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 100 <= value <= 599:
        raise InputError(f"{name} must be an integer HTTP status from 100 to 599")
    return value


def validate_url(value: str, name: str, *, redirect: bool = False) -> None:
    parts = urlsplit(value)
    if not parts.scheme or not parts.netloc or parts.fragment or parts.username or parts.password:
        raise InputError(f"{name} must be an absolute URL without fragment or userinfo")
    if parts.scheme != "https":
        loopback = parts.hostname in {"127.0.0.1", "::1", "localhost"}
        if not (redirect and parts.scheme == "http" and loopback):
            raise InputError(f"{name} must use https (except loopback redirect URIs)")
    for key, _ in parse_qsl(parts.query, keep_blank_values=True):
        if key.lower() in SENSITIVE_QUERY_KEYS:
            raise InputError(f"{name} contains a sensitive query parameter")


def reject_secrets(value: Any, path: str = "$", seen: set[int] | None = None) -> None:
    if seen is None:
        seen = set()
    if isinstance(value, (dict, list)):
        marker = id(value)
        if marker in seen:
            raise InputError(f"cyclic value at {path}")
        seen.add(marker)
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                raise InputError(f"secret-bearing field is forbidden at {path}.{key}")
            reject_secrets(item, f"{path}.{key}", seen)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_secrets(item, f"{path}[{index}]", seen)
    elif isinstance(value, str):
        if BEARER_RE.search(value):
            raise InputError(f"bearer credential is forbidden at {path}")
        if value.startswith(("http://", "https://")):
            parts = urlsplit(value)
            if parts.username or parts.password:
                raise InputError(f"URL userinfo is forbidden at {path}")
            if any(key.lower() in SENSITIVE_QUERY_KEYS for key, _ in parse_qsl(parts.query, keep_blank_values=True)):
                raise InputError(f"sensitive URL query is forbidden at {path}")
    elif isinstance(value, float) and not math.isfinite(value):
        raise InputError(f"non-finite number at {path}")


def normalize(document: Any) -> dict[str, Any]:
    root = require_object(document, "root")
    assert root is not None
    reject_secrets(root)
    allowed = {
        "schema_version", "profile", "context", "target_resource", "challenge",
        "resource_metadata", "authorization_server_metadata", "authorization_request",
        "token_request", "token_response", "retry",
    }
    unknown = sorted(set(root) - allowed)
    if unknown:
        raise InputError(f"unknown root fields: {', '.join(unknown)}")
    if root.get("schema_version") != 1:
        raise InputError("schema_version must be 1")
    profile = require_string(root.get("profile"), "profile")
    if profile != PROFILE:
        raise InputError(f"unsupported profile: {profile}")
    context = require_string(root.get("context"), "context")
    if context not in {"initial", "mid_session"}:
        raise InputError("context must be initial or mid_session")

    target = require_string(root.get("target_resource"), "target_resource", optional=True)
    if target:
        validate_url(target, "target_resource")

    challenge = require_object(root.get("challenge"), "challenge", optional=True)
    if challenge is not None:
        allowed_challenge = {"status", "error", "resource_metadata", "scope"}
        if set(challenge) - allowed_challenge:
            raise InputError("challenge has unknown fields")
        challenge["status"] = status_code(challenge.get("status"), "challenge.status")
        validate_error_name(challenge.get("error"), "challenge.error")
        for key in ("resource_metadata", "scope"):
            require_string(challenge.get(key), f"challenge.{key}", optional=True)
        if challenge.get("scope"):
            scope_list(challenge["scope"].split(), "challenge.scope")
        if challenge.get("resource_metadata"):
            validate_url(challenge["resource_metadata"], "challenge.resource_metadata")

    prm = require_object(root.get("resource_metadata"), "resource_metadata", optional=True)
    if prm is not None:
        if set(prm) - {"url", "resource", "authorization_servers", "scopes_supported"}:
            raise InputError("resource_metadata has unknown fields")
        for key in ("url", "resource"):
            value = require_string(prm.get(key), f"resource_metadata.{key}")
            assert value is not None
            validate_url(value, f"resource_metadata.{key}")
        servers = string_list(prm.get("authorization_servers"), "resource_metadata.authorization_servers")
        scopes = scope_list(prm.get("scopes_supported", []), "resource_metadata.scopes_supported")
        for index, server in enumerate(servers or []):
            validate_url(server, f"resource_metadata.authorization_servers[{index}]")
        prm["authorization_servers"] = servers
        prm["scopes_supported"] = scopes

    asm = require_object(root.get("authorization_server_metadata"), "authorization_server_metadata", optional=True)
    if asm is not None:
        allowed_asm = {"issuer", "authorization_endpoint", "token_endpoint", "code_challenge_methods_supported"}
        if set(asm) - allowed_asm:
            raise InputError("authorization_server_metadata has unknown fields")
        for key in ("issuer", "authorization_endpoint", "token_endpoint"):
            value = require_string(asm.get(key), f"authorization_server_metadata.{key}")
            assert value is not None
            validate_url(value, f"authorization_server_metadata.{key}")
        asm["code_challenge_methods_supported"] = string_list(
            asm.get("code_challenge_methods_supported", []),
            "authorization_server_metadata.code_challenge_methods_supported",
        )

    for section_name in ("authorization_request", "token_request"):
        section = require_object(root.get(section_name), section_name, optional=True)
        if section is None:
            continue
        allowed_section = {"endpoint", "resource", "scope", "redirect_uri", "pkce_method", "pkce_verifier_present"}
        if set(section) - allowed_section:
            raise InputError(f"{section_name} has unknown fields")
        for key in ("endpoint", "resource", "redirect_uri"):
            value = require_string(section.get(key), f"{section_name}.{key}", optional=True)
            if value:
                validate_url(value, f"{section_name}.{key}", redirect=(key == "redirect_uri"))
        section["scope"] = scope_list(section.get("scope", []), f"{section_name}.scope")
        method = require_string(section.get("pkce_method"), f"{section_name}.pkce_method", optional=True)
        if method and method != "S256":
            raise InputError(f"{section_name}.pkce_method must be S256 when present")
        present = section.get("pkce_verifier_present")
        if present is not None and not isinstance(present, bool):
            raise InputError(f"{section_name}.pkce_verifier_present must be boolean")

    response = require_object(root.get("token_response"), "token_response", optional=True)
    if response is not None:
        if set(response) - {"status", "error", "granted_scope"}:
            raise InputError("token_response has unknown fields")
        response["status"] = status_code(response.get("status"), "token_response.status")
        validate_error_name(response.get("error"), "token_response.error")
        response["granted_scope"] = scope_list(response.get("granted_scope", []), "token_response.granted_scope")

    retry = require_object(root.get("retry"), "retry", optional=True)
    if retry is not None:
        if set(retry) - {"status", "error"}:
            raise InputError("retry has unknown fields")
        retry["status"] = status_code(retry.get("status"), "retry.status")
        validate_error_name(retry.get("error"), "retry.error")
    return root


def analyze(document: Any) -> dict[str, Any]:
    root = normalize(document)
    challenge = root.get("challenge")
    prm = root.get("resource_metadata")
    asm = root.get("authorization_server_metadata")
    auth = root.get("authorization_request")
    token = root.get("token_request")
    response = root.get("token_response")
    retry = root.get("retry")
    target = root.get("target_resource")

    oauth_evidence = any((challenge, prm, asm, auth, token, response))
    if not oauth_evidence:
        return {
            "schema_version": 1, "profile": PROFILE, "classification": "not_applicable",
            "valid": True, "findings": [],
            "next_action": "Route to transport, TLS, DNS, or application diagnostics; no OAuth evidence was supplied.",
        }
    if not target:
        raise InputError("target_resource is required when OAuth evidence is present")

    findings: list[dict[str, str]] = []

    def add(code: str, level: str, phase: str, detail: str) -> None:
        findings.append({"code": code, "level": level, "phase": phase, "detail": detail})

    if challenge:
        if challenge["status"] not in {401, 403}:
            add("unexpected_challenge_status", "error", "challenge", "OAuth challenge evidence must come from HTTP 401 or 403.")
        if not challenge.get("resource_metadata"):
            add("resource_metadata_hint_missing", "error", "challenge", "Challenge does not identify protected-resource metadata.")
        if challenge.get("error") == "insufficient_scope" and not challenge.get("scope"):
            add("scope_missing_on_insufficient_scope", "error", "challenge", "An insufficient_scope challenge does not state the required scope.")
        elif prm and prm.get("scopes_supported") and not challenge.get("scope"):
            add("scope_hint_missing", "warning", "challenge", "Challenge omits scope; compare the protected-resource scope list before authorization.")

    if challenge and prm and challenge.get("resource_metadata") != prm.get("url"):
        add("resource_metadata_url_mismatch", "error", "discovery", "Challenge metadata URL differs byte-for-byte from the fetched metadata URL.")

    resource_values = [("target", target)]
    if prm:
        resource_values.append(("metadata", prm.get("resource")))
    if auth and auth.get("resource"):
        resource_values.append(("authorization", auth.get("resource")))
    if token and token.get("resource"):
        resource_values.append(("token", token.get("resource")))
    concrete_resources = [(name, value) for name, value in resource_values if value]
    if concrete_resources and len({value for _, value in concrete_resources}) > 1:
        add("resource_indicator_mismatch", "error", "resource", "Resource indicators differ exactly; do not normalize trailing slashes or paths.")

    if prm and asm and asm.get("issuer") not in prm.get("authorization_servers", []):
        add("issuer_not_authorized", "error", "discovery", "Authorization-server issuer is absent from protected-resource metadata.")
    if auth and asm and auth.get("endpoint") and auth["endpoint"] != asm.get("authorization_endpoint"):
        add("authorization_endpoint_mismatch", "error", "authorization", "Authorization request endpoint differs from discovered metadata.")
    if token and asm and token.get("endpoint") and token["endpoint"] != asm.get("token_endpoint"):
        add("token_endpoint_mismatch", "error", "token", "Token request endpoint differs from discovered metadata.")

    required_scope: set[str] = set()
    if challenge and challenge.get("scope"):
        required_scope = set(challenge["scope"].split())
    elif prm:
        required_scope = set(prm.get("scopes_supported", []))
    auth_scope = set(auth.get("scope", [])) if auth else set()
    token_scope = set(token.get("scope", [])) if token else set()
    if required_scope and auth and not required_scope.issubset(auth_scope):
        add("authorization_scope_missing", "error", "authorization", "Authorization request omits one or more discovered required scopes.")
    if auth_scope and token:
        if not token_scope:
            add("token_scope_omitted", "warning", "token", "Token request omits the authorization scope; some authorization servers require it to be carried forward.")
        elif token_scope != auth_scope:
            add("token_scope_mismatch", "error", "token", "Token request scope differs from the authorization request scope.")

    if auth:
        if auth.get("pkce_method") != "S256":
            add("pkce_s256_missing", "error", "authorization", "Authorization request does not prove PKCE S256.")
        if asm and "S256" not in asm.get("code_challenge_methods_supported", []):
            add("pkce_support_unproven", "error", "discovery", "Authorization-server metadata does not advertise S256.")
    if token and token.get("pkce_verifier_present") is not True:
        add("pkce_verifier_missing", "error", "token", "Token request does not prove presence of the PKCE verifier.")
    if auth and token and auth.get("redirect_uri") != token.get("redirect_uri"):
        add("redirect_uri_mismatch", "error", "token", "Redirect URI differs between authorization and token requests.")

    if root["context"] == "mid_session" and challenge and challenge.get("error") == "invalid_token" and auth and not token:
        add("mid_session_reauth_incomplete", "error", "recovery", "A new authorization redirect began mid-session but no token exchange was observed.")
    if response and response["status"] >= 400:
        add("token_exchange_failed", "error", "token", f"Token endpoint returned HTTP {response['status']} ({response.get('error') or 'unspecified error'}).")
    if response and response["status"] < 400 and retry and retry["status"] in {401, 403}:
        add("token_rejected_on_retry", "error", "retry", "A successful token response was rejected by the protected resource; recheck exact resource, audience, and granted scope.")
    if response and response["status"] < 400 and required_scope:
        granted = set(response.get("granted_scope", []))
        if granted and not required_scope.issubset(granted):
            add("granted_scope_insufficient", "error", "token", "Granted scope does not cover the discovered required scope.")

    required_phases = (
        ("challenge", challenge),
        ("resource_metadata", prm),
        ("authorization_server_metadata", asm),
        ("authorization_request", auth),
        ("token_request", token),
        ("token_response", response),
    )
    for phase_name, evidence in required_phases:
        if evidence is None:
            add("evidence_incomplete", "error", phase_name, f"Required {phase_name} evidence was not observed.")
            break
    else:
        assert response is not None
        if response["status"] < 400 and retry is None:
            add("evidence_incomplete", "error", "retry", "A bounded protected-resource retry was not observed after token success.")

    errors = [item for item in findings if item["level"] == "error"]
    if errors:
        phase = errors[0]["phase"]
        next_action = f"Stop at {phase}; repair the first exact mismatch, then replay one bounded redacted flow from discovery."
        classification = "blocked"
    else:
        next_action = "Run one bounded MCP request with metadata-only logging; do not print or persist OAuth credentials."
        classification = "ready"
    return {
        "schema_version": 1, "profile": PROFILE, "classification": classification,
        "valid": not errors, "findings": findings, "next_action": next_action,
    }


def emit_json(report: dict[str, Any], stream: TextIO) -> None:
    try:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
    except (OSError, TypeError, ValueError) as exc:
        raise InputError(f"cannot serialize report: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--report", choices=["json"], default="json")
    args = parser.parse_args(argv)
    try:
        report = analyze(load_json(args.input))
        emit_json(report, sys.stdout)
    except InputError as exc:
        print(f"input-error: {exc}", file=sys.stderr)
        return 2
    return 1 if report["classification"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
