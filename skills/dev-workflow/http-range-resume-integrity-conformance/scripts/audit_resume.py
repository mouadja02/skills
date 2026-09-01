#!/usr/bin/env python3
"""Offline fail-closed HTTP range-resume transcript auditor."""
import argparse
import json
import re
import sys

INVALID = 2
OUTPUT_ERROR = 74
CR_PART = re.compile(r"^bytes ([0-9]+)-([0-9]+)/([0-9]+)$")
CR_UNSAT = re.compile(r"^bytes \*/([0-9]+)$")

class InputError(ValueError):
    pass

def integer(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise InputError(f"{name} must be a non-negative integer")
    return value

def text(value, name):
    if not isinstance(value, str) or not value:
        raise InputError(f"{name} must be a non-empty string")
    return value

def headers(raw):
    if not isinstance(raw, dict):
        raise InputError("response.headers must be an object")
    out = {}
    for key, value in raw.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise InputError("header names and values must be strings")
        name = key.strip().lower()
        if not name or name in out:
            raise InputError(f"duplicate or empty header: {key!r}")
        out[name] = value.strip()
    return out

def strong_etag(value):
    return bool(re.fullmatch(r'"[^"\x00-\x1f\x7f]*"', value or ""))

def finding(code, detail):
    return {"code": code, "detail": detail}

def audit(doc):
    if not isinstance(doc, dict):
        raise InputError("root must be an object")
    cp = doc.get("checkpoint")
    req = doc.get("request")
    response = doc.get("response")
    if not isinstance(cp, dict) or not isinstance(req, dict) or not isinstance(response, dict):
        raise InputError("checkpoint, request, and response must be objects")
    local_size = integer(cp.get("local_size"), "checkpoint.local_size")
    expected_digest = cp.get("expected_sha256")
    if expected_digest is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", text(expected_digest, "checkpoint.expected_sha256")):
        raise InputError("checkpoint.expected_sha256 must contain 64 hexadecimal characters")
    checkpoint_etag = cp.get("etag")
    if checkpoint_etag is not None and not strong_etag(text(checkpoint_etag, "checkpoint.etag")):
        raise InputError("checkpoint.etag must be a strong quoted ETag")
    range_start = integer(req.get("range_start"), "request.range_start")
    status = integer(response.get("status"), "response.status")
    if status < 100 or status > 599:
        raise InputError("response.status must be between 100 and 599")
    body_length = integer(response.get("body_length"), "response.body_length")
    hs = headers(response.get("headers"))
    findings = []
    decision = "reject"
    write_mode = "none"

    if range_start != local_size:
        findings.append(finding("REQUEST_OFFSET_MISMATCH", "Range start differs from the persisted local size."))
    encoding = hs.get("content-encoding", "identity").lower()
    if encoding != "identity":
        findings.append(finding("CONTENT_ENCODING_UNSAFE", "Resume byte offsets require identity content encoding."))
    etag = hs.get("etag")
    if checkpoint_etag:
        if not etag or not strong_etag(etag):
            findings.append(finding("STRONG_VALIDATOR_REQUIRED", "The response lacks a strong ETag matching the checkpoint."))
        elif etag != checkpoint_etag:
            findings.append(finding("REPRESENTATION_CHANGED", "The response ETag differs from the checkpoint."))

    cr = hs.get("content-range")
    content_length = hs.get("content-length")
    parsed_length = None
    if content_length is not None:
        if not re.fullmatch(r"[0-9]+", content_length):
            findings.append(finding("INVALID_CONTENT_LENGTH", "Content-Length is not an unsigned decimal integer."))
        else:
            parsed_length = int(content_length)
            if parsed_length != body_length:
                findings.append(finding("BODY_LENGTH_MISMATCH", "Observed body length differs from Content-Length."))

    if status == 206:
        match = CR_PART.fullmatch(cr or "")
        if not match:
            findings.append(finding("INVALID_CONTENT_RANGE", "A 206 response requires a complete byte Content-Range."))
        else:
            start, end, total = map(int, match.groups())
            if start > end or end >= total:
                findings.append(finding("INVALID_CONTENT_RANGE", "Content-Range bounds are inconsistent."))
            if start != local_size or start != range_start:
                findings.append(finding("RANGE_START_MISMATCH", "Returned range does not begin at the persisted/requested offset."))
            if end >= start and end - start + 1 != body_length:
                findings.append(finding("RANGE_LENGTH_MISMATCH", "Returned range span differs from observed body length."))
        if not findings:
            decision, write_mode = "append", "append_at_verified_offset"
    elif status == 200:
        if cr is not None:
            findings.append(finding("STATUS_RANGE_CONTRADICTION", "A ranged 200 response carrying Content-Range is not safe to append or accept as a full response."))
        if not findings:
            decision, write_mode = "restart", "replace_temporary_from_zero"
    elif status == 416:
        match = CR_UNSAT.fullmatch(cr or "")
        if not match:
            findings.append(finding("INVALID_UNSATISFIED_RANGE", "A 416 response requires Content-Range: bytes */length."))
        else:
            total = int(match.group(1))
            if total == local_size and expected_digest:
                decision, write_mode = "verify_local_complete", "hash_existing_without_writing"
            elif total == local_size:
                findings.append(finding("COMPLETENESS_UNPROVEN", "Size equality without an independent digest does not prove completeness."))
            else:
                findings.append(finding("STALE_PARTIAL", "Remote complete length differs from the local partial size."))
    else:
        findings.append(finding("UNSUPPORTED_STATUS", "The response status is not a safe resume transition."))

    if findings:
        decision, write_mode = "reject", "none"
    return {"classification": decision, "write_mode": write_mode, "safe_to_append": decision == "append", "findings": findings}

def load(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle, parse_constant=lambda value: (_ for _ in ()).throw(InputError(f"non-finite JSON value: {value}")))
    except (OSError, UnicodeError, json.JSONDecodeError, InputError) as exc:
        raise InputError(str(exc)) from exc

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = audit(load(args.input))
    except InputError as exc:
        result = {"error": "invalid_input", "detail": str(exc)}
        code = INVALID
    else:
        code = 1 if result["findings"] else 0
    try:
        json.dump(result, sys.stdout, indent=2 if args.pretty else None, sort_keys=True, allow_nan=False)
        sys.stdout.write("\n")
        sys.stdout.flush()
    except (AttributeError, BrokenPipeError, OSError, UnicodeError, ValueError):
        return OUTPUT_ERROR
    return code
if __name__ == "__main__":
    raise SystemExit(main())
