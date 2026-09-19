#!/usr/bin/env python3
"""Offline OCI image-index platform and graph conformance analyzer."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

INDEX_MT = "application/vnd.oci.image.index.v1+json"
IMAGE_MT = "application/vnd.oci.image.manifest.v1+json"
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

class InputError(ValueError):
    pass

def reject_constant(value: str) -> None:
    raise InputError(f"non-finite JSON value: {value}")

def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, InputError) as exc:
        raise InputError(f"cannot read valid JSON input: {exc}") from exc

def finding(code: str, path: str, message: str, severity: str = "error") -> dict[str, str]:
    return {"code": code, "path": path, "severity": severity, "message": message}

def require_dict(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{path} must be an object")
    return value

def validate_platform(value: Any, path: str) -> dict[str, Any]:
    platform = require_dict(value, path)
    for key in ("os", "architecture"):
        if not isinstance(platform.get(key), str) or not platform[key]:
            raise InputError(f"{path}.{key} must be a non-empty string")
    for key in ("variant", "os.version"):
        if key in platform and (not isinstance(platform[key], str) or not platform[key]):
            raise InputError(f"{path}.{key} must be a non-empty string")
    for key in ("os.features", "features"):
        if key in platform and (not isinstance(platform[key], list) or not all(isinstance(x, str) and x for x in platform[key])):
            raise InputError(f"{path}.{key} must be an array of non-empty strings")
    return platform

def validate_descriptor(value: Any, path: str) -> dict[str, Any]:
    desc = require_dict(value, path)
    if not isinstance(desc.get("mediaType"), str) or not desc["mediaType"]:
        raise InputError(f"{path}.mediaType must be a non-empty string")
    if not isinstance(desc.get("digest"), str) or not DIGEST_RE.fullmatch(desc["digest"]):
        raise InputError(f"{path}.digest must be lowercase sha256 with 64 hex characters")
    size = desc.get("size")
    if isinstance(size, bool) or not isinstance(size, int) or size < 0:
        raise InputError(f"{path}.size must be a non-negative integer")
    if "platform" in desc:
        validate_platform(desc["platform"], f"{path}.platform")
    return desc

def validate_snapshot(value: Any, path: str) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    snap = require_dict(value, path)
    index = require_dict(snap.get("index"), f"{path}.index")
    if index.get("schemaVersion") != 2:
        raise InputError(f"{path}.index.schemaVersion must equal 2")
    if "mediaType" in index and index["mediaType"] != INDEX_MT:
        raise InputError(f"{path}.index.mediaType must be {INDEX_MT}")
    manifests = index.get("manifests")
    if not isinstance(manifests, list):
        raise InputError(f"{path}.index.manifests must be an array")
    validated = [validate_descriptor(item, f"{path}.index.manifests[{i}]") for i, item in enumerate(manifests)]
    children = snap.get("children", {})
    children = require_dict(children, f"{path}.children")
    for digest, child in children.items():
        if not isinstance(digest, str) or not DIGEST_RE.fullmatch(digest):
            raise InputError(f"{path}.children keys must be lowercase sha256 digests")
        child = require_dict(child, f"{path}.children[{digest}]")
        if child.get("schemaVersion") != 2:
            raise InputError(f"{path}.children[{digest}].schemaVersion must equal 2")
        validate_platform(require_dict(child.get("config"), f"{path}.children[{digest}].config"), f"{path}.children[{digest}].config")
    return index, validated, children

def platform_tuple(p: dict[str, Any]) -> tuple[str, str, str | None, str | None, tuple[str, ...]]:
    return (p["os"], p["architecture"], p.get("variant"), p.get("os.version"), tuple(p.get("os.features", [])))

def matches(request: dict[str, Any], platform: dict[str, Any]) -> bool:
    return all(platform.get(key) == value for key, value in request.items())

def analyze(data: Any) -> tuple[dict[str, Any], int]:
    if isinstance(data, dict) and data.get("mediaType") == "application/vnd.oci.image.manifest.v1+json" and data.get("kind") is None:
        return {"schema_version": 1, "applicable": False, "status": "not_applicable", "profile": None, "selected_digest": None, "findings": [], "observations": [], "mutation_permitted": False}, 0
    root = require_dict(data, "$input")
    if root.get("kind") != "oci_image_platform_graph_audit":
        raise InputError("kind must be oci_image_platform_graph_audit, or input must be a single OCI image manifest")
    if root.get("schema_version") != 1:
        raise InputError("schema_version must equal 1")
    if root.get("profile") != "oci-image-spec-1.1.1":
        raise InputError("profile must be oci-image-spec-1.1.1")
    if root.get("matcher") != "exact":
        raise InputError("matcher must be exact; runtime-specific compatibility requires a separate declared profile")
    request = validate_platform(root.get("request"), "$input.request")
    _, before, children = validate_snapshot(root.get("before"), "$input.before")
    findings: list[dict[str, str]] = []
    observations: list[dict[str, Any]] = []
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []
    for i, desc in enumerate(before):
        path = f"$input.before.index.manifests[{i}]"
        digest = desc["digest"]
        if digest in seen:
            findings.append(finding("DUPLICATE_DESCRIPTOR_DIGEST", path, f"descriptor digest {digest} is repeated"))
        seen.add(digest)
        if desc["mediaType"] == IMAGE_MT:
            if "platform" not in desc:
                findings.append(finding("MISSING_PLATFORM", path, "platform-specific image descriptor has no platform"))
            else:
                if matches(request, desc["platform"]):
                    candidates.append(desc)
                child = children.get(digest)
                if child is None:
                    findings.append(finding("MISSING_CHILD_CONTENT", path, f"no child config observation for {digest}"))
                elif platform_tuple(desc["platform"]) != platform_tuple(child["config"]):
                    findings.append(finding("PLATFORM_CONFIG_MISMATCH", path, "descriptor platform differs from child image config platform"))
        elif "platform" in desc:
            observations.append({"code": "NON_IMAGE_DESCRIPTOR_PLATFORM", "path": path, "digest": digest})
    selected = candidates[0]["digest"] if candidates else None
    if not candidates:
        findings.append(finding("NO_PLATFORM_MATCH", "$input.request", "no image descriptor exactly matches the requested platform"))
    elif len(candidates) > 1:
        findings.append(finding("AMBIGUOUS_PLATFORM_MATCH", "$input.request", f"{len(candidates)} descriptors match; first-match selection is ambiguous"))
    if "after" in root:
        _, after, after_children = validate_snapshot(root["after"], "$input.after")
        before_by = {d["digest"]: d for d in before}
        after_by = {d["digest"]: d for d in after}
        for digest, desc in before_by.items():
            if digest not in after_by:
                findings.append(finding("GRAPH_DESCRIPTOR_REMOVED", "$input.after.index.manifests", f"before descriptor {digest} is absent after transport"))
            elif desc != after_by[digest]:
                findings.append(finding("GRAPH_DESCRIPTOR_DRIFT", "$input.after.index.manifests", f"descriptor metadata changed for {digest}"))
            elif digest in children and digest not in after_children:
                findings.append(finding("GRAPH_CHILD_REMOVED", "$input.after.children", f"child observation {digest} is absent after transport"))
            elif digest in children and children[digest] != after_children[digest]:
                findings.append(finding("GRAPH_CHILD_DRIFT", "$input.after.children", f"child config observation changed for {digest}"))
        before_order = [d["digest"] for d in before if d["digest"] in after_by]
        after_order = [d["digest"] for d in after if d["digest"] in before_by]
        if before_order != after_order:
            findings.append(finding("GRAPH_ORDER_CHANGED", "$input.after.index.manifests", "relative order of preserved descriptors changed"))
        extras = [d["digest"] for d in after if d["digest"] not in before_by]
        if extras:
            observations.append({"code": "GRAPH_DESCRIPTORS_ADDED", "digests": extras})
    status = "fail" if findings else ("review" if observations else "pass")
    report = {"schema_version": 1, "applicable": True, "status": status, "profile": root["profile"], "matcher": root["matcher"], "selected_digest": selected, "match_count": len(candidates), "findings": findings, "observations": observations, "mutation_permitted": False}
    return report, 1 if findings else 0

def emit(report: dict[str, Any], output: Path | None) -> None:
    text = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    try:
        if output:
            output.write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
            sys.stdout.flush()
    except (OSError, UnicodeError) as exc:
        raise InputError(f"cannot write report: {exc}") from exc

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report, code = analyze(load_json(args.input))
        emit(report, args.output)
        return code
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
