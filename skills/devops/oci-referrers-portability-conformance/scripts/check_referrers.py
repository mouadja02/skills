#!/usr/bin/env python3
"""Offline OCI Distribution 1.1.1 referrers snapshot comparator."""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROFILE = "oci-distribution-1.1.1"
INDEX_MEDIA_TYPE = "application/vnd.oci.image.index.v1+json"
DIGEST_RE = re.compile(r"^[a-z0-9]+(?:[+._-][a-z0-9]+)*:[A-Fa-f0-9]{32,}$")


class InputError(ValueError):
    pass


def _reject_constant(value: str) -> None:
    raise InputError(f"non-standard JSON number {value!r}")


def load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle, parse_constant=_reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, InputError) as exc:
        raise InputError(f"cannot read valid JSON from {path}: {exc}") from exc


def _finite(value: Any, path: str = "$") -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise InputError(f"{path} contains a non-finite number")
    if isinstance(value, dict):
        for key, child in value.items():
            _finite(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _finite(child, f"{path}[{index}]")


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{path} must be an object")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value:
        raise InputError(f"{path} must be a non-empty string")
    return value


def _digest(value: Any, path: str) -> str:
    text = _string(value, path)
    if not DIGEST_RE.fullmatch(text):
        raise InputError(f"{path} is not a supported digest")
    return text.lower()


def _finding(code: str, path: str, message: str, severity: str = "error") -> dict[str, str]:
    return {"code": code, "severity": severity, "path": path, "message": message}


def _descriptor(value: Any, path: str) -> dict[str, Any]:
    item = _object(value, path)
    digest = _digest(item.get("digest"), f"{path}.digest")
    media_type = _string(item.get("mediaType"), f"{path}.mediaType")
    size = item.get("size")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise InputError(f"{path}.size must be a non-negative integer")
    artifact_type = item.get("artifactType")
    if artifact_type is not None and (not isinstance(artifact_type, str) or not artifact_type):
        raise InputError(f"{path}.artifactType must be a non-empty string when present")
    annotations = item.get("annotations", {})
    if not isinstance(annotations, dict) or not all(
        isinstance(key, str) and isinstance(val, str) for key, val in annotations.items()
    ):
        raise InputError(f"{path}.annotations must be a string-to-string object")
    return {
        "digest": digest,
        "mediaType": media_type,
        "size": size,
        "artifactType": artifact_type,
        "annotations": annotations,
    }


def _endpoint(value: Any, path: str) -> tuple[list[dict[str, Any]], set[str], list[dict[str, str]], str]:
    endpoint = _object(value, path)
    status = endpoint.get("api_status")
    if isinstance(status, bool) or not isinstance(status, int):
        raise InputError(f"{path}.api_status must be an integer")
    findings: list[dict[str, str]] = []
    if status == 200:
        mode = "api"
    elif status == 404:
        mode = "fallback_tag"
        fallback = endpoint.get("fallback_status")
        if isinstance(fallback, bool) or not isinstance(fallback, int):
            raise InputError(f"{path}.fallback_status must be an integer after API 404")
        if fallback != 200:
            findings.append(_finding("FALLBACK_UNAVAILABLE", f"{path}.fallback_status", "referrers API returned 404 and fallback tag did not return 200"))
    else:
        mode = "invalid"
        findings.append(_finding("UNEXPECTED_API_STATUS", f"{path}.api_status", "expected 200 or the defined 404 fallback boundary"))

    content_type = endpoint.get("content_type")
    if content_type != INDEX_MEDIA_TYPE:
        findings.append(_finding("INVALID_INDEX_MEDIA_TYPE", f"{path}.content_type", f"expected {INDEX_MEDIA_TYPE}"))
    raw = endpoint.get("referrers")
    if not isinstance(raw, list):
        raise InputError(f"{path}.referrers must be an array")
    descriptors = [_descriptor(item, f"{path}.referrers[{index}]") for index, item in enumerate(raw)]
    counts = Counter(item["digest"] for item in descriptors)
    for digest, count in sorted(counts.items()):
        if count > 1:
            findings.append(_finding("DUPLICATE_DESCRIPTOR", f"{path}.referrers", f"digest {digest} appears {count} times"))

    coverage_raw = endpoint.get("platform_coverage", [])
    if not isinstance(coverage_raw, list):
        raise InputError(f"{path}.platform_coverage must be an array")
    coverage = {_digest(item, f"{path}.platform_coverage[{index}]") for index, item in enumerate(coverage_raw)}
    return descriptors, coverage, findings, mode


def analyze(document: Any) -> dict[str, Any]:
    _finite(document)
    root = _object(document, "$")
    if root.get("kind") != "oci_referrers_audit":
        return {
            "schema_version": 1,
            "status": "not_applicable",
            "applicable": False,
            "profile": None,
            "findings": [],
            "mutation_permitted": False,
        }
    if root.get("schema_version") != 1:
        raise InputError("$.schema_version must equal 1")
    if root.get("profile") != PROFILE:
        raise InputError(f"$.profile must equal {PROFILE!r}")
    subject = _digest(root.get("subject"), "$.subject")
    platform_raw = root.get("platform_subjects", [])
    if not isinstance(platform_raw, list):
        raise InputError("$.platform_subjects must be an array")
    platforms = {_digest(item, f"$.platform_subjects[{index}]") for index, item in enumerate(platform_raw)}

    source, source_coverage, source_findings, source_mode = _endpoint(root.get("source"), "$.source")
    destination, destination_coverage, destination_findings, destination_mode = _endpoint(root.get("destination"), "$.destination")
    findings = source_findings + destination_findings

    source_by_digest = {item["digest"]: item for item in source}
    destination_by_digest = {item["digest"]: item for item in destination}
    for digest in sorted(source_by_digest.keys() - destination_by_digest.keys()):
        findings.append(_finding("DESTINATION_MISSING_REFERRER", "$.destination.referrers", f"source descriptor {digest} is absent"))
    for digest in sorted(destination_by_digest.keys() - source_by_digest.keys()):
        findings.append(_finding("DESTINATION_EXTRA_REFERRER", "$.destination.referrers", f"destination descriptor {digest} is absent from source", "warning"))
    for digest in sorted(source_by_digest.keys() & destination_by_digest.keys()):
        left, right = source_by_digest[digest], destination_by_digest[digest]
        if left["mediaType"] != right["mediaType"] or left["size"] != right["size"]:
            findings.append(_finding("DESCRIPTOR_IDENTITY_DRIFT", "$.destination.referrers", f"mediaType or size changed for {digest}"))
        if left["artifactType"] != right["artifactType"]:
            findings.append(_finding("ARTIFACT_TYPE_DRIFT", "$.destination.referrers", f"artifactType changed for {digest}"))
        if left["annotations"] != right["annotations"]:
            findings.append(_finding("ANNOTATION_DRIFT", "$.destination.referrers", f"annotations changed for {digest}"))

    for digest in sorted(platforms - source_coverage):
        findings.append(_finding("SOURCE_PLATFORM_COVERAGE_MISSING", "$.source.platform_coverage", f"declared platform subject {digest} was not inventoried at source"))
    for digest in sorted(source_coverage - destination_coverage):
        findings.append(_finding("DESTINATION_PLATFORM_COVERAGE_MISSING", "$.destination.platform_coverage", f"source platform subject {digest} is absent at destination"))

    errors = sum(item["severity"] == "error" for item in findings)
    status = "fail" if errors else ("review" if findings else "pass")
    algorithm, encoded = subject.split(":", 1)
    return {
        "schema_version": 1,
        "status": status,
        "applicable": True,
        "profile": PROFILE,
        "subject": subject,
        "fallback_tag": f"{algorithm}-{encoded[:64]}",
        "modes": {"source": source_mode, "destination": destination_mode},
        "counts": {"source": len(source), "destination": len(destination), "errors": errors, "warnings": len(findings) - errors},
        "findings": findings,
        "mutation_permitted": False,
    }


def _write_report(report: dict[str, Any], output: str | None) -> None:
    text = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if output is None:
        sys.stdout.write(text)
        return
    target = Path(output)
    temporary = target.with_name(f".{target.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except OSError as exc:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise InputError(f"cannot write report to {target}: {exc}") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        report = analyze(load_json(Path(args.input)))
        _write_report(report, args.output)
    except InputError as exc:
        report = {"schema_version": 1, "status": "input_error", "applicable": False, "error": str(exc), "findings": [], "mutation_permitted": False}
        try:
            _write_report(report, args.output)
        except InputError:
            sys.stderr.write(json.dumps(report, sort_keys=True) + "\n")
        return 2
    return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
