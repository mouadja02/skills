#!/usr/bin/env python3
"""Fail-closed, bounded HTTP Content-Encoding chain fixture analyzer."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import math
import re
import sys
import zlib
from pathlib import Path
from typing import Any

TOKEN = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
DEFAULT_POLICY = {
    "max_chain": 4,
    "max_encoded_bytes": 1_048_576,
    "max_output_bytes": 8_388_608,
    "max_expansion_ratio": 100.0,
}
ALIASES = {"x-gzip": "gzip"}
SUPPORTED = {"gzip", "deflate", "x-gzip"}


class Rejection(Exception):
    def __init__(self, reason: str, detail: str):
        super().__init__(detail)
        self.reason = reason
        self.detail = detail


def strict_constant(value: str) -> Any:
    raise ValueError(f"non-standard JSON constant: {value}")


def require_positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise Rejection("invalid_policy", f"{name} must be a positive integer")
    return value


def load_policy(raw: Any) -> dict[str, Any]:
    if raw is None:
        raw = {}
    if not isinstance(raw, dict):
        raise Rejection("invalid_policy", "policy must be an object")
    unknown = set(raw) - set(DEFAULT_POLICY)
    if unknown:
        raise Rejection("invalid_policy", f"unknown policy keys: {sorted(unknown)}")
    policy = dict(DEFAULT_POLICY)
    policy.update(raw)
    for key in ("max_chain", "max_encoded_bytes", "max_output_bytes"):
        policy[key] = require_positive_int(policy[key], key)
    ratio = policy["max_expansion_ratio"]
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or not math.isfinite(ratio) or ratio <= 0:
        raise Rejection("invalid_policy", "max_expansion_ratio must be finite and positive")
    policy["max_expansion_ratio"] = float(ratio)
    return policy


def parse_chain(lines: Any, max_chain: int) -> list[str]:
    if not isinstance(lines, list) or any(not isinstance(line, str) for line in lines):
        raise Rejection("invalid_field_lines", "field_lines must be an array of strings")
    chain: list[str] = []
    for line in lines:
        for member in line.split(","):
            coding = member.strip().lower()
            if not coding:
                raise Rejection("empty_coding", "empty Content-Encoding list member")
            if not TOKEN.fullmatch(coding):
                raise Rejection("invalid_coding", f"invalid content-coding token: {coding!r}")
            chain.append(coding)
    if len(chain) > max_chain:
        raise Rejection("chain_limit_exceeded", f"coding count {len(chain)} exceeds max_chain {max_chain}")
    if "identity" in chain:
        raise Rejection("identity_not_allowed", "identity is reserved and not accepted in Content-Encoding")
    unknown = [coding for coding in chain if coding not in SUPPORTED]
    if unknown:
        raise Rejection("unsupported_coding", f"unsupported content-coding(s): {unknown}")
    return chain


def bounded_decompress(data: bytes, coding: str, cap: int) -> bytes:
    wbits = 31 if coding == "gzip" else zlib.MAX_WBITS
    decoder = zlib.decompressobj(wbits)
    try:
        output = decoder.decompress(data, cap + 1)
    except zlib.error as exc:
        raise Rejection("decode_error", f"{coding} decoding failed: {exc}") from exc
    if len(output) > cap or decoder.unconsumed_tail:
        raise Rejection("output_limit_exceeded", f"decoded layer exceeds max_output_bytes {cap}")
    try:
        output += decoder.flush(cap + 1 - len(output))
    except (ValueError, zlib.error) as exc:
        raise Rejection("decode_error", f"{coding} flush failed: {exc}") from exc
    if len(output) > cap:
        raise Rejection("output_limit_exceeded", f"decoded layer exceeds max_output_bytes {cap}")
    if not decoder.eof:
        raise Rejection("truncated_stream", f"{coding} stream did not reach end marker")
    if decoder.unused_data:
        raise Rejection("trailing_data", f"{coding} stream has trailing or concatenated data")
    return output


def analyze(document: Any) -> tuple[dict[str, Any], int]:
    report: dict[str, Any] = {"status": "rejected", "reason": None, "application_order": [], "inverse_order": [], "transitions": []}
    try:
        if not isinstance(document, dict):
            raise Rejection("invalid_document", "top-level JSON value must be an object")
        allowed = {"field_lines", "body_base64", "policy", "transfer_encoding"}
        unknown_keys = set(document) - allowed
        if unknown_keys:
            raise Rejection("invalid_document", f"unknown top-level keys: {sorted(unknown_keys)}")
        policy = load_policy(document.get("policy"))
        chain = parse_chain(document.get("field_lines"), policy["max_chain"])
        report.update({"policy": policy, "application_order": chain, "inverse_order": list(reversed(chain))})
        if not chain:
            transfer = document.get("transfer_encoding")
            if transfer is not None and not isinstance(transfer, str):
                raise Rejection("invalid_transfer_encoding", "transfer_encoding must be a string")
            report.update({"status": "not_applicable", "reason": "content_encoding_absent", "conceptual_layer": "transfer-coding/message-framing" if transfer else "no-content-coding"})
            return report, 0
        if "body_base64" not in document:
            report.update({"status": "preflight_ok", "reason": None})
            return report, 0
        encoded_text = document["body_base64"]
        if not isinstance(encoded_text, str):
            raise Rejection("invalid_body", "body_base64 must be a string")
        try:
            current = base64.b64decode(encoded_text, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise Rejection("invalid_base64", "body_base64 is not canonical base64") from exc
        if len(current) > policy["max_encoded_bytes"]:
            raise Rejection("encoded_limit_exceeded", f"encoded body exceeds max_encoded_bytes {policy['max_encoded_bytes']}")
        encoded_size = len(current)
        for coding in reversed(chain):
            canonical = ALIASES.get(coding, coding)
            before = current
            current = bounded_decompress(before, canonical, policy["max_output_bytes"])
            report["transitions"].append({
                "coding": coding,
                "input_bytes": len(before),
                "output_bytes": len(current),
                "output_sha256": hashlib.sha256(current).hexdigest(),
            })
        ratio = len(current) / max(encoded_size, 1)
        if ratio > policy["max_expansion_ratio"]:
            raise Rejection("expansion_ratio_exceeded", f"final expansion ratio {ratio:.6g} exceeds cap {policy['max_expansion_ratio']:.6g}")
        report.update({"status": "decoded", "reason": None, "encoded_bytes": encoded_size, "decoded_bytes": len(current), "expansion_ratio": ratio, "final_sha256": hashlib.sha256(current).hexdigest()})
        return report, 0
    except Rejection as exc:
        report.update({"status": "rejected", "reason": exc.reason, "detail": exc.detail})
        return report, 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    args = parser.parse_args(argv)
    try:
        with args.fixture.open("r", encoding="utf-8") as handle:
            document = json.load(handle, parse_constant=strict_constant)
        report, code = analyze(document)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        report, code = ({"status": "rejected", "reason": "input_error", "detail": str(exc), "application_order": [], "inverse_order": [], "transitions": []}, 2)
    try:
        sys.stdout.write(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
        sys.stdout.flush()
    except (BrokenPipeError, OSError):
        return 3
    return code


if __name__ == "__main__":
    raise SystemExit(main())
