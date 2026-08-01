#!/usr/bin/env python3
"""Fail-closed offline checker for redacted Gateway API BackendTLSPolicy observations."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

MAX_BYTES = 1_000_000
PROFILE = "gateway-api-v1.6.1"
KIND = "gateway_backend_tls_audit"
FEATURE_BASE = "BackendTLSPolicy"
FEATURE_SAN = "BackendTLSPolicySANValidation"
RESULTS = {"success", "http_5xx", "not_run"}
ROTATION_RESULTS = {"reconciled", "not_run"}

class InputError(ValueError):
    pass

def obj(value: Any, name: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise InputError(f"{name} must be an object")
    return value

def text(value: Any, name: str) -> str:
    if type(value) is not str or not value.strip() or "\x00" in value:
        raise InputError(f"{name} must be a non-empty NUL-free string")
    return value

def boolean(value: Any, name: str) -> bool:
    if type(value) is not bool:
        raise InputError(f"{name} must be a boolean")
    return value

def exact_keys(value: dict[str, Any], required: set[str], optional: set[str], name: str) -> None:
    missing = required - value.keys()
    unknown = value.keys() - required - optional
    if missing:
        raise InputError(f"{name} missing keys: {', '.join(sorted(missing))}")
    if unknown:
        raise InputError(f"{name} has unknown keys: {', '.join(sorted(unknown))}")

def load(path: Path) -> Any:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise InputError(f"cannot read input: {exc}") from exc
    if len(raw) > MAX_BYTES:
        raise InputError(f"input exceeds {MAX_BYTES} bytes")
    try:
        return json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(InputError(f"non-standard number {value}")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError(f"invalid JSON: {exc}") from exc

def finding(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}

def evaluate(data: Any) -> dict[str, Any]:
    root = obj(data, "root")
    kind = text(root.get("kind"), "kind")
    if kind != KIND:
        return {"schema_version": 1, "status": "not_applicable", "mutation_permitted": False,
                "findings": [], "summary": "Input is not a Gateway API BackendTLSPolicy audit."}
    exact_keys(root, {"schema_version", "kind", "profile", "inventory", "policy", "probes"}, set(), "root")
    if type(root["schema_version"]) is not int or root["schema_version"] != 1:
        raise InputError("schema_version must be integer 1")
    if text(root["profile"], "profile") != PROFILE:
        raise InputError(f"profile must be {PROFILE}")

    inv = obj(root["inventory"], "inventory")
    exact_keys(inv, {"controller", "controller_version", "gateway_api_version", "supported_features"}, set(), "inventory")
    for key in ("controller", "controller_version", "gateway_api_version"):
        text(inv[key], f"inventory.{key}")
    if inv["gateway_api_version"] != "v1.6.1":
        raise InputError("inventory.gateway_api_version must be v1.6.1 for this profile")
    features = inv["supported_features"]
    if type(features) is not list or any(type(x) is not str or not x for x in features):
        raise InputError("inventory.supported_features must be an array of non-empty strings")
    if len(features) != len(set(features)):
        raise InputError("inventory.supported_features must not contain duplicates")

    pol = obj(root["policy"], "policy")
    required = {"namespace", "target_namespace", "target_kind", "target_name", "target_exists",
                "target_refs_distinct", "ca_source", "hostname", "subject_alt_name_types",
                "competing_policy", "conditions"}
    exact_keys(pol, required, set(), "policy")
    for key in ("namespace", "target_namespace", "target_kind", "target_name", "hostname"):
        text(pol[key], f"policy.{key}")
    for key in ("target_exists", "target_refs_distinct", "competing_policy"):
        boolean(pol[key], f"policy.{key}")
    if pol["ca_source"] not in {"ConfigMap", "System"}:
        raise InputError("policy.ca_source must be ConfigMap or System")
    sans = pol["subject_alt_name_types"]
    if type(sans) is not list or any(x not in {"Hostname", "URI"} for x in sans) or len(sans) != len(set(sans)):
        raise InputError("policy.subject_alt_name_types must be a unique array of Hostname/URI values")
    conditions = obj(pol["conditions"], "policy.conditions")
    exact_keys(conditions, {"Accepted", "ResolvedRefs"}, set(), "policy.conditions")
    for key in conditions:
        boolean(conditions[key], f"policy.conditions.{key}")

    probes = obj(root["probes"], "probes")
    required_probes = {"valid_ca_hostname", "untrusted_ca", "mismatched_hostname", "configmap_rotation"}
    allowed_probes = required_probes | {"hostname_san_match", "hostname_san_mismatch", "uri_san_match", "uri_san_mismatch", "chain_depth"}
    exact_keys(probes, required_probes, allowed_probes - required_probes, "probes")
    for key, value in probes.items():
        allowed = ROTATION_RESULTS if key == "configmap_rotation" else RESULTS
        if value not in allowed:
            raise InputError(f"probes.{key} must be one of {sorted(allowed)}")

    findings: list[dict[str, str]] = []
    if FEATURE_BASE not in features:
        findings.append(finding("FEATURE_UNADVERTISED", "Controller did not advertise BackendTLSPolicy support."))
    if not conditions["Accepted"]:
        findings.append(finding("POLICY_NOT_ACCEPTED", "Accepted is not true."))
    if not conditions["ResolvedRefs"]:
        findings.append(finding("REFS_UNRESOLVED", "ResolvedRefs is not true."))
    if pol["namespace"] != pol["target_namespace"] or pol["target_kind"] != "Service" or not pol["target_exists"]:
        findings.append(finding("TARGET_ATTACHMENT_INVALID", "Target must be an existing same-namespace Service."))
    if not pol["target_refs_distinct"]:
        findings.append(finding("TARGET_REFS_CONFLICT", "Target references are not distinct by target/section."))
    if probes["valid_ca_hostname"] != "success":
        findings.append(finding("VALID_PATH_FAILED", "Valid CA and hostname probe did not succeed."))
    if probes["untrusted_ca"] != "http_5xx":
        findings.append(finding("UNTRUSTED_CA_ACCEPTED", "Untrusted CA probe did not fail closed with HTTP 5xx."))
    if probes["mismatched_hostname"] != "http_5xx":
        findings.append(finding("HOSTNAME_MISMATCH_ACCEPTED", "Mismatched hostname probe did not fail closed with HTTP 5xx."))
    if pol["ca_source"] == "ConfigMap" and probes["configmap_rotation"] != "reconciled":
        findings.append(finding("CA_ROTATION_NOT_RECONCILED", "ConfigMap CA rotation was not observed to reconcile."))
    if sans:
        if FEATURE_SAN not in features:
            findings.append(finding("SAN_FEATURE_UNADVERTISED", "SAN validation was requested but not advertised."))
        if "Hostname" in sans:
            if probes.get("hostname_san_match") != "success":
                findings.append(finding("HOSTNAME_SAN_MATCH_FAILED", "Matching hostname SAN did not succeed."))
            if probes.get("hostname_san_mismatch") != "http_5xx":
                findings.append(finding("HOSTNAME_SAN_MISMATCH_ACCEPTED", "Mismatching hostname SAN did not fail closed."))
        if "URI" in sans:
            if probes.get("uri_san_match") != "success":
                findings.append(finding("URI_SAN_MATCH_FAILED", "Matching URI SAN did not succeed."))
            if probes.get("uri_san_mismatch") != "http_5xx":
                findings.append(finding("URI_SAN_MISMATCH_ACCEPTED", "Mismatching URI SAN did not fail closed."))
    if probes.get("chain_depth") == "http_5xx":
        findings.append(finding("CHAIN_DEPTH_FAILURE", "A valid bounded certificate-chain probe failed."))
    if pol["competing_policy"]:
        findings.append(finding("POLICY_PRECEDENCE_UNRESOLVED", "An implementation-native competing policy requires an isolated precedence test."))

    return {"schema_version": 1, "status": "fail" if findings else "pass", "mutation_permitted": False,
            "findings": findings, "summary": f"{len(findings)} conformance finding(s)."}

def write_report(report: dict[str, Any], output: Path | None) -> None:
    payload = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if output is None:
        sys.stdout.write(payload)
        return
    try:
        output.write_text(payload, encoding="utf-8")
    except OSError as exc:
        raise InputError(f"cannot write report: {exc}") from exc

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = evaluate(load(args.input))
        write_report(report, args.output)
    except InputError as exc:
        print(f"input error: {exc}", file=sys.stderr)
        return 2
    return 1 if report["status"] == "fail" else 0

if __name__ == "__main__":
    raise SystemExit(main())
