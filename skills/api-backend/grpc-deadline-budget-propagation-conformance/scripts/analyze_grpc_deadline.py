#!/usr/bin/env python3
"""Offline gRPC deadline-budget trace analyzer."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

UNITS = {"H": 3_600_000_000_000, "M": 60_000_000_000, "S": 1_000_000_000,
         "m": 1_000_000, "u": 1_000, "n": 1}
TIMEOUT_RE = re.compile(r"([1-9][0-9]{0,7})([HMSmun])\Z", re.ASCII)
RPC_TYPES = {"unary", "client_streaming", "server_streaming", "bidi_streaming"}

class InputError(ValueError):
    pass

def silence_broken_stdout() -> None:
    """Prevent interpreter-shutdown flush from replacing exit 2 with 120."""
    try:
        fd = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(fd, sys.stdout.fileno())
        finally:
            os.close(fd)
    except OSError:
        pass

def timeout_ns(value: object) -> int:
    if not isinstance(value, str):
        raise InputError("timeout must be a string")
    match = TIMEOUT_RE.fullmatch(value)
    if not match:
        raise InputError("timeout must be 1-8 ASCII digits, positive, plus H/M/S/m/u/n")
    return int(match.group(1)) * UNITS[match.group(2)]

def integer(value: object, field: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise InputError(f"{field} must be an integer >= {minimum}")
    return value

def analyze(doc: object) -> dict:
    if not isinstance(doc, dict):
        raise InputError("top level must be an object")
    if doc.get("kind") != "grpc_deadline_trace":
        return {"schema_version": 1, "classification": "not_applicable", "findings": [],
                "observations": ["no grpc_deadline_trace evidence"]}
    if doc.get("schema_version") != 1:
        raise InputError("schema_version must equal 1")
    rpc_type = doc.get("rpc_type")
    if rpc_type not in RPC_TYPES:
        raise InputError("rpc_type is invalid")
    findings, observations, transitions = [], [], []
    raw_initial = doc.get("initial_timeout")
    missing_policy = doc.get("missing_deadline_policy")
    if missing_policy not in {"allow", "block"}:
        raise InputError("missing_deadline_policy must be allow or block")
    if raw_initial is None:
        if missing_policy == "block":
            findings.append({"code": "missing_deadline_blocked"})
        return {"schema_version": 1, "classification": "blocked" if findings else "ready",
                "rpc_type": rpc_type, "findings": findings,
                "observations": ["deadline omitted under explicit policy"], "transitions": []}
    try:
        initial = timeout_ns(raw_initial)
    except InputError as exc:
        return {"schema_version": 1, "classification": "blocked", "rpc_type": rpc_type,
                "findings": [{"code": "invalid_timeout", "field": "initial_timeout", "detail": str(exc)}],
                "observations": [], "transitions": []}
    effective = initial
    if "server_max_ns" in doc:
        maximum = integer(doc["server_max_ns"], "server_max_ns", 1)
        if effective > maximum:
            effective = maximum
            observations.append({"code": "server_max_clamp", "from_ns": initial, "to_ns": effective})
    hops = doc.get("hops", [])
    if not isinstance(hops, list):
        raise InputError("hops must be an array")
    received = effective
    for index, hop in enumerate(hops):
        if not isinstance(hop, dict):
            raise InputError(f"hops[{index}] must be an object")
        name = hop.get("name")
        if not isinstance(name, str) or not name:
            raise InputError(f"hops[{index}].name must be a non-empty string")
        elapsed = integer(hop.get("elapsed_ns"), f"hops[{index}].elapsed_ns")
        available = max(received - elapsed, 0)
        raw_sent = hop.get("forwarded_timeout")
        try:
            sent = timeout_ns(raw_sent)
        except InputError as exc:
            findings.append({"code": "invalid_timeout", "hop": name, "detail": str(exc)})
            transitions.append({"hop": name, "received_ns": received, "elapsed_ns": elapsed,
                                "available_ns": available, "sent_ns": None})
            break
        transition = {"hop": name, "received_ns": received, "elapsed_ns": elapsed,
                      "available_ns": available, "sent_ns": sent}
        transitions.append(transition)
        if available == 0:
            findings.append({"code": "expired_before_dispatch", "hop": name})
        if sent > available:
            findings.append({"code": "deadline_budget_expanded", "hop": name,
                             "available_ns": available, "sent_ns": sent})
        received = sent
    server = doc.get("server")
    if server is not None:
        if not isinstance(server, dict):
            raise InputError("server must be an object")
        elapsed_total = integer(server.get("elapsed_since_initial_ns"), "server.elapsed_since_initial_ns")
        active = server.get("work_active")
        cancelled = server.get("cancellation_observed")
        if not isinstance(active, bool) or not isinstance(cancelled, bool):
            raise InputError("server work_active and cancellation_observed must be booleans")
        if elapsed_total >= effective and active and not cancelled:
            findings.append({"code": "work_continued_after_expiry", "elapsed_ns": elapsed_total,
                             "effective_initial_ns": effective})
        if server.get("status") in {"DEADLINE_EXCEEDED", "CANCELLED"}:
            observations.append({"code": "terminal_status_observed", "status": server["status"]})
    return {"schema_version": 1, "classification": "blocked" if findings else "ready",
            "rpc_type": rpc_type, "initial_timeout_ns": initial, "effective_initial_ns": effective,
            "findings": findings, "observations": observations, "transitions": transitions}

def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: analyze_grpc_deadline.py TRACE.json", file=sys.stderr)
        return 2
    try:
        raw = Path(argv[1]).read_text(encoding="utf-8")
        doc = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(InputError(f"non-finite JSON value: {value}")))
        result = analyze(doc)
    except (OSError, UnicodeError, json.JSONDecodeError, InputError) as exc:
        try:
            print(json.dumps({"schema_version": 1, "classification": "input_error", "error": str(exc)}, sort_keys=True))
            sys.stdout.flush()
        except OSError:
            silence_broken_stdout()
            return 2
        return 2
    try:
        print(json.dumps(result, indent=2, sort_keys=True))
        sys.stdout.flush()
    except OSError:
        silence_broken_stdout()
        return 2
    return 1 if result["classification"] == "blocked" else 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
