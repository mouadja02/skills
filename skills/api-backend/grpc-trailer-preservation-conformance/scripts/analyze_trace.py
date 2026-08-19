#!/usr/bin/env python3
"""Offline analyzer for redacted gRPC response-trailer observations."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

MAX_FILE = 1_000_000
MAX_CASES = 64
MAX_HOPS = 16
MAX_FIELDS = 128
MAX_VALUE = 16_384
STATUS_RE = re.compile(r"[0-9]+\Z")


class InputError(ValueError):
    pass


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise InputError(f"duplicate JSON member: {key}")
        out[key] = value
    return out


def _constant(value):
    raise InputError(f"non-standard JSON number: {value}")


def load_json(path: Path):
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise InputError(f"cannot read input: {exc}") from exc
    if len(raw) > MAX_FILE:
        raise InputError("input exceeds 1000000 bytes")
    try:
        return json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError(f"invalid JSON: {exc}") from exc


def obj(value, name):
    if not isinstance(value, dict):
        raise InputError(f"{name} must be an object")
    return value


def text(value, name, *, maximum=256):
    if not isinstance(value, str) or not value or len(value) > maximum or "\x00" in value:
        raise InputError(f"{name} must be a non-empty bounded string without NUL")
    return value


def integer(value, name, *, minimum=0, maximum=1_000_000):
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise InputError(f"{name} must be an integer in [{minimum}, {maximum}]")
    return value


def boolean(value, name):
    if not isinstance(value, bool):
        raise InputError(f"{name} must be boolean")
    return value


def fields(value, name):
    value = obj(value, name)
    if len(value) > MAX_FIELDS:
        raise InputError(f"{name} has too many fields")
    normalized = {}
    for raw_key, raw_values in value.items():
        key = text(raw_key, f"{name} key", maximum=128).lower()
        if key in normalized:
            raise InputError(f"{name} has case-insensitive duplicate field {key}")
        if not isinstance(raw_values, list) or not raw_values:
            raise InputError(f"{name}.{key} must be a non-empty string array")
        values = []
        for index, item in enumerate(raw_values):
            values.append(text(item, f"{name}.{key}[{index}]", maximum=MAX_VALUE))
        normalized[key] = values
    return normalized


def expected_shape(case, index):
    expected = obj(case.get("expected"), f"cases[{index}].expected")
    status = text(expected.get("grpc_status"), f"cases[{index}].expected.grpc_status", maximum=3)
    if not STATUS_RE.fullmatch(status):
        raise InputError(f"cases[{index}].expected.grpc_status must contain digits only")
    trailers = fields(expected.get("trailers"), f"cases[{index}].expected.trailers")
    if trailers.get("grpc-status") != [status]:
        raise InputError(f"cases[{index}] expected trailers must contain exactly grpc-status={status}")
    return {
        "grpc_status": status,
        "messages": integer(expected.get("messages"), f"cases[{index}].expected.messages"),
        "trailers": trailers,
        "trailers_only": boolean(expected.get("trailers_only"), f"cases[{index}].expected.trailers_only"),
    }


def analyze_observation(observation, expected, case_index, hop_index):
    prefix = f"cases[{case_index}].observations[{hop_index}]"
    observation = obj(observation, prefix)
    hop = text(observation.get("hop"), f"{prefix}.hop")
    protocol = text(observation.get("http_version"), f"{prefix}.http_version", maximum=16)
    initial = fields(observation.get("initial_headers", {}), f"{prefix}.initial_headers")
    trailers = fields(observation.get("trailers", {}), f"{prefix}.trailers")
    if "grpc-status" in initial:
        return hop, "LOSS", ["grpc-status recorded as initial metadata instead of terminal metadata"]
    messages = integer(observation.get("messages"), f"{prefix}.messages")
    trailers_only = boolean(observation.get("trailers_only"), f"{prefix}.trailers_only")
    end_stream = boolean(observation.get("end_stream"), f"{prefix}.end_stream")
    declared = boolean(observation.get("declared_limit", False), f"{prefix}.declared_limit")
    evidence = boolean(observation.get("limit_evidence", False), f"{prefix}.limit_evidence")
    configured = observation.get("configured_trailer_limit_bytes")
    signature = observation.get("rejection_signature")

    if protocol not in ("h2", "h2c"):
        return hop, "OTHER_FAILURE", [f"unsupported response leg {protocol}; use a separately pinned translation profile"]

    if declared:
        valid_limit = (
            evidence
            and isinstance(configured, int) and not isinstance(configured, bool) and configured > 0
            and isinstance(signature, str) and bool(signature.strip()) and len(signature) <= 256
            and not trailers
        )
        if valid_limit:
            return hop, "DECLARED_LIMIT", []
        return hop, "LOSS", ["configured/claimed limit lacks fail-closed telemetry, signature, or has partial trailers"]

    reasons = []
    if not end_stream:
        reasons.append("terminal END_STREAM absent")
    if messages != expected["messages"]:
        reasons.append(f"message count {messages} != expected {expected['messages']}")
    if trailers_only != expected["trailers_only"]:
        reasons.append("trailers-only shape changed")
    if trailers != expected["trailers"]:
        reasons.append("terminal trailer multimap changed")
    status_values = trailers.get("grpc-status", [])
    if len(status_values) != 1 or not STATUS_RE.fullmatch(status_values[0]):
        reasons.append("exactly one numeric grpc-status is required in terminal metadata")
    return hop, "LOSS" if reasons else "PRESERVE", reasons


def analyze(document):
    document = obj(document, "root")
    if document.get("version") != 1:
        raise InputError("version must be 1")
    cases = document.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_CASES:
        raise InputError(f"cases must contain 1..{MAX_CASES} items")
    result_cases = []
    overall = "PASS"
    for case_index, case in enumerate(cases):
        case = obj(case, f"cases[{case_index}]")
        case_id = text(case.get("id"), f"cases[{case_index}].id")
        expected = expected_shape(case, case_index)
        observations = case.get("observations")
        if not isinstance(observations, list) or not 1 <= len(observations) <= MAX_HOPS:
            raise InputError(f"cases[{case_index}].observations must contain 1..{MAX_HOPS} items")
        seen = set()
        outputs = []
        first = None
        for hop_index, observation in enumerate(observations):
            hop, classification, reasons = analyze_observation(observation, expected, case_index, hop_index)
            if hop in seen:
                raise InputError(f"cases[{case_index}] repeats hop {hop}")
            seen.add(hop)
            outputs.append({"hop": hop, "classification": classification, "reasons": reasons})
            if first is None and classification != "PRESERVE":
                first = hop
        case_status = "PASS" if first is None else "FAIL"
        if case_status == "FAIL":
            overall = "FAIL"
        result_cases.append({"id": case_id, "status": case_status, "first_divergent_hop": first, "observations": outputs})
    return {"version": 1, "status": overall, "cases": result_cases}


def write_result(result, output):
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if output is None:
        sys.stdout.write(payload)
        return
    target = Path(output)
    temporary = target.with_name(target.name + f".tmp.{os.getpid()}")
    try:
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, target)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise InputError(f"cannot write output: {exc}") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        result = analyze(load_json(args.trace))
        write_result(result, args.output)
    except (InputError, BrokenPipeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
