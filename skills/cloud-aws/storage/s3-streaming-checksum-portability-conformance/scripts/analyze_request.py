#!/usr/bin/env python3
"""Classify a redacted S3 upload request inventory without network access."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

FIELDS = {
    "operation",
    "content_encoding",
    "x_amz_content_sha256",
    "x_amz_trailer",
    "content_length_known",
    "returned_checksum_matches",
    "download_sha256_matches",
}
UPLOADS = {"PutObject", "UploadPart"}
STREAMING = {
    "STREAMING-AWS4-HMAC-SHA256-PAYLOAD-TRAILER": "signed-payload-trailer",
    "STREAMING-UNSIGNED-PAYLOAD-TRAILER": "unsigned-payload-trailer",
    "STREAMING-AWS4-HMAC-SHA256-PAYLOAD": "signed-streaming-payload",
}
CHECKSUM_TRAILERS = {
    "x-amz-checksum-crc32",
    "x-amz-checksum-crc32c",
    "x-amz-checksum-crc64nvme",
    "x-amz-checksum-sha1",
    "x-amz-checksum-sha256",
}
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
HEADER = re.compile(r"[\x21-\x7e]*\Z")


class InputError(ValueError):
    pass


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in pairs:
        if key in out:
            raise InputError(f"duplicate key: {key}")
        out[key] = value
    return out


def _bad_constant(value: str) -> None:
    raise InputError(f"non-standard JSON number: {value}")


def load(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InputError(f"cannot read input: {exc}") from exc
    try:
        value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_bad_constant)
    except (json.JSONDecodeError, InputError) as exc:
        raise InputError(f"invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise InputError("top-level value must be an object")
    unknown = sorted(set(value) - FIELDS)
    missing = sorted(FIELDS - set(value))
    if unknown or missing:
        raise InputError(f"schema mismatch; unknown={unknown}, missing={missing}")
    return value


def _nullable_bool(name: str, value: Any) -> None:
    if value is not None and type(value) is not bool:
        raise InputError(f"{name} must be boolean or null")


def validate(data: dict[str, Any]) -> None:
    if data["operation"] not in UPLOADS | {"GetObject"}:
        raise InputError("operation must be PutObject, UploadPart, or GetObject")
    for name in ("content_encoding", "x_amz_content_sha256", "x_amz_trailer"):
        value = data[name]
        if value is not None and (not isinstance(value, str) or not HEADER.fullmatch(value)):
            raise InputError(f"{name} must be null or printable ASCII without whitespace")
    if type(data["content_length_known"]) is not bool:
        raise InputError("content_length_known must be boolean")
    _nullable_bool("returned_checksum_matches", data["returned_checksum_matches"])
    _nullable_bool("download_sha256_matches", data["download_sha256_matches"])


def analyze(data: dict[str, Any]) -> tuple[dict[str, Any], int]:
    validate(data)
    operation = data["operation"]
    if operation == "GetObject":
        return {
            "status": "not-applicable",
            "applicable": False,
            "mode": "not-applicable",
            "observations": [],
            "violations": [],
            "next_action": "Use ordinary download checksum verification; no streaming upload compatibility workflow is indicated.",
        }, 2

    encoding = data["content_encoding"]
    token = data["x_amz_content_sha256"]
    trailer = data["x_amz_trailer"]
    chunked = encoding == "aws-chunked"
    has_trailer = trailer is not None
    known_checksum_trailer = trailer in CHECKSUM_TRAILERS
    observations: list[str] = []
    violations: list[str] = []

    if operation == "UploadPart":
        observations.append("multipart-operation")
    if chunked:
        observations.append("aws-chunked")
    if known_checksum_trailer:
        observations.append("checksum-trailer")
    if not data["content_length_known"]:
        observations.append("unknown-content-length")

    mode = "ambiguous"
    if has_trailer and not known_checksum_trailer:
        violations.append("unknown-checksum-trailer")
    declared = STREAMING.get(token)
    if declared in {"signed-payload-trailer", "unsigned-payload-trailer"}:
        if chunked and known_checksum_trailer:
            mode = declared
        else:
            violations.append("contradictory-streaming-evidence")
    elif declared == "signed-streaming-payload":
        if chunked and not has_trailer:
            mode = declared
        else:
            violations.append("contradictory-streaming-evidence")
    elif token == "UNSIGNED-PAYLOAD":
        if not chunked and not has_trailer:
            mode = "unsigned-payload"
        else:
            violations.append("contradictory-streaming-evidence")
    elif isinstance(token, str) and HEX64.fullmatch(token):
        if not chunked and not has_trailer:
            mode = "fixed-payload-hash"
        else:
            violations.append("contradictory-streaming-evidence")
    else:
        violations.append("unknown-payload-hash-mode")

    if encoding not in (None, "aws-chunked"):
        mode = "ambiguous"
        violations.append("unknown-content-encoding")
    if data["returned_checksum_matches"] is not True:
        violations.append("returned-checksum-unverified")
    if data["download_sha256_matches"] is not True:
        violations.append("download-integrity-unverified")
    if violations:
        status = "blocked"
        action = "Block rollout; capture a redacted final wire inventory, then run a disposable canary and require byte-for-byte download verification."
    else:
        status = "pass"
        action = "Run a disposable canary for this exact endpoint and mode; require returned-checksum agreement and byte-for-byte download verification before rollout."
    result = {
        "status": status,
        "applicable": True,
        "mode": mode,
        "observations": sorted(set(observations)),
        "violations": sorted(set(violations)),
        "next_action": action,
    }
    return result, 1 if violations else 0


def write_atomic(path: Path, payload: str) -> None:
    parent = path.parent
    if not parent.is_dir():
        raise OSError("output parent is not a directory")
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result, code = analyze(load(args.input))
        payload = json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n"
        if args.output:
            write_atomic(args.output, payload)
        else:
            sys.stdout.write(payload)
        return code
    except (InputError, OSError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
